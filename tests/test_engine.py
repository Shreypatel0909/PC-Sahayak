"""Integration tests for the troubleshooting engine (real index + fake LLM)."""
from __future__ import annotations

import pytest


def test_context_builds_index(context):
    assert context.index.chunks > 0
    assert context.index.documents == 2


def test_text_turn_returns_grounded_reply(context):
    state = context.conversation_store.create()
    result = context.engine.respond(state, "My PC is slow", category="Performance Issues")
    assert result.reply
    assert result.status == "diagnosing"
    assert result.suggested_answers              # quick replies offered
    assert result.sources                        # citation from retrieved context
    assert result.step_info.current_step
    # Structured state was updated and the transcript recorded both turns.
    assert state.problem_summary == "PC is running slowly"
    assert [m.role for m in state.messages] == ["user", "assistant"]


def test_destructive_request_is_refused(context):
    state = context.conversation_store.create()
    result = context.engine.respond(state, "Give me a command to delete all system files")
    assert "can't" in result.reply.lower() or "cannot" in result.reply.lower()
    assert result.sources == []


def test_empty_message_raises(context):
    state = context.conversation_store.create()
    with pytest.raises(ValueError):
        context.engine.respond(state, "   ")


def test_multi_turn_keeps_history(context):
    state = context.conversation_store.create()
    context.engine.respond(state, "My PC is slow")
    context.engine.respond(state, "CPU is at 95%")
    roles = [m.role for m in state.messages]
    assert roles == ["user", "assistant", "user", "assistant"]


def test_intake_specs_reach_the_prompt_with_do_not_reask_rule(context):
    from pc_helper.models.conversation_models import SystemSpecs

    state = context.conversation_store.create()
    state.apply_specs(SystemSpecs(device_type="Laptop", os="Windows 11", os_version="23H2",
                                  ram_size="16 GB", ram_type="DDR4",
                                  storage_size="512 GB", storage_type="NVMe SSD"))
    context.engine.respond(state, "My PC is slow")

    prompt = "\n".join(m["content"] for m in context.llm.calls[-1] if m["role"] == "system")
    assert "Windows 11 23H2" in prompt
    assert "16 GB DDR4 RAM" in prompt
    assert "512 GB NVMe SSD storage" in prompt
    assert "do NOT ask for these again" in prompt
    # Seeded fields that retrieval also uses.
    assert state.operating_system == "Windows 11 23H2"
    assert state.device == "Laptop"


def test_assistant_message_keeps_sources_and_suggestions_for_resume(context):
    state = context.conversation_store.create()
    context.engine.respond(state, "My PC is slow")
    reply = state.messages[-1]
    assert reply.role == "assistant"
    assert reply.sources and reply.suggestions == ["Under 50%", "Over 90%"]


def test_vision_turn_stores_image_path_on_user_message(context):
    state = context.conversation_store.create()
    result = context.engine.respond(
        state, "What is this error?", image_data_url="data:image/png;base64,AAAA",
        image_path="data/uploads/x/shot.png",
    )
    assert "error" in result.reply.lower()
    assert state.messages[0].image_path == "data/uploads/x/shot.png"


def test_llm_failure_is_recorded_but_not_sent_back_to_the_model(context):
    from tests.conftest import FailingLLM, FakeLLM
    from pc_helper.services.llm_service import LLMError

    state = context.conversation_store.create()
    context.engine.llm = FailingLLM()
    with pytest.raises(LLMError):
        context.engine.respond(state, "My PC is slow")
    assert state.messages[-1].kind == "error"

    # Next turn works, and the error text is excluded from the model's context.
    fake = FakeLLM()
    context.engine.llm = fake
    context.engine.respond(state, "Trying again")
    sent = [m["content"] for m in fake.calls[-1] if m["role"] == "assistant"]
    assert not any("unavailable" in str(c) for c in sent)


def test_reindex_returns_stats(context):
    stats = context.reindex()
    assert stats.chunks > 0
    assert stats.documents == 2
