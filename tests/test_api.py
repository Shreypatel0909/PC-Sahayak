"""API tests: the FastAPI layer the React UI talks to.

Uses the hermetic ``context`` fixture (temp knowledge base + index + chat store,
scripted FakeLLM), so no network or API credits are used.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from api.categories import classify_text, resolve_category
from pc_helper.models.conversation_models import ConversationState

SPECS = {"device_type": "Laptop", "os": "Windows 11", "os_version": "23H2", "ram_size": "16 GB",
         "ram_type": "DDR4", "storage_size": "512 GB", "storage_type": "NVMe SSD"}
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


@pytest.fixture()
def client(context):
    from api.main import create_app

    with TestClient(create_app(context)) as c:
        c.ctx = context
        yield c


def start(client, issue="My laptop is running slowly", files=None):
    return client.post("/api/conversations", data={"specs": json.dumps(SPECS), "issue": issue}, files=files)


def test_meta_lists_options_and_models(client):
    r = client.get("/api/meta")
    assert r.status_code == 200
    body = r.json()
    assert "Laptop" in body["options"]["device_types"]
    assert body["llm"]["text_model"] == "test-text"
    assert body["kb"]["documents"] == 2
    assert body["last_specs"] is None


def test_start_conversation_runs_the_engine(client):
    r = start(client)
    assert r.status_code == 200
    conv = r.json()
    assert conv["title"] == "My laptop is running slowly"
    assert [m["role"] for m in conv["messages"]] == ["user", "assistant"]
    assert conv["messages"][1]["suggestions"] == ["Under 50%", "Over 90%"]
    # The colour comes from the category the LLM set, and the route from state.
    assert conv["category"] == "performance"
    assert conv["route"] == {"origin": "PC is running slowly", "done": [],
                             "current": "Check CPU usage in Task Manager", "fixed": False}
    assert conv["specs"]["ram_size"] == "16 GB"
    # Specs are offered back to pre-fill the next intake form.
    assert client.get("/api/meta").json()["last_specs"]["os_version"] == "23H2"


def test_start_requires_issue_or_screenshot(client):
    r = start(client, issue="  ")
    assert r.status_code == 422
    assert "screenshot" in r.json()["detail"]


def test_follow_up_message_and_listing(client):
    cid = start(client).json()["id"]
    r = client.post(f"/api/conversations/{cid}/messages", data={"text": "Over 90%"})
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 4
    listing = client.get("/api/conversations").json()
    assert listing[0]["id"] == cid
    assert listing[0]["category"] == "performance"
    assert listing[0]["steps"] == 1


def test_screenshot_upload_is_stored_and_served(client):
    r = start(client, issue="", files={"image": ("error.png", PNG, "image/png")})
    assert r.status_code == 200
    conv = r.json()
    url = conv["messages"][0]["image_url"]
    assert url.startswith(f"/api/uploads/{conv['id']}/")
    assert conv["messages"][1]["content"].startswith("I can see a Windows error dialog")
    img = client.get(url)
    assert img.status_code == 200 and img.content == PNG


def test_rejects_non_image_upload(client):
    r = start(client, files={"image": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 415


def test_upload_path_traversal_is_blocked(client):
    cid = start(client).json()["id"]
    assert client.get(f"/api/uploads/{cid}/..%2F..%2Fconfig.yaml").status_code == 404


def test_llm_failure_is_recorded_and_retry_recovers(client):
    from tests.conftest import FailingLLM, FakeLLM

    client.ctx.engine.llm = FailingLLM()
    conv = start(client).json()
    assert conv["messages"][-1]["kind"] == "error"

    client.ctx.engine.llm = FakeLLM()
    r = client.post(f"/api/conversations/{conv['id']}/retry")
    assert r.status_code == 200
    roles = [(m["role"], m["kind"]) for m in r.json()["messages"]]
    assert roles == [("user", "normal"), ("assistant", "normal")]


def test_retry_without_error_is_rejected(client):
    cid = start(client).json()["id"]
    assert client.post(f"/api/conversations/{cid}/retry").status_code == 409


def test_delete_one_and_all(client):
    a = start(client).json()["id"]
    start(client, issue="Wi-Fi keeps dropping")
    assert client.delete(f"/api/conversations/{a}").status_code == 200
    assert client.get(f"/api/conversations/{a}").status_code == 404
    assert client.delete("/api/conversations").json() == {"deleted": 1}
    assert client.get("/api/conversations").json() == []


def test_reindex(client):
    r = client.post("/api/reindex")
    assert r.status_code == 200
    assert r.json()["documents"] == 2


@pytest.mark.parametrize("label,expected", [
    ("network", "network"), ("Wi-Fi", "network"), ("Windows boot", "boot"), ("bogus", None),
])
def test_category_from_llm_label(label, expected):
    state = ConversationState(issue_category=label, problem_summary="something odd")
    assert resolve_category(state) == (expected or "other")


def test_category_falls_back_to_keywords():
    assert classify_text("My laptop gets too hot when gaming") == "hardware"
    assert classify_text("Stuck on Preparing Automatic Repair") == "boot"
    assert resolve_category(ConversationState(title="My C drive is almost full")) == "performance"


def test_off_topic_question_leaves_the_diagnosis_alone(client):
    conv = start(client).json()
    r = client.post(f"/api/conversations/{conv['id']}/messages", data={"text": "What is the capital of France?"})
    after = r.json()
    reply = after["messages"][-1]
    assert reply["tag"] == "off_topic"
    assert reply["suggestions"] == []
    assert after["category"] == "performance"
    assert after["route"] == conv["route"]
    assert after["status"] == "diagnosing"


def test_off_topic_first_message_has_no_route(client):
    conv = start(client, issue="What is the capital of France?").json()
    assert conv["messages"][-1]["tag"] == "off_topic"
    assert conv["route"]["origin"] == ""


def test_saying_it_worked_closes_and_locks_the_chat(client):
    cid = start(client).json()["id"]
    r = client.post(f"/api/conversations/{cid}/messages", data={"text": "Yes, that worked!"})
    conv = r.json()
    assert conv["status"] == "resolved" and conv["locked"] is True
    assert conv["messages"][-1]["tag"] == "summary"
    assert conv["route"]["fixed"] is True
    assert conv["route"]["done"] == ["Check CPU usage in Task Manager"]
    blocked = client.post(f"/api/conversations/{cid}/messages", data={"text": "one more thing"})
    assert blocked.status_code == 409 and "Unlock" in blocked.json()["detail"]


def test_resolve_button_summarises_then_unlock_allows_chatting(client):
    cid = start(client).json()["id"]
    conv = client.post(f"/api/conversations/{cid}/resolve").json()
    assert conv["locked"] is True
    assert conv["messages"][-2]["content"] == "This solved my problem."
    assert conv["messages"][-1]["content"].startswith("**Fixed**")
    assert client.post(f"/api/conversations/{cid}/resolve").status_code == 409

    unlocked = client.post(f"/api/conversations/{cid}/unlock").json()
    assert unlocked["locked"] is False
    r = client.post(f"/api/conversations/{cid}/messages", data={"text": "It came back"})
    assert r.status_code == 200


# --- local-network mode -------------------------------------------------------
@pytest.fixture()
def lan_client(context):
    from api.main import create_app

    # TestClient requests come from host "testclient", i.e. another device.
    with TestClient(create_app(context, access_code="K7Q2M9")) as c:
        yield c


def test_network_mode_blocks_devices_without_the_link(lan_client):
    assert lan_client.get("/api/meta").status_code == 401
    page = lan_client.get("/", follow_redirects=False)
    assert page.status_code == 401 and "access link" in page.text
    assert lan_client.get("/?access=WRONG", follow_redirects=False).status_code == 401


def test_network_mode_share_link_sets_a_cookie(lan_client):
    r = lan_client.get("/?access=K7Q2M9", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/"
    assert "K7Q2M9" not in r.headers["set-cookie"]  # the code itself is never stored
    meta = lan_client.get("/api/meta")
    assert meta.status_code == 200
    assert meta.json()["share_urls"] == []  # share links are only shown on the host PC


def test_this_computer_never_needs_the_code(context):
    from api.main import create_app

    with TestClient(create_app(context, access_code="K7Q2M9"), client=("127.0.0.1", 50000)) as c:
        assert c.get("/api/meta").status_code == 200


def test_meta_reports_version(client):
    from pc_helper import __version__

    assert client.get("/api/meta").json()["version"] == __version__ == "1.3.1"


# --- closing the app ------------------------------------------------------------
def test_close_from_this_computer_stops_the_server(context):
    from api.main import create_app

    app = create_app(context)
    calls = []
    app.state.shutdown = lambda: calls.append("stop")
    with TestClient(app, client=("127.0.0.1", 50000)) as c:
        assert c.get("/api/meta").json()["is_host"] is True
        r = c.post("/api/shutdown")
    assert r.status_code == 200 and r.json() == {"closing": True}
    assert calls == ["stop"]


def test_other_devices_cannot_close_the_app(context):
    from api.main import create_app

    app = create_app(context, access_code="K7Q2M9")
    calls = []
    app.state.shutdown = lambda: calls.append("stop")
    with TestClient(app) as c:  # host "testclient" = another device
        c.get("/?access=K7Q2M9", follow_redirects=False)
        assert c.get("/api/meta").json()["is_host"] is False
        r = c.post("/api/shutdown")
    assert r.status_code == 403
    assert calls == []
