"""Tests for the native OpenCode continuation adapter."""
import json
from io import BytesIO
from unittest.mock import patch

from importers.opencode_resume import create_opencode_session


def test_creates_session_queues_context_without_resuming_agent(monkeypatch):
    calls = []

    def fake_urlopen(request, timeout=15.0):
        calls.append(request)
        path = request.full_url.replace("http://127.0.0.1:4096", "")
        if path == "/api/info":
            payload = {}
        elif path == "/api/session":
            payload = {"data": {"id": "ses_test123"}}
        elif path == "/api/session/ses_test123/prompt":
            body = json.loads(request.data.decode("utf-8"))
            assert body["resume"] is False
            assert "AgentSON continuation packet" in body["text"]
            payload = {"data": {"id": "inbox_test123"}}
        elif path == "/api/session/ses_test123/message":
            payload = {"data": [{"info": {"text": "# AgentSON continuation packet"}}]}
        else:
            raise AssertionError("Unexpected request: " + path)
        return BytesIO(json.dumps(payload).encode("utf-8"))

    with patch("importers.opencode_resume.urlopen", side_effect=fake_urlopen):
        session_id = create_opencode_session("# AgentSON continuation packet\nSafe context")

    assert session_id == "ses_test123"
    assert [request.get_method() for request in calls] == ["GET", "POST", "POST", "GET"]


def test_uses_basic_auth_from_environment(monkeypatch):
    seen = []

    def fake_urlopen(request, timeout=15.0):
        seen.append(request.get_header("Authorization"))
        path = request.full_url.replace("http://127.0.0.1:4096", "")
        if path == "/api/info":
            payload = {}
        elif path == "/api/session":
            payload = {"data": {"id": "ses_auth"}}
        elif path.endswith("/prompt"):
            payload = {"data": {"id": "queued"}}
        else:
            payload = {"data": [{"info": {"text": "AgentSON continuation packet"}}]}
        return BytesIO(json.dumps(payload).encode("utf-8"))

    monkeypatch.setenv("OPENCODE_SERVER_USERNAME", "operator")
    monkeypatch.setenv("OPENCODE_SERVER_PASSWORD", "secret")
    with patch("importers.opencode_resume.urlopen", side_effect=fake_urlopen):
        create_opencode_session("AgentSON continuation packet")

    assert all(value == "Basic b3BlcmF0b3I6c2VjcmV0" for value in seen)


def test_rejects_non_http_server_url():
    try:
        create_opencode_session("packet", server_url="file:///tmp/opencode")
    except ValueError as exc:
        assert "http://" in str(exc)
    else:
        raise AssertionError("Expected an invalid URL to be rejected")
