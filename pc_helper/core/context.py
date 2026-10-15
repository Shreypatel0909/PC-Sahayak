"""Application context: builds and holds the shared services.

Created once per app run (cached by Streamlit via @st.cache_resource). It loads
the vector index from disk if it is present and compatible with the current
embedder and knowledge-base directory; otherwise it ingests the knowledge base
to build one.
"""
from __future__ import annotations

import threading
from typing import Optional

from ..services.conversation_store import ConversationStore
from ..services.embeddings import BaseEmbedder, build_embedder
from ..services.ingestion_service import IngestionStats, ingest
from ..services.llm_service import GroqLLM, build_llm
from ..services.retrieval_service import Retriever
from ..services.troubleshooting_service import TroubleshootingEngine
from ..services.vector_store import VectorIndex
from .config import Settings, get_settings
from .logging_config import configure_logging, get_logger

logger = get_logger(__name__)


class AppContext:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        configure_logging(self.settings.config.logging.level)

        self.embedder: BaseEmbedder = build_embedder(
            self.settings.config.embeddings.backend,
            self.settings.config.embeddings.model,
        )
        self.index: VectorIndex = VectorIndex(self.settings.index_dir)
        self.last_ingestion: Optional[IngestionStats] = None
        self._reindex_lock = threading.Lock()
        self._reindexing = False

        self._load_or_build_index()

        self.retriever = Retriever(self.index, self.embedder)
        self.llm: GroqLLM = build_llm(self.settings.llm, self.settings.config.llm)
        self.conversation_store = ConversationStore(
            self.settings.conversations_dir,
            uploads_dir=self.settings.uploads_dir,
            project_root=self.settings.project_root,
        )
        self.engine = TroubleshootingEngine(self.settings, self.retriever, self.llm)

    def _load_or_build_index(self) -> None:
        loaded = self.index.load()
        source = str(self.settings.kb_dir)
        if loaded and self.index.is_compatible(self.embedder.name, source):
            logger.info(
                "Loaded existing index: %d docs, %d chunks (embedder=%s)",
                self.index.documents, self.index.chunks, self.embedder.name,
            )
            return
        if loaded:
            logger.warning(
                "Existing index is incompatible (different embedder or knowledge base) — rebuilding."
            )
        logger.info("Building knowledge-base index (embedder=%s)...", self.embedder.name)
        self.index, self.last_ingestion = ingest(self.settings, self.embedder)

    @property
    def is_reindexing(self) -> bool:
        return self._reindexing

    def reindex(self) -> IngestionStats:
        """Rebuild the index. Guarded so concurrent calls don't collide."""
        if not self._reindex_lock.acquire(blocking=False):
            raise RuntimeError("A re-indexing operation is already in progress.")
        try:
            self._reindexing = True
            logger.info("Re-indexing knowledge base...")
            self.index, self.last_ingestion = ingest(self.settings, self.embedder)
            # Point the retriever at the freshly built index.
            self.retriever.index = self.index
            return self.last_ingestion
        finally:
            self._reindexing = False
            self._reindex_lock.release()
