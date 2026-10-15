"""Text embeddings with a pluggable backend.

Two backends are provided:

* ``SentenceTransformerEmbedder`` — real semantic embeddings (requires the
  optional ``sentence-transformers`` dependency). Best retrieval quality.
* ``HashingEmbedder`` — a lightweight, dependency-free fallback (numpy only).
  It maps word unigrams and bigrams into a fixed-dimensional vector using a
  *stable* hash (hashlib, not Python's salted ``hash()``), so the same text
  always produces the same vector across runs — essential for a persisted
  index. Quality is lexical rather than semantic, but it lets the whole
  application run and be tested with no heavy downloads.

``backend: "auto"`` uses sentence-transformers if importable, else hashing.

Every embedder exposes ``name`` and ``dim`` so the vector index can record
which embedder built it and refuse to reuse an incompatible index.
"""
from __future__ import annotations

import hashlib
import re
from typing import List

import numpy as np

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class BaseEmbedder:
    name: str = "base"
    dim: int = 0

    def encode(self, texts: List[str]) -> np.ndarray:  # pragma: no cover - interface
        raise NotImplementedError

    def encode_one(self, text: str) -> np.ndarray:
        return self.encode([text])[0]


class HashingEmbedder(BaseEmbedder):
    """Deterministic bag-of-ngrams hashing embedder (no external deps)."""

    def __init__(self, dim: int = 512):
        self.dim = dim
        self.name = f"hashing-{dim}"

    @staticmethod
    def _tokens(text: str) -> List[str]:
        text = text.lower()
        words = _TOKEN_RE.findall(text)
        bigrams = [f"{a}_{b}" for a, b in zip(words, words[1:])]
        # Collapsed forms strip internal punctuation so hyphenated/compound
        # terms match ("wi-fi" -> "wifi", "c++" -> "c"). This noticeably
        # improves the lexical fallback's recall on real documents.
        word_set = set(words)
        collapsed = [re.sub(r"[^a-z0-9]", "", t) for t in text.split()]
        collapsed = [t for t in collapsed if t and t not in word_set]
        return words + bigrams + collapsed

    def _hash(self, token: str) -> int:
        digest = hashlib.md5(token.encode("utf-8")).digest()
        return int.from_bytes(digest[:4], "little")

    def encode(self, texts: List[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for i, text in enumerate(texts):
            for tok in self._tokens(text):
                h = self._hash(tok)
                idx = h % self.dim
                sign = 1.0 if (h // self.dim) % 2 == 0 else -1.0
                out[i, idx] += sign
            norm = np.linalg.norm(out[i])
            if norm > 0:
                out[i] /= norm
        return out


class SentenceTransformerEmbedder(BaseEmbedder):
    """Semantic embeddings via sentence-transformers (optional dependency)."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer  # lazy import

        self._model = SentenceTransformer(model_name)
        self.dim = int(self._model.get_sentence_embedding_dimension())
        self.name = f"st-{model_name}"

    def encode(self, texts: List[str]) -> np.ndarray:
        vecs = self._model.encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        return np.asarray(vecs, dtype=np.float32)


def _sentence_transformers_available() -> bool:
    import importlib.util

    return importlib.util.find_spec("sentence_transformers") is not None


def build_embedder(backend: str = "auto", model: str = "all-MiniLM-L6-v2") -> BaseEmbedder:
    """Construct the embedder named by config, with graceful fallback."""
    backend = (backend or "auto").lower()
    if backend == "hashing":
        return HashingEmbedder()
    if backend in {"sentence-transformers", "sentence_transformers", "st"}:
        return SentenceTransformerEmbedder(model)
    # auto
    if _sentence_transformers_available():
        try:
            return SentenceTransformerEmbedder(model)
        except Exception as exc:  # noqa: BLE001 - fall back if the model can't load
            from ..core.logging_config import get_logger

            get_logger(__name__).warning(
                "sentence-transformers is installed but model '%s' failed to load "
                "(%s: %s); falling back to the lightweight hashing embedder.",
                model, exc.__class__.__name__, exc,
            )
            return HashingEmbedder()
    return HashingEmbedder()
