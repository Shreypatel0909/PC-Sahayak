"""Rebuild the vector index from the configured Markdown knowledge base.

Run this after changing the knowledge-base directory or adding/editing documents:

    python -m scripts.reindex_knowledge_base
    python -m scripts.reindex_knowledge_base --kb-dir "D:\\PC_Helper\\knowledge_base"

Run from the project root (the pc-helper/ folder).
"""
from __future__ import annotations

import argparse
import os
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild the PC-Sahayak knowledge-base index.")
    parser.add_argument("--kb-dir", help="Override the knowledge-base directory for this run.")
    args = parser.parse_args()

    if args.kb_dir:
        os.environ["PC_HELPER_KB_DIR"] = args.kb_dir

    # Import after setting env so the override is picked up.
    from pc_helper.core.config import load_settings
    from pc_helper.services.embeddings import build_embedder
    from pc_helper.services.ingestion_service import ingest

    settings = load_settings()
    print(f"Knowledge base: {settings.kb_dir}")
    print(f"Index output:   {settings.index_dir}")

    embedder = build_embedder(
        settings.config.embeddings.backend, settings.config.embeddings.model
    )
    print(f"Embedder:       {embedder.name} (dim={embedder.dim})")

    _, stats = ingest(settings, embedder)
    print(
        f"\nDone: {stats.documents} documents, {stats.chunks} chunks, "
        f"{stats.skipped} skipped."
    )
    if stats.errors:
        print("\nWarnings/errors:")
        for e in stats.errors:
            print(f"  - {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
