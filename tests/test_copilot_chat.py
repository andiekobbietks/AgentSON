"""
Unit tests for GitHub Copilot Chat reader.
"""

import json
import pytest
from pathlib import Path
from datetime import datetime
from readers.copilot_chat import CopilotChatReader


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


def test_export_session_sanitizes_path_traversal_attempt(tmp_path):
    """
    Regression test for a real path traversal vulnerability: a crafted
    session_id like "../../etc/passwd" used to resolve the export
    filename outside the intended output directory entirely. Confirmed
    with a direct pathlib reproduction before the fix landed.
    """
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    output_dir = tmp_path / "safe_output"

    evil_id = "../../../tmp/agentson_escape_proof"
    history_file = history_dir / "history.jsonl"
    entries = [
        {"type": "user", "content": "hi", "sessionId": evil_id, "timestamp": "2026-01-01T00:00:00Z"},
        {"type": "assistant", "content": "hello", "model": "gpt-4", "sessionId": evil_id, "timestamp": "2026-01-01T00:00:01Z"},
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    reader = CopilotChatReader(str(history_dir))
    result_path = reader.export_session(evil_id, str(output_dir))

    assert result_path is not None
    resolved = Path(result_path).resolve()
    assert str(resolved).startswith(str(output_dir.resolve())), (
        f"Export escaped the intended output directory: {resolved}"
    )


def test_agent_provider_reflects_actual_model_used(tmp_path):
    """
    Regression test: agent.name/provider used to be hardcoded to
    "gpt-4"/"openai" regardless of which model actually answered.
    Copilot Chat can be backed by Claude, Gemini, etc. -- an entry
    answered by claude-3.5-sonnet must not be reported as gpt-4/openai.
    """
    history_dir = tmp_path / "history"
    history_dir.mkdir()
    history_file = history_dir / "history.jsonl"
    entries = [
        {"type": "user", "content": "hi", "sessionId": "s1", "timestamp": "2026-01-01T00:00:00Z"},
        {"type": "assistant", "content": "hello", "model": "claude-3.5-sonnet", "sessionId": "s1", "timestamp": "2026-01-01T00:00:01Z"},
    ]
    with open(history_file, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")

    reader = CopilotChatReader(str(history_dir))
    session = reader.read_session("s1")

    assert session["agent"]["name"] == "claude-3.5-sonnet"
    assert session["agent"]["provider"] == "anthropic"
