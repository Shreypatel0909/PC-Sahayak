"""Persistent vector index.

Why a numpy-backed store rather than FAISS/Chroma?
  For a small, local, single-node university project this is the smallest
  reliable option: no native build steps (FAISS wheels are awkward on
  Windows), no extra services, and the cosine search is completely
  transparent and easy to explain academically. The interface is small, so
  swapping in FAISS/Chroma later would be localised to this file.

On disk (in the configured index directory):
  vectors.npy   float32 matrix, shape (n_chunks, dim), L2-normalized
  records.json  per-chunk metadata (file, heading, text, chunk_index)
  manifest.json indexing metadata — embedder name, dim, source directory,
                chunking config, build time, and a per-file content hash.

The manifest lets the app detect when an index was built from a different
knowledge base or a different embedder and refuse to reuse it silently.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

import numpy as np

from pydantic import BaseModel


class ChunkRecord(BaseModel):
    chunk_id: str
    file: str          # relative path within the knowledge base
    heading: Optional[str] = None
    text: str
    chunk_index: int


class RetrievedChunk(BaseModel):
    file: str
    heading: Optional[str]
    text: str
    score: float


class Manifest(BaseModel):
    embedder: str
    dim: int
    source_directory: str
    chunk_size: int
    chunk_overlap: int
    documents: int
    chunks: int
    built_at: str
    file_hashes: dict = {}


class VectorIndex:
    def __init__(self, index_dir: Path):
        self.index_dir = Path(index_dir)
        self.vectors: Optional[np.ndarray] = None
        self.records: List[ChunkRecord] = []
        self.manifest: Optional[Manifest] = None

    # --- paths ---
    @property
    def _vectors_path(self) -> Path:
        return self.index_dir / "vectors.npy"

    @property
    def _records_path(self) -> Path:
        return self.index_dir / "records.json"

    @property
    def _manifest_path(self) -> Path:
        return self.index_dir / "manifest.json"

    # --- state ---
    @property
    def exists(self) -> bool:
        return self._manifest_path.exists() and self._vectors_path.exists()

    @property
    def documents(self) -> int:
        return self.manifest.documents if self.manifest else 0

    @property
    def chunks(self) -> int:
        return len(self.records)

    # --- persistence ---
    def build(self, records: List[ChunkRecord], vectors: np.ndarray, manifest: Manifest) -> None:
        self.records = records
        self.vectors = vectors.astype(np.float32)
        self.manifest = manifest

    def save(self) -> None:
        self.index_dir.mkdir(parents=True, exist_ok=True)
        np.save(self._vectors_path, self.vectors if self.vectors is not None else np.zeros((0, 0), dtype=np.float32))
        self._records_path.write_text(
            json.dumps([r.model_dump() for r in self.records], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        self._manifest_path.write_text(
            self.manifest.model_dump_json(indent=2) if self.manifest else "{}",
            encoding="utf-8",
        )

    def load(self) -> bool:
        if not self.exists:
            return False
        try:
            self.vectors = np.load(self._vectors_path)
            self.records = [ChunkRecord(**r) for r in json.loads(self._records_path.read_text(encoding="utf-8"))]
            self.manifest = Manifest(**json.loads(self._manifest_path.read_text(encoding="utf-8")))
            return True
        except Exception:  # noqa: BLE001 - treat a corrupt index as "not loaded"
            self.vectors = None
            self.records = []
            self.manifest = None
            return False

    # --- compatibility ---
    def is_compatible(self, embedder_name: str, source_directory: str) -> bool:
        if not self.manifest:
            return False
        return (
            self.manifest.embedder == embedder_name
            and self.manifest.source_directory == source_directory
            and self.vectors is not None
            and self.vectors.shape[0] == len(self.records)
        )

    # --- search ---
    def search(self, query_vec: np.ndarray, top_k: int, threshold: Optional[float] = None) -> List[RetrievedChunk]:
        if self.vectors is None or len(self.records) == 0:
            return []
        q = np.asarray(query_vec, dtype=np.float32)
        norm = np.linalg.norm(q)
        if norm > 0:
            q = q / norm
        scores = self.vectors @ q  # cosine (both sides normalized)
        order = np.argsort(scores)[::-1]
        results: List[RetrievedChunk] = []
        for idx in order[: max(top_k, 0)]:
            score = float(scores[idx])
            if threshold is not None and score < threshold:
                continue
            rec = self.records[idx]
            results.append(
                RetrievedChunk(file=rec.file, heading=rec.heading, text=rec.text, score=score)
            )
        return results


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
