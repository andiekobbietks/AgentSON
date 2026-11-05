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
    assert "pytest -q" in packet
    assert "2 tests failed" in packet
    assert "untrusted historical data" in packet
    assert "does not restore private runtime state" in packet
    assert "Do not replay historical commands" in packet


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
    assert "new OpenCode session" in output.read_text(encoding="utf-8")
    assert "Continuation packet created" in capsys.readouterr().out
