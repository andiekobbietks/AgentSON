"""Tests for portable cross-harness continuation packets."""
import json

from exporters.jsonl import write_agentson_stream
from importers.continuation import build_continuation_packet, write_continuation_packet


def test_packet_preserves_context_and_marks_historical_commands_inert(tmp_path):
    source = tmp_path / "session.agentson"
    session = {
        "id": "session-001",
        "tool": {"name": "opencode", "session_id": "native-001"},
        "agent": {"name": "assistant"},
        "entries": [
            {"type": "user-query", "text": "Fix the failing tests"},
            {
                "type": "action",
                "tool": "shell.run",
                "args": {"command": "pytest -q"},
                "tool_call_id": "call-1",
            },
            {"type": "observation", "source": "tool", "text": "2 tests failed"},
            {"type": "answer", "text": "The failing tests are in the importer."},
        ],
    }
    with source.open("w", encoding="utf-8") as handle:
        write_agentson_stream(session, handle, source_tool="opencode")

    packet = build_continuation_packet(str(source), target="claude-code")
    assert "new Claude Code session" in packet
    assert "Fix the failing tests" in packet
    assert "shell.run" in packet
    assert '- args:' not in packet
    assert '"command": "pytest -q"' not in packet
    assert "2 tests failed" in packet
    assert "untrusted historical data" in packet
    assert "does not restore private runtime state" in packet
    assert "do not replay historical commands" in packet


def test_packet_writer_creates_parent_directory_and_utf8_file(tmp_path):
    source = tmp_path / "legacy.agentson"
    source.write_text(json.dumps({
        "id": "legacy-session",
        "tool": {"name": "chatgpt", "session_id": "native-chat"},
        "entries": [{"type": "answer", "text": "Café context"}],
    }), encoding="utf-8")
    destination = tmp_path / "nested" / "resume.md"

    result = write_continuation_packet(str(source), str(destination), target="generic")

    assert result == str(destination)
    assert destination.exists()
    assert "Café context" in destination.read_text(encoding="utf-8")


def test_packet_rejects_non_list_entries(tmp_path):
    source = tmp_path / "bad.agentson"
    source.write_text(json.dumps({"id": "bad", "entries": "not-a-list"}), encoding="utf-8")
    try:
        build_continuation_packet(str(source))
    except ValueError as exc:
        assert "entries must be a list" in str(exc)
    else:
        raise AssertionError("Expected malformed session to be rejected")


def test_public_cli_resume_command_creates_packet(tmp_path, monkeypatch, capsys):
    import sys
    from cli.main import main

    source = tmp_path / "cli-session.agentson"
    source.write_text(json.dumps({
        "id": "cli-session",
        "tool": {"name": "chatgpt", "session_id": "native-cli"},
        "entries": [{"type": "user-query", "text": "Continue this task"}],
    }), encoding="utf-8")
    output = tmp_path / "cli-resume.md"
    monkeypatch.setattr(sys, "argv", [
        "agentson", "resume", str(source), "--target", "opencode",
        "--output", str(output),
    ])

    main()

    assert output.exists()
    assert "Continue this task" in output.read_text(encoding="utf-8")
    assert "new Opencode session" in output.read_text(encoding="utf-8")
    assert "Continuation packet created" in capsys.readouterr().out


def test_packet_rejects_non_object_event_with_position(tmp_path):
    source = tmp_path / "malformed.agentson"
    source.write_text(json.dumps({
        "id": "malformed",
        "entries": [{"type": "user-query", "text": "hello"}, "not-an-event"],
    }), encoding="utf-8")
    try:
        build_continuation_packet(str(source))
    except ValueError as exc:
        assert "position 1" in str(exc)
    else:
        raise AssertionError("Expected malformed event to be rejected")


def test_packet_redacts_credentials_and_renders_handoff_side_effect_fields(tmp_path):
    source = tmp_path / "sensitive.agentson"
    source.write_text(json.dumps({
        "id": "sensitive",
        "tool": {"name": "fixture"},
        "entries": [
            {"type": "user-query", "text": "Use token ghp_abcdefghijklmnopqrstuvwxyz1234567890"},
            {"type": "handoff", "from": "planner", "to": "builder", "conch": "build"},
            {"type": "side-effect", "action": "file_write", "path": "/private/report.txt"},
        ],
    }), encoding="utf-8")
    packet = build_continuation_packet(str(source))
    assert "ghp_abcdefghijklmnopqrstuvwxyz1234567890" not in packet
    assert "[SECRET]" in packet
    assert "- from: planner" in packet
    assert "- to: builder" in packet
    assert "- conch: build" in packet
    assert "- action: file_write" in packet
    assert "- path: /private/report.txt" in packet
