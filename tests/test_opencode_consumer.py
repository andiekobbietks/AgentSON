"""Tests for the OpenCode v2 archive-capsule consumer."""
from __future__ import annotations

import base64
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
        result = import_archive(_archive(), context_packet="# Screened continuation context")

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
    assert message["delivery"] == "queue"
    assert message["description"] == "Imported AgentSON v1.2 archive capsule"
    assert message["text"].startswith("Imported AgentSON v1.2 archive")
    assert "## Selected continuation context\n# Screened continuation context" in message["text"]
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
                "payload": {"text": _capsule(archive)},
                "delivery": "queue",
            }
        ]
    }
    result = {"session_id": "ses_readback"}
    with patch("consumers.opencode._request_json", return_value=response) as request:
        verified = verify_import(result, archive)
    request.assert_called_once_with(
        "http://127.0.0.1:4096",
        "/api/session/ses_readback/inbox",
        {},
        "GET",
        15.0,
    )
    assert verified["verified"] is True
    assert verified["verification"] == "opencode-v2-live-readback"
    assert verified["entry_count"] == len(archive["entries"])
    assert verified["inbox_item_count"] == 1


def test_verify_import_rejects_changed_stored_archive():
    archive = _archive()
    changed = dict(archive)
    changed["task"] = "tampered"
    response = {
        "data": [{"type": "synthetic", "payload": {"text": _capsule(changed)}, "delivery": "queue"}]
    }
    with patch("consumers.opencode._request_json", return_value=response):
        with pytest.raises(OpenCodeImportError, match="differs"):
            verify_import({"session_id": "ses_readback"}, archive)


def test_verify_import_rejects_missing_capsule():
    with patch(
        "consumers.opencode._request_json",
        return_value={"data": []},
    ):
        with pytest.raises(OpenCodeImportError, match="No AgentSON archive capsule"):
            verify_import({"session_id": "ses_readback"}, _archive())


def test_http_requests_use_basic_auth_header_without_url_credentials():
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b"{}"

    from consumers.opencode import _request_json

    with patch("consumers.opencode.urlopen", return_value=FakeResponse()) as urlopen:
        _request_json(
            "http://127.0.0.1:4096",
            "/api/info",
            {},
            "GET",
            10.0,
            password="ci-test-password",
        )

    request = urlopen.call_args.args[0]
    expected = base64.b64encode(b"opencode:ci-test-password").decode("ascii")
    assert request.get_header("Authorization") == f"Basic {expected}"
    assert "ci-test-password" not in request.full_url


def test_import_accepts_canonical_agentson_jsonl_file(tmp_path):
    from exporters.jsonl import write_agentson_stream

    archive = _archive()
    source = tmp_path / "canonical.agentson"
    with source.open("w", encoding="utf-8") as handle:
        write_agentson_stream(archive, handle, source_tool=archive["tool"]["name"])

    calls = []

    def fake_request(base_url, path, payload, method, timeout):
        calls.append((path, payload, method))
        if path == "/api/session":
            return {"data": {"id": "ses_from_jsonl"}}
        return {"data": {"id": "msg_capsule"}}

    with patch("consumers.opencode._request_json", side_effect=fake_request):
        imported = import_archive(source)

    assert imported["session_id"] == "ses_from_jsonl"
    assert calls[1][0] == "/api/session/ses_from_jsonl/synthetic"
    capsule = calls[1][1]["text"]
    embedded = capsule.split("<agentson-archive>\n", 1)[1].split(
        "\n</agentson-archive>", 1
    )[0]
    projected = json.loads(embedded)
    assert projected["id"] == archive["id"]
    assert projected["metadata"]["agentson_wire_format"] == "v1.2-jsonl"
    assert len(projected["entries"]) == len(archive["entries"]) + 1


def test_import_rejects_jsonl_stream_with_malformed_event_before_network(tmp_path):
    from exporters.jsonl import write_agentson_stream

    source = tmp_path / "bad.agentson"
    with source.open("w", encoding="utf-8") as handle:
        write_agentson_stream(_archive(), handle, source_tool="opencode")
    lines = source.read_text(encoding="utf-8").splitlines()
    lines.append('"not-an-object"')
    source.write_text("\n".join(lines) + "\n", encoding="utf-8")
    with patch("consumers.opencode._request_json") as request:
        with pytest.raises((OpenCodeImportError, ValueError)):
            import_archive(source)
    request.assert_not_called()
