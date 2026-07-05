"""
Unit tests for GitHub Copilot Chat reader.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from readers.copilot_chat import (
    CopilotChatReader,
    read as copilot_chat_read,
    list_sessions as copilot_chat_list_sessions,
)


@pytest.fixture
def sample_history(tmp_path):
    """Create a sample history.jsonl file for testing."""
    history_file = tmp_path / "history.jsonl"
    entries = [
        {
            "type": "user",
            "content": "How do I implement JWT authentication?",
            "sessionId": "session-001",
            "timestamp": "2026-07-05T10:00:00Z",
        },
        {
            "type": "assistant",
            "content": "JWT (JSON Web Tokens) authentication involves three parts: header, payload, and signature.",
            "model": "gpt-4",
            "sessionId": "session-001",
            "timestamp": "2026-07-05T10:00:05Z",
        },
        {
            "type": "code",
            "language": "python",
            "snippet": "import jwt\ntoken = jwt.encode({'user_id': 123}, 'secret', algorithm='HS256')",
            "filePath": "auth.py",
            "sessionId": "session-001",
            "timestamp": "2026-07-05T10:00:10Z",
        },
        {
            "type": "user",
            "content": "Can you explain the payload?",
            "sessionId": "session-001",
            "timestamp": "2026-07-05T10:00:15Z",
        },
        {
            "type": "assistant",
            "content": "The payload contains the claims—data you want to transmit. Common claims are user_id, exp (expiry), and iat (issued at).",
            "model": "gpt-4",
            "sessionId": "session-001",
            "timestamp": "2026-07-05T10:00:20Z",
        },
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")
    return str(tmp_path)


def test_list_sessions(sample_history):
    """Test listing Copilot chat sessions."""
    reader = CopilotChatReader(sample_history)
    sessions = reader.list_sessions(limit=10)

    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "session-001"
    assert sessions[0]["messageCount"] == 5


def test_read_session(sample_history):
    """Test reading a full Copilot chat session."""
    reader = CopilotChatReader(sample_history)
    session = reader.read_session("session-001")

    assert session is not None
    assert session["id"] == "copilot-chat-session-001"
    assert session["tool"]["name"] == "copilot-chat"
    assert session["agent"]["name"] == "gpt-4"
    assert session["task"] == "How do I implement JWT authentication?"
    assert session["outcome"] == "success"


def test_entry_types(sample_history):
    """Test that entries are correctly typed."""
    reader = CopilotChatReader(sample_history)
    session = reader.read_session("session-001")
    entries = session["entries"]

    # Should have: user-query, answer, action, user-query, answer
    assert entries[0]["type"] == "user-query"
    assert entries[0]["text"] == "How do I implement JWT authentication?"

    assert entries[1]["type"] == "answer"
    assert "JWT" in entries[1]["text"]

    assert entries[2]["type"] == "action"
    assert entries[2]["tool"] == "code-python"
    assert "jwt.encode" in entries[2]["code"]
    assert entries[2]["path"] == "auth.py"

    assert entries[3]["type"] == "user-query"
    assert entries[4]["type"] == "answer"


def test_schema_compliance(sample_history):
    """Test that output conforms to AgentSON v1.1 schema."""
    reader = CopilotChatReader(sample_history)
    session = reader.read_session("session-001")

    # Required fields
    assert "$schema" in session
    assert session["$schema"] == "https://agentson.dev/schema/v1.1.json"
    assert "id" in session
    assert "tool" in session
    assert "entries" in session

    # Tool shape
    assert session["tool"]["name"] == "copilot-chat"
    assert "session_id" in session["tool"]

    # Agent shape
    assert "name" in session["agent"]
    assert "provider" in session["agent"]

    # Timestamps
    assert session["started_at"] is not None
    assert session["ended_at"] is not None


def test_empty_session(tmp_path):
    """Test handling of non-existent session."""
    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("nonexistent")
    assert session is None


def test_export_session(sample_history, tmp_path):
    """Test exporting a session to .agentson file."""
    reader = CopilotChatReader(sample_history)
    output_file = reader.export_session("session-001", str(tmp_path))

    assert output_file is not None
    assert Path(output_file).exists()
    assert output_file.endswith(".agentson")

    # Verify file contents
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["id"] == "copilot-chat-session-001"
    assert len(data["entries"]) == 5


def test_export_session_nonexistent_returns_none(tmp_path):
    """export_session should return None (and create nothing) for a missing session."""
    reader = CopilotChatReader(str(tmp_path))
    output_dir = tmp_path / "output"
    result = reader.export_session("nonexistent", str(output_dir))

    assert result is None
    assert not output_dir.exists()


def test_module_level_read_and_list_sessions(sample_history):
    """Test the module-level convenience functions `read` and `list_sessions`."""
    sessions = copilot_chat_list_sessions(sample_history, limit=10)
    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "session-001"

    session = copilot_chat_read("session-001", sample_history)
    assert session is not None
    assert session["id"] == "copilot-chat-session-001"


def test_module_level_read_missing_session(tmp_path):
    """The module-level `read` helper should return None for missing sessions."""
    assert copilot_chat_read("nonexistent", str(tmp_path)) is None


def test_multiple_sessions_ordering_and_limit(tmp_path):
    """Sessions should be listed most-recent-first and the limit should be respected."""
    history_file = tmp_path / "history.jsonl"
    entries = [
        {
            "type": "user",
            "content": "first session msg",
            "sessionId": "s1",
            "timestamp": "2026-07-01T00:00:00Z",
        },
        {
            "type": "user",
            "content": "second session msg",
            "sessionId": "s2",
            "timestamp": "2026-07-02T00:00:00Z",
        },
        {
            "type": "user",
            "content": "third session msg",
            "sessionId": "s3",
            "timestamp": "2026-07-03T00:00:00Z",
        },
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    sessions = reader.list_sessions(limit=10)
    assert [s["sessionId"] for s in sessions] == ["s3", "s2", "s1"]

    limited = reader.list_sessions(limit=2)
    assert [s["sessionId"] for s in limited] == ["s3", "s2"]


def test_list_sessions_missing_history_file(tmp_path):
    """list_sessions should return an empty list when history.jsonl doesn't exist."""
    reader = CopilotChatReader(str(tmp_path))
    assert reader.list_sessions() == []


def test_list_sessions_skips_malformed_lines(tmp_path):
    """Malformed JSON lines and blank lines in history.jsonl should be skipped."""
    history_file = tmp_path / "history.jsonl"
    with open(history_file, "w", encoding="utf-8") as f:
        f.write("{not valid json\n")
        f.write("\n")
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "content": "hi",
                    "sessionId": "s1",
                    "timestamp": "2026-07-05T00:00:00Z",
                }
            )
            + "\n"
        )

    reader = CopilotChatReader(str(tmp_path))
    sessions = reader.list_sessions()
    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "s1"


def test_read_session_skips_malformed_lines_and_other_sessions(tmp_path):
    """read_session should ignore malformed lines and entries from other sessions."""
    history_file = tmp_path / "history.jsonl"
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "content": "other session",
                    "sessionId": "other",
                    "timestamp": "2026-07-05T00:00:00Z",
                }
            )
            + "\n"
        )
        f.write("{not valid json\n")
        f.write(
            json.dumps(
                {
                    "type": "user",
                    "content": "target session",
                    "sessionId": "target",
                    "timestamp": "2026-07-05T00:00:01Z",
                }
            )
            + "\n"
        )

    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("target")
    assert session is not None
    assert session["metadata"]["message_count"] == 1
    assert session["entries"][0]["text"] == "target session"


def test_thought_and_observation_entries(tmp_path):
    """`thought` and `observation` entry types should be converted correctly."""
    history_file = tmp_path / "history.jsonl"
    entries = [
        {
            "type": "thought",
            "content": "Let me consider the options.",
            "sessionId": "s1",
            "timestamp": "2026-07-05T00:00:00Z",
        },
        {
            "type": "observation",
            "content": "Tests passed.",
            "source": "test-runner",
            "correlation_id": "abc-123",
            "sessionId": "s1",
            "timestamp": "2026-07-05T00:00:01Z",
        },
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("s1")
    types = [e["type"] for e in session["entries"]]
    assert types == ["thought", "observation"]

    thought = session["entries"][0]
    assert thought["text"] == "Let me consider the options."

    observation = session["entries"][1]
    assert observation["text"] == "Tests passed."
    assert observation["source"] == "test-runner"
    assert observation["correlation_id"] == "abc-123"


def test_outcome_partial_without_assistant_entries(tmp_path):
    """Outcome should remain 'partial' when there is no assistant response."""
    history_file = tmp_path / "history.jsonl"
    entry = {
        "type": "user",
        "content": "Anyone there?",
        "sessionId": "s1",
        "timestamp": "2026-07-05T00:00:00Z",
    }
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("s1")
    assert session["outcome"] == "partial"


def test_task_truncated_to_200_chars(tmp_path):
    """The `task` field should be truncated to the first 200 characters of the first user message."""
    long_message = "x" * 300
    history_file = tmp_path / "history.jsonl"
    entry = {
        "type": "user",
        "content": long_message,
        "sessionId": "s1",
        "timestamp": "2026-07-05T00:00:00Z",
    }
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("s1")
    assert session["task"] == "x" * 200


def test_first_message_truncated_to_100_chars(tmp_path):
    """`firstMessage` in list_sessions output should be truncated to 100 characters."""
    long_message = "y" * 150
    history_file = tmp_path / "history.jsonl"
    entry = {
        "type": "user",
        "content": long_message,
        "sessionId": "s1",
        "timestamp": "2026-07-05T00:00:00Z",
    }
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    sessions = reader.list_sessions()
    assert sessions[0]["firstMessage"] == "y" * 100


def test_code_entry_without_language(tmp_path):
    """Code entries without a language should use the generic 'code' tool name."""
    history_file = tmp_path / "history.jsonl"
    entry = {
        "type": "code",
        "snippet": "echo hi",
        "filePath": "run.sh",
        "sessionId": "s1",
        "timestamp": "2026-07-05T00:00:00Z",
    }
    with open(history_file, "w", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

    reader = CopilotChatReader(str(tmp_path))
    session = reader.read_session("s1")
    action = session["entries"][0]
    assert action["type"] == "action"
    assert action["tool"] == "code"
    assert action["code"] == "echo hi"
    assert action["path"] == "run.sh"


def test_history_file_is_directory_handled_gracefully(tmp_path):
    """If history.jsonl can't be opened (e.g. it's a directory), reads should fail gracefully."""
    (tmp_path / "history.jsonl").mkdir()

    reader = CopilotChatReader(str(tmp_path))
    assert reader.list_sessions() == []
    assert reader.read_session("any-session") is None


def test_default_config_dir_uses_home(monkeypatch, tmp_path):
    """Without an explicit config_dir, the reader should default to ~/.copilot."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    reader = CopilotChatReader()
    assert reader.copilot_dir == tmp_path / ".copilot"


class TestTimestampToIso:
    """Tests for the CopilotChatReader._timestamp_to_iso static helper."""

    def test_none_returns_none(self):
        assert CopilotChatReader._timestamp_to_iso(None) is None

    def test_empty_string_returns_none(self):
        assert CopilotChatReader._timestamp_to_iso("") is None

    def test_already_iso_format_passthrough(self):
        ts = "2026-07-05T10:00:00Z"
        assert CopilotChatReader._timestamp_to_iso(ts) == ts

    def test_date_only_converted_to_iso(self):
        result = CopilotChatReader._timestamp_to_iso("2026-07-05")
        assert result == "2026-07-05T00:00:00Z"

    def test_unparseable_timestamp_returned_unchanged(self):
        assert CopilotChatReader._timestamp_to_iso("not-a-date") == "not-a-date"


def test_readers_init_exports_copilot_chat():
    """readers/__init__.py should expose the Copilot Chat reader and its helpers."""
    import readers

    assert readers.CopilotChatReader is CopilotChatReader
    assert readers.CopilotChat is CopilotChatReader
    assert readers.read_copilot_chat is copilot_chat_read
    assert readers.list_copilot_chat is copilot_chat_list_sessions
