"""Retrieval: turn a user message + conversation context into a query, then
fetch the most relevant knowledge-base chunks.

Per the brief, an ambiguous follow-up ("No, none of them can") must be rewritten
into a useful standalone query using what we already know about the issue. We do
this cheaply by prepending the structured problem context to the message.
"""
from __future__ import annotations

from typing import List, Optional

from ..models.conversation_models import ConversationState
from .embeddings import BaseEmbedder
from .vector_store import RetrievedChunk, VectorIndex


class Retriever:
    def __init__(self, index: VectorIndex, embedder: BaseEmbedder):
        self.index = index
        self.embedder = embedder

    def build_query(self, message: str, state: Optional[ConversationState]) -> str:
        if state is None:
            return message
        parts: List[str] = []
        if state.problem_summary:
            parts.append(state.problem_summary)
        if state.issue_category:
            parts.append(state.issue_category)
        if state.operating_system:
            parts.append(state.operating_system)
        if state.device:
            parts.append(state.device)
        # A couple of the most recent known facts help disambiguate follow-ups.
        parts.extend(state.known_facts[-3:])
        parts.append(message)
        return " | ".join(p for p in parts if p)

    def retrieve(
        self,
        message: str,
        state: Optional[ConversationState],
        top_k: int,
        threshold: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        query = self.build_query(message, state)
        vec = self.embedder.encode_one(query)
        return self.index.search(vec, top_k=top_k, threshold=threshold)
