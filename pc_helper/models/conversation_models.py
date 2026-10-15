"""Structured conversation state.

The brief stresses that model-generated text is NOT a reliable substitute for
structured state, so each conversation carries an explicit, validated state
object alongside the raw message transcript.

Each message also carries its display metadata (attached screenshot, cited
sources, suggested replies) so a saved conversation can be resumed and shown
exactly as it looked.
"""
from __future__ import annotations

import time
import uuid
from typing import List, Optional

from pydantic import BaseModel, Field

UNKNOWN = "Don't know"


def _now() -> float:
    return time.time()


def new_id() -> str:
    return uuid.uuid4().hex[:12]


class SourceRef(BaseModel):
    file: str
    heading: Optional[str] = None


class Message(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    timestamp: float = Field(default_factory=_now)
    kind: str = "normal"  # "normal" | "error" (errors are shown but never sent to the LLM)
    image_path: Optional[str] = None  # relative to the project root
    sources: List[SourceRef] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)


class SystemSpecs(BaseModel):
    """Hardware/OS profile collected by the intake form before chatting."""

    device_type: Optional[str] = None
    os: Optional[str] = None
    os_version: Optional[str] = None
    ram_size: Optional[str] = None
    ram_type: Optional[str] = None
    storage_size: Optional[str] = None
    storage_type: Optional[str] = None

    @staticmethod
    def _known(value: Optional[str]) -> bool:
        return bool(value and value.strip() and value != UNKNOWN)

    def os_label(self) -> Optional[str]:
        parts = [p for p in (self.os, self.os_version) if self._known(p)]
        return " ".join(parts) or None

    def summary(self) -> str:
        """Compact one-line profile, skipping unknown fields."""
        ram = " ".join(p for p in (self.ram_size, self.ram_type) if self._known(p))
        storage = " ".join(p for p in (self.storage_size, self.storage_type) if self._known(p))
        parts = [
            self.device_type if self._known(self.device_type) else None,
            self.os_label(),
            f"{ram} RAM" if ram else None,
            f"{storage} storage" if storage else None,
        ]
        return " · ".join(p for p in parts if p) or "No system details provided"


class ConversationState(BaseModel):
    conversation_id: str = Field(default_factory=new_id)
    title: Optional[str] = None

    # Collected up front by the intake form (never re-asked in chat).
    system_specs: Optional[SystemSpecs] = None
    intake_complete: bool = False

    # Diagnostic understanding (updated as the conversation progresses).
    issue_category: Optional[str] = None
    problem_summary: Optional[str] = None
    device: Optional[str] = None
    operating_system: Optional[str] = None

    known_facts: List[str] = Field(default_factory=list)
    questions_asked: List[str] = Field(default_factory=list)
    completed_steps: List[str] = Field(default_factory=list)
    current_step: Optional[str] = None
    observations: List[str] = Field(default_factory=list)
    retrieved_sources: List[SourceRef] = Field(default_factory=list)

    status: str = "diagnosing"  # diagnosing | needs_info | resolved | general
    resolution_confirmed: bool = False

    # Raw transcript.
    messages: List[Message] = Field(default_factory=list)

    created_at: float = Field(default_factory=_now)
    updated_at: float = Field(default_factory=_now)

    def add_message(self, role: str, content: str, **extra) -> Message:
        msg = Message(role=role, content=content, **extra)
        self.messages.append(msg)
        self.updated_at = _now()
        return msg

    def recent_messages(self, limit: int) -> List[Message]:
        return self.messages[-limit:] if limit > 0 else self.messages

    def apply_specs(self, specs: SystemSpecs) -> None:
        """Store the intake profile and seed the fields retrieval already uses."""
        self.system_specs = specs
        self.operating_system = specs.os_label()
        if SystemSpecs._known(specs.device_type):
            self.device = specs.device_type
        self.intake_complete = True
        self.updated_at = _now()
