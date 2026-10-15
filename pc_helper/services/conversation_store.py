"""Local persistence for conversations (chat history).

Each conversation is one JSON file under the configured store directory, and
its attached screenshots live under ``<uploads_dir>/<conversation_id>/``. This
gives a browsable, resumable chat history that survives app restarts (brief
§8.2). Everything stays on the local machine.
"""
from __future__ import annotations

import json
import re
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from ..core.logging_config import get_logger
from ..models.conversation_models import ConversationState

logger = get_logger(__name__)

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass
class ConversationSummary:
    conversation_id: str
    title: str
    updated_at: float
    message_count: int
    status: str


def _safe_id(conversation_id: str) -> str:
    # Guard against path traversal via a crafted conversation_id.
    return "".join(c for c in conversation_id if c.isalnum() or c in "-_")


class ConversationStore:
    def __init__(self, store_dir: Path, uploads_dir: Optional[Path] = None, project_root: Optional[Path] = None):
        self.store_dir = Path(store_dir)
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir = Path(uploads_dir) if uploads_dir else self.store_dir.parent / "uploads"
        self.project_root = Path(project_root) if project_root else self.store_dir.parent.parent
        self._cache: Dict[str, ConversationState] = {}

    def _path(self, conversation_id: str) -> Path:
        return self.store_dir / f"{_safe_id(conversation_id)}.json"

    # --- create / read / write ---
    def create(self) -> ConversationState:
        state = ConversationState()
        self._cache[state.conversation_id] = state
        self.save(state)
        return state

    def get(self, conversation_id: str) -> Optional[ConversationState]:
        if conversation_id in self._cache:
            return self._cache[conversation_id]
        path = self._path(conversation_id)
        if not path.exists():
            return None
        try:
            state = ConversationState.model_validate_json(path.read_text(encoding="utf-8"))
            self._cache[conversation_id] = state
            return state
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load conversation %s: %s", conversation_id, exc)
            return None

    def save(self, state: ConversationState) -> None:
        self._cache[state.conversation_id] = state
        try:
            self._path(state.conversation_id).write_text(state.model_dump_json(indent=2), encoding="utf-8")
        except Exception as exc:  # noqa: BLE001 - persistence failure shouldn't crash a chat
            logger.warning("Failed to persist conversation %s: %s", state.conversation_id, exc)

    # --- history ---
    def list_conversations(self, limit: int = 50) -> List[ConversationSummary]:
        """Saved conversations with at least one message, newest first."""
        summaries: List[ConversationSummary] = []
        for path in self.store_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001 - skip corrupt/partial files
                continue
            messages = data.get("messages") or []
            if not messages:
                continue
            first_user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
            summaries.append(
                ConversationSummary(
                    conversation_id=data.get("conversation_id", path.stem),
                    title=data.get("title") or (first_user[:60] or "Untitled chat"),
                    updated_at=float(data.get("updated_at") or path.stat().st_mtime),
                    message_count=len(messages),
                    status=data.get("status") or "diagnosing",
                )
            )
        summaries.sort(key=lambda s: s.updated_at, reverse=True)
        return summaries[:limit]

    def delete(self, conversation_id: str) -> bool:
        self._cache.pop(conversation_id, None)
        path = self._path(conversation_id)
        existed = path.exists()
        if existed:
            path.unlink()
        uploads = self.uploads_dir / _safe_id(conversation_id)
        if uploads.exists():
            shutil.rmtree(uploads, ignore_errors=True)
        return existed

    # --- attachments ---
    def save_image(self, conversation_id: str, data: bytes, filename: str) -> str:
        """Store an uploaded screenshot; return its path relative to the project root."""
        folder = self.uploads_dir / _safe_id(conversation_id)
        folder.mkdir(parents=True, exist_ok=True)
        name = _SAFE_NAME.sub("_", Path(filename or "screenshot.png").name) or "screenshot.png"
        target = folder / f"{int(time.time() * 1000)}_{name}"
        target.write_bytes(data)
        try:
            return target.relative_to(self.project_root).as_posix()
        except ValueError:  # uploads dir outside the project: keep the absolute path
            return target.as_posix()

    def resolve_image(self, image_path: Optional[str]) -> Optional[Path]:
        if not image_path:
            return None
        p = Path(image_path)
        p = p if p.is_absolute() else self.project_root / p
        return p if p.exists() else None
