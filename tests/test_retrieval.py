"""Unit tests for embeddings, the vector index, and retrieval."""
from __future__ import annotations

from pc_helper.models.conversation_models import ConversationState
from pc_helper.services.embeddings import HashingEmbedder, build_embedder
from pc_helper.services.ingestion_service import ingest
from pc_helper.services.retrieval_service import Retriever


def test_hashing_embedder_is_deterministic():
    e = HashingEmbedder()
    a = e.encode_one("wi-fi is not working")
    b = e.encode_one("wi-fi is not working")
    assert (a == b).all()
    assert abs(float((a * a).sum()) - 1.0) < 1e-5  # normalized


def test_retrieval_finds_relevant_document(test_settings):
    embedder = build_embedder("hashing")
    index, _ = ingest(test_settings, embedder)
    retriever = Retriever(index, embedder)

    results = retriever.retrieve("my wifi keeps dropping", state=None, top_k=2)
    assert results
    assert results[0].file == "networking/wifi.md"


def test_query_builder_incorporates_state_context(test_settings):
    embedder = build_embedder("hashing")
    index, _ = ingest(test_settings, embedder)
    retriever = Retriever(index, embedder)

    state = ConversationState(problem_summary="Wi-Fi not working", issue_category="network")
    state.known_facts.append("No devices can connect")
    query = retriever.build_query("no, none of them can", state)
    assert "Wi-Fi not working" in query
    assert "No devices can connect" in query


def test_index_persists_and_reloads(test_settings):
    from pc_helper.services.vector_store import VectorIndex

    embedder = build_embedder("hashing")
    index, _ = ingest(test_settings, embedder)
    assert index.chunks > 0

    reopened = VectorIndex(test_settings.index_dir)
    assert reopened.load() is True
    assert reopened.chunks == index.chunks
    assert reopened.is_compatible(embedder.name, str(test_settings.kb_dir))
