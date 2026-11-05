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
