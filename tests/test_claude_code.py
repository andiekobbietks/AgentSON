"""Tests for Claude Code reader."""
import json
import os
import tempfile
import pytest
from pathlib import Path
from readers.claude_code import ClaudeCodeReader


@pytest.fixture
def claude_dir(tmp_path):
    """Create a temporary Claude Code directory structure."""
    projects_dir = tmp_path / "projects"
    project_hash = "test-project-hash"
    project_dir = projects_dir / project_hash
    project_dir.mkdir(parents=True)

    # Create sessions-index.json
    index = {
        "version": 1,
        "entries": [
            {
                "sessionId": "test-session-001",
                "fullPath": str(project_dir / "test-session-001.jsonl"),
                "firstPrompt": "Fix the auth bug",
                "summary": "Fixed authentication issue",
                "customTitle": None,
                "messageCount": 5,
                "created": "2026-07-05T10:00:00.000Z",
                "modified": "2026-07-05T10:05:00.000Z",
                "gitBranch": "main",
                "projectPath": "/Users/test/project",
                "isSidechain": False,
                "fileMtime": 1769006749607,
            }
        ],
    }
    with open(project_dir / "sessions-index.json", "w") as f:
        json.dump(index, f)

    # Create a JSONL session file
    jsonl_entries = [
        {
            "type": "user",
            "timestamp": "2026-07-05T10:00:00.000Z",
            "sessionId": "test-session-001",
            "message": {
                "role": "user",
                "content": [{"type": "text", "text": "Fix the auth bug in login.py"}],
            },
        },
        {
            "type": "assistant",
            "timestamp": "2026-07-05T10:00:01.000Z",
            "sessionId": "test-session-001",
            "message": {
                "role": "assistant",
                "model": "claude-sonnet-4-20250514",
                "content": [
                    {"type": "text", "text": "I'll look at the auth module."},
                    {
                        "type": "tool_use",
                        "id": "toolu_001",
                        "name": "Read",
                        "input": {"file_path": "src/auth.py"},
                    },
                ],
            },
        },
        {
            "type": "tool_result",
            "timestamp": "2026-07-05T10:00:02.000Z",
            "sessionId": "test-session-001",
            "tool_use_id": "toolu_001",
            "content": "def authenticate(user, password):\n    if user is None:\n        return False",
        },
        {
            "type": "assistant",
            "timestamp": "2026-07-05T10:00:03.000Z",
            "sessionId": "test-session-001",
            "message": {
                "role": "assistant",
                "model": "claude-sonnet-4-20250514",
                "content": [
                    {
                        "type": "tool_use",
                        "id": "toolu_002",
                        "name": "Edit",
                        "input": {
                            "file_path": "src/auth.py",
                            "old_string": "if user is None:",
                            "new_string": "if user is None or user == '':",
                        },
                    },
                ],
            },
        },
        {
            "type": "assistant",
            "timestamp": "2026-07-05T10:00:04.000Z",
            "sessionId": "test-session-001",
            "message": {
                "role": "assistant",
                "model": "claude-sonnet-4-20250514",
                "content": [
                    {"type": "text", "text": "Fixed the null check in auth.py"}
                ],
            },
        },
        {
            "type": "summary",
            "timestamp": "2026-07-05T10:00:05.000Z",
            "sessionId": "test-session-001",
            "summary": "Fixed the authentication issue by updating the null check.",
        },
    ]

    with open(project_dir / "test-session-001.jsonl", "w") as f:
        for entry in jsonl_entries:
            f.write(json.dumps(entry) + "\n")

    return tmp_path


def test_list_sessions(claude_dir):
    """Test listing sessions from Claude Code directory."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    sessions = reader.list_sessions()

    assert len(sessions) == 1
    assert sessions[0]["sessionId"] == "test-session-001"
    assert sessions[0]["project_hash"] == "test-project-hash"


def test_read_session(claude_dir):
    """Test reading a single session."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    session = reader.read_session("test-session-001")

    assert session is not None
    assert session["id"] == "claude-code-test-session-001"
    assert session["tool"]["name"] == "claude-code"
    assert session["agent"]["provider"] == "anthropic"
    assert session["agent"]["name"] == "claude-sonnet-4-20250514"
    assert session["task"] == "Fix the auth bug in login.py"
    assert session["outcome"] == "success"


def test_session_entries(claude_dir):
    """Test that entries are correctly converted."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    session = reader.read_session("test-session-001")

    entries = session["entries"]
    types = [e["type"] for e in entries]

    assert "user-query" in types
    assert "thought" in types
    assert "action" in types
    assert "observation" in types

    # Check user query
    user_queries = [e for e in entries if e["type"] == "user-query"]
    assert len(user_queries) == 1
    assert "auth bug" in user_queries[0]["text"]

    # Check actions
    actions = [e for e in entries if e["type"] == "action"]
    assert len(actions) == 2
    assert actions[0]["tool"] == "file_read"
    assert actions[0]["tool_call_id"] == "toolu_001"
    assert actions[1]["tool"] == "file_edit"

    # Check observation
    observations = [e for e in entries if e["type"] == "observation"]
    assert len(observations) == 1
    assert observations[0]["correlation_id"] == "toolu_001"


def test_export_session(claude_dir, tmp_path):
    """Test exporting a session to .agentson file."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    output_dir = str(tmp_path / "output")
    result = reader.export_session("test-session-001", output_dir)

    assert result is not None
    assert os.path.exists(result)
    assert result.endswith(".agentson")

    with open(result) as f:
        data = json.load(f)
    assert data["tool"]["name"] == "claude-code"


def test_read_nonexistent_session(claude_dir):
    """Test reading a session that doesn't exist."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    session = reader.read_session("nonexistent-session")
    assert session is None


def test_tool_mapping(claude_dir):
    """Test that Claude Code tools are mapped to AgentSON tools."""
    reader = ClaudeCodeReader(config_dir=str(claude_dir))
    session = reader.read_session("test-session-001")

    actions = [e for e in session["entries"] if e["type"] == "action"]
    tool_names = [a["tool"] for a in actions]

    assert "file_read" in tool_names
    assert "file_edit" in tool_names
