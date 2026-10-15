"""UI tests: drive the real Streamlit app headlessly with streamlit.testing.AppTest.

The Groq client is replaced by the scripted FakeLLM, the knowledge base / index /
chat history live in a temp dir (see conftest.test_settings), and the reply
reveal animation is disabled so tests run fast.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture()
def app_env(test_settings, monkeypatch):
    import streamlit as st

    from pc_helper.services.llm_service import GroqLLM
    from tests.conftest import FakeLLM

    fake = FakeLLM()
    monkeypatch.setenv("PC_HELPER_REVEAL_SECONDS", "0")
    monkeypatch.setattr(
        GroqLLM, "complete",
        lambda self, messages, use_vision=False, json_mode=False: fake.complete(messages, use_vision, json_mode),
    )
    monkeypatch.setattr(GroqLLM, "is_configured", property(lambda self: True))
    st.cache_resource.clear()  # don't reuse an AppContext built for another test's temp dirs
    yield test_settings
    st.cache_resource.clear()


def run(target) -> AppTest:
    """Run an AppTest, or an element after an interaction (e.g. ``button.click()``).

    Both ``AppTest.run()`` and ``Element.run()`` return the AppTest."""
    at = target.run()
    assert not at.exception, [e.value for e in at.exception]
    return at


def all_text(at: AppTest) -> str:
    return "\n".join(m.value for m in at.markdown)


def saved_chats(settings) -> list[dict]:
    return [json.loads(p.read_text(encoding="utf-8")) for p in Path(settings.conversations_dir).glob("*.json")]


def seed_chat(settings, *, with_suggestions=True) -> str:
    from pc_helper.services.conversation_store import ConversationStore

    store = ConversationStore(settings.conversations_dir, uploads_dir=settings.uploads_dir,
                              project_root=settings.project_root)
    s = store.create()
    s.title = "Wi-Fi drops"
    s.intake_complete = True
    s.add_message("user", "My wifi keeps dropping")
    s.add_message("assistant", "Restart the router and tell me if it helps.",
                  suggestions=["It helped", "Still dropping"] if with_suggestions else [])
    store.save(s)
    return s.conversation_id


def test_new_chat_starts_with_intake_form_not_chat_box(app_env):
    at = run(AppTest.from_file(APP, default_timeout=60))
    assert at.text_area(key="intake_issue") is not None
    assert at.selectbox(key="intake_ram_type") is not None
    assert len(at.chat_input) == 0          # main chat only opens after the form


def test_empty_form_submission_is_rejected(app_env):
    at = run(AppTest.from_file(APP, default_timeout=60))
    run(at.button(key="intake_submit").click())
    assert any("describe the issue" in e.value for e in at.error)
    assert saved_chats(app_env) == []


def test_intake_form_starts_chat_saves_specs_and_history(app_env):
    at = run(AppTest.from_file(APP, default_timeout=60))
    at.selectbox(key="intake_device").select("Laptop")
    at.selectbox(key="intake_ram_size").select("16 GB")
    at.selectbox(key="intake_ram_type").select("DDR4")
    at.selectbox(key="intake_storage_type").select("NVMe SSD")
    at.text_area(key="intake_issue").input("My PC is slow")
    run(at.button(key="intake_submit").click())
    if len(at.chat_input) == 0:  # follow the app's st.rerun() if AppTest didn't already
        run(at)

    text = all_text(at)
    assert "Your system:" in text and "16 GB DDR4 RAM" in text      # profile card
    assert "Task Manager" in text                                    # assistant reply
    assert len(at.chat_input) == 1                                   # chat is now open

    chats = saved_chats(app_env)
    assert len(chats) == 1
    chat = chats[0]
    assert chat["title"] == "My PC is slow"
    assert chat["system_specs"]["ram_type"] == "DDR4"
    assert [m["role"] for m in chat["messages"]] == ["user", "assistant"]
    # …and it shows up in the sidebar history.
    assert any(b.key == f"open_{chat['conversation_id']}" for b in at.sidebar.button)


def test_saved_chat_resumes_from_url_with_chips(app_env):
    cid = seed_chat(app_env)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["chat"] = cid
    run(at)
    assert "Restart the router" in all_text(at)
    assert at.button(key="chip_0").label == "It helped"
    assert len(at.chat_input) == 1


def test_clicking_a_chip_sends_it_as_the_next_message(app_env):
    cid = seed_chat(app_env)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["chat"] = cid
    run(at)
    run(at.button(key="chip_1").click())
    if "Still dropping" not in all_text(at):
        run(at)
    chat = next(c for c in saved_chats(app_env) if c["conversation_id"] == cid)
    assert [m["content"] for m in chat["messages"]][2] == "Still dropping"
    assert chat["messages"][3]["role"] == "assistant"


def test_new_chat_button_returns_to_intake(app_env):
    cid = seed_chat(app_env)
    at = AppTest.from_file(APP, default_timeout=60)
    at.query_params["chat"] = cid
    run(at)
    run(at.sidebar.button(key="new_chat").click())
    assert at.text_area(key="intake_issue") is not None
    assert len(at.chat_input) == 0


def test_delete_chat_from_history(app_env):
    cid = seed_chat(app_env)
    at = run(AppTest.from_file(APP, default_timeout=60))
    run(at.button(key=f"del_{cid}").click())
    assert not (Path(app_env.conversations_dir) / f"{cid}.json").exists()
    assert not any(b.key == f"open_{cid}" for b in at.sidebar.button)
