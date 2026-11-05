"""Tests for canonical AgentSON v1.2 JSONL exports."""
import json

from exporters.jsonl import to_v1_2_events, validate_v1_2_events, write_agentson_stream


def test_export_writes_v12_jsonl_but_keeps_agentson_extension(tmp_path):
    session = {
        "id": "session-123",
        "tool": {"name": "opencode", "session_id": "native-123"},
        "agent": {"name": "gpt-test", "provider": "example"},
        "started_at": "2026-11-05T10:00:00Z",
        "metadata": {"source_build": "fixture"},
        "entries": [
            {"type": "user-query", "text": "Run the tests", "timestamp": "2026-11-05T10:00:01Z"},
            {"type": "action", "tool": "shell.run", "code": "pytest -q", "status": "completed"},
            {"type": "observation", "source": "tool", "text": "3 passed"},
            {"type": "answer", "text": "All tests passed."},
        ],
    }
    output = tmp_path / "opencode_session-123.agentson"

    with output.open("w", encoding="utf-8") as handle:
        events = write_agentson_stream(session, handle, source_tool="opencode")

    lines = output.read_text(encoding="utf-8").splitlines()
    assert output.suffix == ".agentson"
    assert len(lines) == 5
    parsed = [json.loads(line) for line in lines]
    assert parsed == events
    assert parsed[0]["type"] == "stream-meta"
    assert parsed[0]["schema_version"] == "1.2"
    assert parsed[0]["source_session"]["tool"] == "opencode"
    assert parsed[0]["source_session"]["session_id"] == "native-123"
    assert parsed[1]["type"] == "user-query"
    assert parsed[1]["timestamp"] == 1793872801000
    assert parsed[2]["status"] == "success"
    assert parsed[2]["source_payload"]["status"] == "completed"
    assert parsed[3]["source"] == "tool"
    assert parsed[4]["type"] == "answer"
    validate_v1_2_events(parsed)


def test_unknown_source_event_is_retained_not_silently_dropped():
    events = to_v1_2_events(
        {
            "id": "unknown-event",
            "tool": {"name": "example", "session_id": "s1"},
            "entries": [{"type": "vendor-private-event", "payload": {"x": 1}}],
        },
        source_tool="example",
    )
    assert events[1]["type"] == "system-event"
    assert events[1]["provenance"]["confidence"] == "unknown"
    assert events[1]["source_payload"]["type"] == "vendor-private-event"
    assert events[1]["source_payload"]["payload"] == {"x": 1}
    validate_v1_2_events(events)


def test_existing_v12_stream_is_not_wrapped_twice():
    source = [
        {"type": "stream-meta", "stream_id": "existing", "mode": "single", "agents": [{"id": "a"}]},
        {"type": "answer", "text": "Already canonical"},
    ]
    events = to_v1_2_events({"id": "existing", "entries": source})
    assert len(events) == 2
    assert events[0]["type"] == "stream-meta"
    assert events[1]["text"] == "Already canonical"
    validate_v1_2_events(events)


def test_invalid_stream_without_stream_meta_is_rejected():
    try:
        validate_v1_2_events([{"type": "answer", "text": "No header"}])
    except ValueError as exc:
        assert "stream-meta" in str(exc)
    else:
        raise AssertionError("Expected invalid stream to be rejected")



def test_cli_export_path_writes_jsonl_with_agentson_suffix(tmp_path, monkeypatch):
    from argparse import Namespace
    import cli.main as cli_main
    import readers.minimax as minimax_reader

    db_path = tmp_path / "minimax.sqlite"
    db_path.write_bytes(b"fixture")
    output_dir = tmp_path / "exports"
    session = {
        "id": "minimax-session",
        "tool": {"name": "minimax", "session_id": "native-minimax-session"},
        "entries": [{"type": "user-query", "text": "hello"}],
    }
    monkeypatch.setattr(cli_main, "get_default_db_paths", lambda: {"minimax": db_path})
    monkeypatch.setattr(minimax_reader, "read", lambda _path, _sid: session)

    cli_main.cmd_export(Namespace(
        tool="minimax",
        output=str(output_dir),
        all=False,
        session="native-minimax-session",
        input=None,
    ))

    exported = output_dir / "minimax_native-minimax-session.agentson"
    assert exported.exists()
    lines = exported.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "stream-meta"
    assert json.loads(lines[1])["type"] == "user-query"



def test_loader_recognises_single_event_jsonl_stream(tmp_path):
    from cli.main import _load_agentson

    source = tmp_path / "single-event.agentson"
    source.write_text(json.dumps({
        "type": "stream-meta",
        "stream_id": "one-line",
        "mode": "single",
        "agents": [{"id": "assistant"}],
    }), encoding="utf-8")

    loaded = _load_agentson(source)
    assert loaded["_format"] == "jsonl"
    assert loaded["id"] == "one-line"
    assert loaded["entries"][0]["type"] == "stream-meta"


def test_loader_keeps_legacy_document_style_agentson_readable(tmp_path):
    from cli.main import _load_agentson

    source = tmp_path / "legacy.agentson"
    source.write_text(json.dumps({
        "id": "legacy-session",
        "tool": {"name": "opencode", "session_id": "legacy-session"},
        "entries": [{"type": "answer", "text": "legacy"}],
    }), encoding="utf-8")

    loaded = _load_agentson(source)
    assert loaded["id"] == "legacy-session"
    assert loaded["entries"][0]["text"] == "legacy"



def test_redaction_preserves_jsonl_and_redacts_source_payload(tmp_path):
    from tools.pii_redactor import PIIRedactor

    original = tmp_path / "private.agentson"
    redacted = tmp_path / "private-redacted.agentson"
    session = {
        "id": "private-session",
        "tool": {"name": "opencode", "session_id": "native-private"},
        "entries": [{"type": "user-query", "text": "Contact me at person@example.com"}],
    }
    with original.open("w", encoding="utf-8") as handle:
        write_agentson_stream(session, handle, source_tool="opencode")

    stats = PIIRedactor(use_model=False).redact_file(str(original), str(redacted))
    lines = redacted.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines]

    assert stats["total_redactions"] >= 1
    assert len(events) == 2
    assert events[0]["type"] == "stream-meta"
    assert "[PRIVATE_EMAIL]" in events[1]["text"]
    assert "[PRIVATE_EMAIL]" in events[1]["source_payload"]["text"]
    validate_v1_2_events(events)


def test_reader_specific_session_metadata_survives_projection():
    """Fields outside the common session shape must remain inspectable."""
    source = {
        "id": "antigravity-session",
        "version": "1.0.0",
        "tool": {"id": "antigravity", "name": "Antigravity IDE", "version": "1.0.0"},
        "agent": {"id": "gemini", "name": "Gemini", "model": "gemini-2.0-flash"},
        "variant": {"id": "antigravity", "name": "Antigravity IDE", "version": "1.0.0"},
        "metrics": {"total_tokens": 0, "cost": 0.0, "total_turns": 1},
        "entries": [{"role": "assistant", "type": 21, "text": "run command", "timestamp": "2026-11-05T10:00:00+00:00"}],
    }
    events = to_v1_2_events(source, source_tool="antigravity")
    retained = events[0]["source_session"]["source_metadata"]
    assert retained["version"] == "1.0.0"
    assert retained["variant"]["name"] == "Antigravity IDE"
    assert retained["metrics"]["total_turns"] == 1
    assert events[1]["source_payload"]["type"] == 21
    assert events[1]["source_payload"]["role"] == "assistant"
    validate_v1_2_events(events)


def test_opencode_real_reader_shape_round_trips_through_canonical_stream(tmp_path):
    """Use the checked-in real OpenCode message/parts sample as a regression fixture."""
    from pathlib import Path
    fixture_path = Path(__file__).parent / "fixtures" / "opencode_real_sample.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    message = fixture["message"]
    reader_entries = [
        {
            "type": "thought",
            "text": fixture["parts"][0]["text"],
            "timestamp": fixture["parts"][0]["time"]["start"],
        },
        {
            "type": "action",
            "tool": fixture["parts"][1]["tool"],
            "code": json.dumps(fixture["parts"][1]["state"]["input"]),
            "output": fixture["parts"][1]["state"]["output"],
            "status": "success",
        },
    ]
    session = {
        "id": message["sessionID"],
        "tool": {"name": "opencode", "session_id": message["sessionID"]},
        "agent": {"name": message["modelID"], "provider": message["providerID"]},
        "metadata": {"message_id": message["id"], "finish": message["finish"]},
        "entries": reader_entries,
    }
    output = tmp_path / "opencode-real-sample.agentson"
    with output.open("w", encoding="utf-8") as handle:
        write_agentson_stream(session, handle, source_tool="opencode")
    parsed = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [event["type"] for event in parsed] == ["stream-meta", "thought", "action"]
    assert parsed[1]["source_payload"]["text"] == "Now run the test script."
    assert parsed[2]["source_payload"]["status"] == "success"
    assert parsed[0]["source_session"]["metadata"]["message_id"] == message["id"]
    validate_v1_2_events(parsed)


def test_claude_reader_direct_export_uses_canonical_jsonl(tmp_path, monkeypatch):
    from readers.claude_code import ClaudeCodeReader

    reader = ClaudeCodeReader(config_dir=str(tmp_path / "claude"))
    monkeypatch.setattr(reader, "read_session", lambda _session_id: {
        "id": "claude-session",
        "tool": {"name": "claude-code", "session_id": "claude-session"},
        "agent": {"name": "claude-sonnet"},
        "entries": [{"type": "user-query", "text": "Inspect this repository"}],
    })
    output = reader.export_session("claude-session", str(tmp_path / "exports"))
    assert output is not None
    assert output.endswith("claude-code-claude-session.agentson")
    events = [json.loads(line) for line in open(output, encoding="utf-8") if line.strip()]
    assert events[0]["type"] == "stream-meta"
    assert events[0]["schema_version"] == "1.2"
    assert events[0]["source_session"]["tool"] == "claude-code"
    assert events[1]["type"] == "user-query"
    validate_v1_2_events(events)
