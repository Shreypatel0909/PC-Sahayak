"""Unit tests for Markdown ingestion and chunking."""
from __future__ import annotations

from pathlib import Path

from pc_helper.services.ingestion_service import (
    chunk_markdown,
    scan_markdown_files,
)


def test_scan_finds_markdown_recursively(tmp_kb: Path):
    files = scan_markdown_files(tmp_kb, [".md", ".markdown"], recursive=True)
    names = {p.name for p in files}
    assert names == {"performance.md", "wifi.md"}


def test_scan_missing_directory_returns_empty(tmp_path: Path):
    assert scan_markdown_files(tmp_path / "does-not-exist", [".md"], recursive=True) == []


def test_chunk_preserves_heading_and_path():
    text = "# Title\n\n## Fixes\nStep one here.\n"
    records = chunk_markdown(text, "windows/doc.md", chunk_size=800, chunk_overlap=100)
    assert records, "expected at least one chunk"
    assert all(r.file == "windows/doc.md" for r in records)
    headings = {r.heading for r in records}
    assert "Fixes" in headings


def test_long_section_is_split_into_multiple_chunks():
    body = "\n\n".join(f"Paragraph number {i} with some filler text." for i in range(60))
    text = f"# Big\n\n## Section\n{body}\n"
    records = chunk_markdown(text, "big.md", chunk_size=300, chunk_overlap=50)
    assert len(records) > 1
    assert all(len(r.text) <= 300 + 50 for r in records)


def test_ingest_on_empty_dir_is_graceful(test_settings, tmp_path: Path):
    import os

    empty = tmp_path / "empty_kb"
    empty.mkdir()
    os.environ["PC_HELPER_KB_DIR"] = empty.as_posix()
    try:
        from pc_helper.core.config import load_settings
        from pc_helper.services.embeddings import build_embedder
        from pc_helper.services.ingestion_service import ingest

        settings = load_settings()
        index, stats = ingest(settings, build_embedder("hashing"))
        assert stats.documents == 0
        assert stats.chunks == 0
        assert index.chunks == 0
    finally:
        os.environ.pop("PC_HELPER_KB_DIR", None)
