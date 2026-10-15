"""Unit tests for conversation state, persistence, and LLM-output parsing."""
from __future__ import annotations

from pc_helper.models.conversation_models import ConversationState
from pc_helper.services.conversation_store import ConversationStore
from pc_helper.services.troubleshooting_service import TroubleshootingEngine


def test_state_add_and_recent_messages():
    s = ConversationState()
    for i in range(5):
        s.add_message("user", f"m{i}")
    assert len(s.messages) == 5
    assert [m.content for m in s.recent_messages(2)] == ["m3", "m4"]


def test_conversation_store_persists_to_disk(tmp_path):
    store = ConversationStore(tmp_path / "conv")
    state = store.create()
    state.add_message("user", "hello")
    state.problem_summary = "test issue"
    store.save(state)

    # A fresh store (cold cache) must read it back from disk.
    reopened = ConversationStore(tmp_path / "conv")
    loaded = reopened.get(state.conversation_id)
    assert loaded is not None
    assert loaded.problem_summary == "test issue"
    assert loaded.messages[0].content == "hello"


def test_store_rejects_path_traversal_ids(tmp_path):
    store = ConversationStore(tmp_path / "conv")
    # A crafted id must not escape the store directory.
    assert store.get("../../etc/passwd") is None


def test_parse_llm_json_handles_valid_invalid_and_wrapped():
    parse = TroubleshootingEngine._parse_llm_json
    assert parse('{"reply": "hi"}')["reply"] == "hi"
    assert parse("prefix text {\"reply\": \"x\"} trailing")["reply"] == "x"
    assert parse("not json at all") is None
    assert parse("") is None


def test_apply_state_updates_merges_facts_and_status():
    from pc_helper.models.conversation_models import SourceRef

    state = ConversationState()
    TroubleshootingEngine._apply_state_updates(
        state,
        {
            "issue_category": "network",
            "problem_summary": "no internet",
            "new_known_facts": ["router light is red", "router light is red"],
            "current_step": "check router",
            "completed_step": "checked cables",
        },
        status="diagnosing",
        sources=[SourceRef(file="networking/wifi.md", heading="Fixes")],
    )
    assert state.issue_category == "network"
    assert state.known_facts.count("router light is red") == 1  # de-duplicated
    assert state.current_step == "check router"
    assert "checked cables" in state.completed_steps
    assert state.retrieved_sources[0].file == "networking/wifi.md"


# --------------------------------------------------------------------------- #
# Intake specs
# --------------------------------------------------------------------------- #
def test_specs_summary_skips_unknown_fields():
    from pc_helper.models.conversation_models import UNKNOWN, SystemSpecs

    specs = SystemSpecs(device_type="Desktop", os="Windows 10", os_version=None,
                        ram_size="8 GB", ram_type=UNKNOWN, storage_size=UNKNOWN, storage_type="HDD (hard disk)")
    assert specs.summary() == "Desktop · Windows 10 · 8 GB RAM · HDD (hard disk) storage"
    assert SystemSpecs().summary() == "No system details provided"


# --------------------------------------------------------------------------- #
# Local chat history
# --------------------------------------------------------------------------- #
def _store(tmp_path):
    return ConversationStore(tmp_path / "conv", uploads_dir=tmp_path / "uploads", project_root=tmp_path)


def test_history_lists_only_chats_with_messages_newest_first(tmp_path):
    import time

    store = _store(tmp_path)
    empty = store.create()                      # never used -> hidden from history
    older = store.create()
    older.title = "Wi-Fi drops"
    older.add_message("user", "wifi drops")
    store.save(older)
    time.sleep(0.01)
    newer = store.create()
    newer.add_message("user", "PC is slow")     # no title -> falls back to first message
    store.save(newer)

    items = store.list_conversations()
    assert [i.conversation_id for i in items] == [newer.conversation_id, older.conversation_id]
    assert items[0].title == "PC is slow" and items[1].title == "Wi-Fi drops"
    assert empty.conversation_id not in {i.conversation_id for i in items}


def test_resume_round_trip_keeps_metadata(tmp_path):
    from pc_helper.models.conversation_models import SourceRef

    store = _store(tmp_path)
    s = store.create()
    s.add_message("assistant", "Try this", sources=[SourceRef(file="a.md", heading="Fix")], suggestions=["Yes", "No"])
    store.save(s)

    reloaded = _store(tmp_path).get(s.conversation_id)  # fresh store = cold cache, read from disk
    msg = reloaded.messages[0]
    assert msg.sources[0].file == "a.md" and msg.suggestions == ["Yes", "No"]


def test_save_image_and_delete_removes_files(tmp_path):
    store = _store(tmp_path)
    s = store.create()
    rel = store.save_image(s.conversation_id, b"\x89PNG fake", "my error?.png")
    path = store.resolve_image(rel)
    assert path is not None and path.read_bytes() == b"\x89PNG fake"
    assert not rel.startswith("/") and ".." not in rel     # stored relative + sanitized

    assert store.delete(s.conversation_id) is True
    assert store.get(s.conversation_id) is None
    assert store.resolve_image(rel) is None                # uploads removed too


def test_old_conversation_files_still_load(tmp_path):
    """Chats saved before the intake/metadata fields existed must still resume."""
    import json

    store = _store(tmp_path)
    legacy = {"conversation_id": "legacy1", "messages": [{"role": "user", "content": "hi", "timestamp": 1.0}]}
    (tmp_path / "conv" / "legacy1.json").write_text(json.dumps(legacy), encoding="utf-8")
    state = store.get("legacy1")
    assert state is not None and state.messages[0].kind == "normal" and state.system_specs is None


def test_moving_to_a_new_step_completes_the_previous_one():
    from pc_helper.services.troubleshooting_service import TroubleshootingEngine

    state = ConversationState()
    TroubleshootingEngine._apply_state_updates(state, {"current_step": "Restart the router"}, "diagnosing", [])
    TroubleshootingEngine._apply_state_updates(state, {"current_step": "Flush the DNS cache"}, "diagnosing", [])
    TroubleshootingEngine._apply_state_updates(state, {"current_step": "Flush the DNS cache"}, "diagnosing", [])
    assert state.completed_steps == ["Restart the router"]
    assert state.current_step == "Flush the DNS cache"
