"""Markdown ingestion: read -> chunk -> embed -> build the vector index.

The chunker is heading-aware: it tracks the current Markdown heading so each
chunk keeps the most relevant heading as metadata (used for citations). Long
sections are split into overlapping windows of roughly ``chunk_size``
characters so no single chunk is too large for retrieval.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from ..core.config import Settings
from ..core.logging_config import get_logger
from .embeddings import BaseEmbedder
from .vector_store import ChunkRecord, Manifest, VectorIndex, utc_now_iso

logger = get_logger(__name__)

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


@dataclass
class IngestionStats:
    documents: int = 0
    chunks: int = 0
    skipped: int = 0
    errors: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------- #
# File scanning
# --------------------------------------------------------------------------- #
def scan_markdown_files(directory: Path, extensions: List[str], recursive: bool) -> List[Path]:
    if not directory.exists() or not directory.is_dir():
        return []
    exts = {e.lower() for e in extensions}
    globber = directory.rglob("*") if recursive else directory.glob("*")
    files = [p for p in globber if p.is_file() and p.suffix.lower() in exts]
    return sorted(files)


# --------------------------------------------------------------------------- #
# Chunking
# --------------------------------------------------------------------------- #
def chunk_markdown(text: str, rel_path: str, chunk_size: int, chunk_overlap: int) -> List[ChunkRecord]:
    """Split a document into heading-aware, overlapping chunks."""
    lines = text.splitlines()

    # Group lines into sections keyed by the nearest heading.
    sections: List[tuple[Optional[str], str]] = []
    current_heading: Optional[str] = None
    buffer: List[str] = []

    def flush():
        if buffer:
            body = "\n".join(buffer).strip()
            if body:
                sections.append((current_heading, body))

    for line in lines:
        m = _HEADING_RE.match(line)
        if m:
            flush()
            buffer = []
            current_heading = m.group(2).strip()
        else:
            buffer.append(line)
    flush()

    # If the doc had no headings at all, treat the whole thing as one section.
    if not sections:
        body = text.strip()
        if body:
            sections = [(None, body)]

    records: List[ChunkRecord] = []
    idx = 0
    for heading, body in sections:
        for piece in _split_with_overlap(body, chunk_size, chunk_overlap):
            records.append(
                ChunkRecord(
                    chunk_id=f"{rel_path}::{idx}",
                    file=rel_path,
                    heading=heading,
                    text=piece,
                    chunk_index=idx,
                )
            )
            idx += 1
    return records


def _split_with_overlap(text: str, chunk_size: int, overlap: int) -> List[str]:
    text = text.strip()
    if len(text) <= chunk_size:
        return [text] if text else []

    # Prefer to break on paragraph boundaries, then fall back to hard windows.
    paragraphs = re.split(r"\n\s*\n", text)
    chunks: List[str] = []
    current = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(para) > chunk_size:
            # Paragraph itself too big: hard-window it.
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_hard_windows(para, chunk_size, overlap))
            continue
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}" if current else para
        else:
            chunks.append(current)
            # start next chunk with a tail overlap of the previous one
            tail = current[-overlap:] if overlap > 0 else ""
            current = f"{tail}\n\n{para}" if tail else para
    if current:
        chunks.append(current)
    return [c.strip() for c in chunks if c.strip()]


def _hard_windows(text: str, chunk_size: int, overlap: int) -> List[str]:
    step = max(chunk_size - overlap, 1)
    return [text[i : i + chunk_size] for i in range(0, len(text), step)]


# --------------------------------------------------------------------------- #
# Full ingestion
# --------------------------------------------------------------------------- #
def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def ingest(settings: Settings, embedder: BaseEmbedder) -> tuple[VectorIndex, IngestionStats]:
    """Build and persist the vector index from the configured knowledge base."""
    kb = settings.config.knowledge_base
    kb_dir = settings.kb_dir
    stats = IngestionStats()

    files = scan_markdown_files(kb_dir, kb.file_extensions, kb.recursive_scan)
    if not files:
        logger.warning("No markdown files found in %s", kb_dir)

    all_records: List[ChunkRecord] = []
    file_hashes: dict = {}

    for path in files:
        rel = path.relative_to(kb_dir).as_posix()
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            stats.skipped += 1
            stats.errors.append(f"{rel}: could not read ({exc})")
            continue
        if not text.strip():
            stats.skipped += 1
            stats.errors.append(f"{rel}: empty file")
            continue
        recs = chunk_markdown(text, rel, kb.chunking.chunk_size, kb.chunking.chunk_overlap)
        if not recs:
            stats.skipped += 1
            continue
        all_records.extend(recs)
        file_hashes[rel] = _file_hash(path)
        stats.documents += 1

    index = VectorIndex(settings.index_dir)

    if all_records:
        vectors = embedder.encode([r.text for r in all_records])
    else:
        import numpy as np

        vectors = np.zeros((0, embedder.dim or 1), dtype="float32")

    manifest = Manifest(
        embedder=embedder.name,
        dim=embedder.dim,
        source_directory=str(kb_dir),
        chunk_size=kb.chunking.chunk_size,
        chunk_overlap=kb.chunking.chunk_overlap,
        documents=stats.documents,
        chunks=len(all_records),
        built_at=utc_now_iso(),
        file_hashes=file_hashes,
    )
    index.build(all_records, vectors, manifest)
    index.save()

    stats.chunks = len(all_records)
    logger.info(
        "Ingestion complete: %d documents, %d chunks, %d skipped",
        stats.documents, stats.chunks, stats.skipped,
    )
    return index, stats
