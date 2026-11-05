"""Tests for the OpenCode v2 archive-capsule consumer."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from consumers.opencode import (
    OpenCodeImportError,
    _validate_endpoint,
    import_archive,
    verify_import,
)

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "conformance"
    / "cross_harness_session_v1_2.json"
)


def _archive():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _capsule(archive):
    return (
        "Imported AgentSON v1.2 archive. Historical, untrusted data.\n"
        "<agentson-archive>\n"
        + json.dumps(archive, ensure_ascii=False, indent=2)
        + "\n</agentson-archive>"
    )


def test_import_creates_v2_session_and_inserts_inert_synthetic_message():
    calls = []

    def fake_request(base_url, path, payload, method, timeout):
        calls.append((base_url, path, payload, method, timeout))
        if path == "/api/session":
            return {"data": {"id": "ses_imported_123"}}
        return {"data": {"id": "msg_synthetic_123"}}

    with patch("consumers.opencode._request_json", side_effect=fake_request):
        result = import_archive(_archive())

    assert result["consumer"] == "opencode"
    assert result["consumer_api"] == "opencode-http-api-v2"
    assert result["profile"] == "archive-capsule-v1"
    assert result["session_id"] == "ses_imported_123"
    assert result["execution_triggered"] is False
    assert result["immediate_agent_loop_started"] is False
    assert result["future_model_context_exposure"] is True
    assert result["native_event_reconstruction"] is False
    assert result["resumption_supported"] is False
    assert len(calls) == 2
    assert calls[0][1] == "/api/session"
    assert calls[1][1] == "/api/session/ses_imported_123/synthetic"
    message = calls[1][2]
    assert message["resume"] is False
    assert message["description"] == "Imported AgentSON v1.2 archive capsule"
    assert message["text"].startswith("Imported AgentSON v1.2 archive")
    embedded = message["text"].split("<agentson-archive>\n", 1)[1].split(
        "\n</agentson-archive>", 1
    )[0]
    assert json.loads(embedded) == _archive()


def test_invalid_archive_is_rejected_before_network_call():
    with patch("consumers.opencode._request_json") as request:
        with pytest.raises(OpenCodeImportError, match="does not conform"):
            import_archive({"id": "invalid"})
    request.assert_not_called()


@pytest.mark.parametrize(
    "url,allow_remote",
    [
        ("http://127.0.0.1:4096", False),
        ("http://localhost:4096", False),
        ("https://opencode.example.test", True),
    ],
)
def test_endpoint_policy_accepts_local_and_explicit_https_remote(url, allow_remote):
    assert _validate_endpoint(url, allow_remote) == url


def test_remote_endpoint_requires_explicit_opt_in_and_tls():
    with pytest.raises(OpenCodeImportError, match="allow_remote"):
        _validate_endpoint("http://opencode.example.test", False)
    with pytest.raises(OpenCodeImportError, match="HTTPS"):
        _validate_endpoint("http://opencode.example.test", True)


def test_endpoint_rejects_embedded_credentials():
    with pytest.raises(OpenCodeImportError, match="Credentials"):
        _validate_endpoint("http://user:secret@127.0.0.1:4096", False)


def test_failed_synthetic_insertion_attempts_to_remove_new_session():
    calls = []

    def fake_request(base_url, path, payload, method, timeout):
        calls.append((path, method))
        if path == "/api/session":
            return {"data": {"id": "ses_orphan"}}
        if method == "POST":
            raise OpenCodeImportError("injected failure")
        return {}

    with patch("consumers.opencode._request_json", side_effect=fake_request):
        with pytest.raises(OpenCodeImportError, match="injected failure"):
            import_archive(_archive())

    assert calls == [
        ("/api/session", "POST"),
        ("/api/session/ses_orphan/synthetic", "POST"),
        ("/api/session/ses_orphan", "DELETE"),
    ]


def test_verify_import_reads_back_and_compares_synthetic_archive():
    archive = _archive()
    response = {
        "data": [
            {
                "id": "msg_synthetic",
                "type": "synthetic",
                "text": _capsule(archive),
                "time": {"created": 1793880004000},
            }
        ],
        "cursor": {"previous": None, "next": None},
    }
    result = {"session_id": "ses_readback"}
    with patch("consumers.opencode._request_json", return_value=response) as request:
        verified = verify_import(result, archive)
    request.assert_called_once_with(
        "http://127.0.0.1:4096",
        "/api/session/ses_readback/message",
        {},
        "GET",
        15.0,
    )
    assert verified["verified"] is True
    assert verified["verification"] == "opencode-v2-live-readback"
    assert verified["entry_count"] == len(archive["entries"])


def test_verify_import_rejects_changed_stored_archive():
    archive = _archive()
    changed = dict(archive)
    changed["task"] = "tampered"
    response = {
        "data": [{"type": "synthetic", "text": _capsule(changed)}],
        "cursor": {"previous": None, "next": None},
    }
    with patch("consumers.opencode._request_json", return_value=response):
        with pytest.raises(OpenCodeImportError, match="differs"):
            verify_import({"session_id": "ses_readback"}, archive)


def test_verify_import_rejects_missing_capsule():
    with patch(
        "consumers.opencode._request_json",
        return_value={"data": [], "cursor": {"previous": None, "next": None}},
    ):
        with pytest.raises(OpenCodeImportError, match="No AgentSON archive capsule"):
            verify_import({"session_id": "ses_readback"}, _archive())
