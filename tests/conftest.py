"""Shared pytest fixtures.

Tests are hermetic: a temporary knowledge base, index and conversation store are
created per test, the lightweight 'hashing' embedder is forced (no heavy
downloads), and the LLM is replaced by a scripted fake so no API credits are used.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import yaml


class FakeLLM:
    """Scripted, deterministic LLM (no network). Records every prompt it receives."""

    is_configured = True

    def __init__(self):
        self.calls: list[list[dict]] = []

    def complete(self, messages: list[dict], use_vision: bool = False, json_mode: bool = False) -> str:
        self.calls.append(messages)
        user_msgs = [m for m in messages if m["role"] == "user"]
        last = ""
        if user_msgs:
            c = user_msgs[-1]["content"]
            last = c.lower() if isinstance(c, str) else str(c).lower()
        has_context = any(
            m["role"] == "system" and m["content"].startswith("CONTEXT (")
            for m in messages
        )

        if use_vision:
            return "I can see a Windows error dialog. **Next step**\n1. Note the exact error code."

        resolving = any(
            m["role"] == "system" and "confirmed the problem is SOLVED" in m["content"] for m in messages
        )
        if resolving or "that worked" in last:
            return json.dumps({
                "reply": "**Fixed**\nClosing the busy app fixed it.\n\n**What we did**\n"
                         "1. Checked CPU usage in Task Manager: one app was at 95%.",
                "follow_up_question": None,
                "suggested_answers": [],
                "status": "resolved",
                "used_sources": [],
                "state_updates": {},
            })

        if "capital of france" in last:
            return json.dumps({
                "reply": "I can only help with PC problems. Tell me what's wrong with your computer.",
                "follow_up_question": None,
                "suggested_answers": [],
                "status": "off_topic",
                "used_sources": [],
                "state_updates": {"issue_category": "other", "problem_summary": "Geography question"},
            })

        if "delete all" in last and "system file" in last:
            return json.dumps({
                "reply": "I can't help delete system files — that would break Windows. "
                         "Let's find the real cause safely instead.",
                "follow_up_question": "What problem are you trying to fix?",
                "suggested_answers": ["It's slow", "It won't boot"],
                "status": "general",
                "used_sources": [],
                "state_updates": {},
            })

        return json.dumps({
            "reply": "**Next step**\n1. Open Task Manager with `Ctrl+Shift+Esc` and check CPU usage.",
            "follow_up_question": "What is the CPU usage percentage?",
            "suggested_answers": ["Under 50%", "Over 90%"],
            "status": "diagnosing",
            "used_sources": [0] if has_context else [],
            "state_updates": {
                "issue_category": "performance",
                "problem_summary": "PC is running slowly",
                "new_known_facts": ["User reports the PC is slow"],
                "current_step": "Check CPU usage in Task Manager",
            },
        })


class FailingLLM:
    """Simulates the provider being down."""

    is_configured = True

    def complete(self, messages, use_vision=False, json_mode=False):
        from pc_helper.services.llm_service import LLMUnavailableError

        raise LLMUnavailableError("The AI service is currently unavailable. Please try again.")


@pytest.fixture()
def tmp_kb(tmp_path: Path) -> Path:
    kb = tmp_path / "kb"
    (kb / "windows").mkdir(parents=True)
    (kb / "networking").mkdir(parents=True)
    (kb / "windows" / "performance.md").write_text(
        "# Windows Performance\n\n## Overview\nThis covers slow PC performance.\n\n"
        "## Step-by-step fixes\n1. Open Task Manager to inspect CPU and memory usage.\n"
        "2. Disable unnecessary startup apps.\n",
        encoding="utf-8",
    )
    (kb / "networking" / "wifi.md").write_text(
        "# Wi-Fi Troubleshooting\n\n## Overview\nFixing wireless network connection problems and dropped Wi-Fi.\n\n"
        "## Step-by-step fixes\n1. Restart your router.\n2. Run `ipconfig /flushdns`.\n",
        encoding="utf-8",
    )
    return kb


@pytest.fixture()
def test_settings(tmp_path: Path, tmp_kb: Path):
    index_dir = tmp_path / "index"
    conv_dir = tmp_path / "conversations"
    cfg = {
        "project": {"name": "PC-Sahayak (test)"},
        "llm": {"text_model": "test-text", "vision_model": "test-vision",
                "use_rag": True, "temperature": 0.0, "max_tokens": 300},
        "knowledge_base": {
            "markdown_directory": tmp_kb.as_posix(),
            "file_extensions": [".md", ".markdown"],
            "recursive_scan": True,
            "chunking": {"chunk_size": 400, "chunk_overlap": 60},
            "retrieval": {"top_k": 3, "similarity_threshold": None},
            "citations": {"enabled": True},
        },
        "embeddings": {"backend": "hashing", "model": "all-MiniLM-L6-v2"},
        "vector_index": {"path": index_dir.as_posix()},
        "conversation": {
            "max_history_messages": 20,
            "store_path": conv_dir.as_posix(),
            "uploads_path": (tmp_path / "uploads").as_posix(),
        },
        "logging": {"level": "WARNING"},
    }
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    keys = ("PC_HELPER_CONFIG", "PC_HELPER_KB_DIR", "PC_HELPER_INDEX_DIR",
            "PC_HELPER_CONV_DIR", "PC_HELPER_UPLOADS_DIR")
    old_env = {k: os.environ.get(k) for k in keys}
    for k in keys:
        os.environ.pop(k, None)
    os.environ["PC_HELPER_CONFIG"] = cfg_path.as_posix()

    from pc_helper.core.config import get_settings, load_settings
    get_settings.cache_clear()
    yield load_settings()
    get_settings.cache_clear()
    for k, v in old_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture()
def context(test_settings):
    """A built AppContext (real hashing index over tmp_kb) with a fake LLM."""
    from pc_helper.core.context import AppContext

    ctx = AppContext(test_settings)
    fake = FakeLLM()
    ctx.llm = fake
    ctx.engine.llm = fake
    return ctx
