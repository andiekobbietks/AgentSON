"""Tests for the Cline reader."""
from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.cline import (
    _api_messages_to_entries,
    _extract_provider,
    _load_json,
    list_sessions,
    read_session,
)


def _make_test_task(tmp_dir: Path) -> Path:
    """Create a minimal Cline task directory with test data."""
    task_dir = tmp_dir / "01HXyz123abc"
    task_dir.mkdir(parents=True, exist_ok=True)

    # history_item.json
    history = {
        "id": "01HXyz123abc",
        "ts": 1720000000000,
        "task": "Implement user authentication",
        "tokensIn": 5000,
        "tokensOut": 2000,
        "modelId": "claude-sonnet-4-20250514",
        "mode": "act",
        "status": "completed",
        "cwdOnTaskInitialization": "/Users/dev/myproject",
    }
    (task_dir / "history_item.json").write_text(json.dumps(history), encoding="utf-8")

    # api_conversation_history.json
    api_messages = [
        {
            "id": "msg-1",
            "role": "user",
            "content": [
                {"type": "text", "text": "Implement user authentication with JWT"},
            ],
            "ts": 1720000000000,
        },
        {
            "id": "msg-2",
            "role": "assistant",
            "content": [
                {"type": "thinking", "thinking": "I need to create auth middleware..."},
                {"type": "text", "text": "I'll create the auth module with JWT support."},
                {
                    "type": "tool_use",
                    "id": "tool-1",
                    "name": "write_to_file",
                    "input": {"path": "src/auth.py", "content": "import jwt\n..."},
                },
            ],
            "ts": 1720000030000,
        },
        {
            "id": "msg-3",
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "tool-1",
                    "content": "File written successfully",
                    "is_error": False,
                },
            ],
            "ts": 1720000035000,
        },
        {
            "id": "msg-4",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Done. Created src/auth.py with JWT authentication."},
            ],
            "ts": 1720000050000,
        },
    ]
    (task_dir / "api_conversation_history.json").write_text(
        json.dumps(api_messages), encoding="utf-8"
    )

    # task_metadata.json
    metadata = {
        "model_usage": [
            {"modelId": "claude-sonnet-4-20250514", "tokensIn": 5000, "tokensOut": 2000}
        ],
        "files_in_context": [
            {"path": "src/auth.py", "lastKnownHash": "abc123"}
        ],
    }
    (task_dir / "task_metadata.json").write_text(json.dumps(metadata), encoding="utf-8")

    return tmp_dir


class TestClineReader(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        _make_test_task(self.tmp_dir)

    def test_list_sessions(self):
        sessions = list_sessions(str(self.tmp_dir))
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["id"], "01HXyz123abc")
        self.assertEqual(sessions[0]["title"], "Implement user authentication")
        self.assertEqual(sessions[0]["model"], "claude-sonnet-4-20250514")

    def test_read_session_structure(self):
        doc = read_session(str(self.tmp_dir), "01HXyz123abc")
        self.assertEqual(doc["$schema"], "https://agentson.dev/schema/v1.1.json")
        self.assertEqual(doc["tool"]["name"], "cline")
        self.assertEqual(doc["tool"]["session_id"], "01HXyz123abc")

    def test_read_session_entries(self):
        doc = read_session(str(self.tmp_dir), "01HXyz123abc")
        entries = doc["entries"]
        types = [e["type"] for e in entries]
        self.assertIn("user-query", types)
        self.assertIn("thought", types)
        self.assertIn("action", types)
        self.assertIn("observation", types)
        self.assertIn("answer", types)

    def test_read_session_trajectory(self):
        doc = read_session(str(self.tmp_dir), "01HXyz123abc")
        self.assertIn("auth", doc["task"].lower())
        self.assertEqual(doc["outcome"], "success")

    def test_read_session_agent(self):
        doc = read_session(str(self.tmp_dir), "01HXyz123abc")
        self.assertEqual(doc["agent"]["name"], "claude-sonnet-4-20250514")
        self.assertEqual(doc["agent"]["provider"], "anthropic")

    def test_read_session_metadata(self):
        doc = read_session(str(self.tmp_dir), "01HXyz123abc")
        self.assertEqual(doc["metadata"]["total_tokens_in"], 5000)
        self.assertEqual(doc["metadata"]["total_tokens_out"], 2000)
        self.assertEqual(doc["metadata"]["files_in_context"], 1)

    def test_read_nonexistent_task(self):
        with self.assertRaises(FileNotFoundError):
            read_session(str(self.tmp_dir), "nonexistent")

    def test_api_messages_to_entries(self):
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "Hello"}], "ts": 100},
            {"role": "assistant", "content": [{"type": "text", "text": "Hi there"}], "ts": 200},
        ]
        entries = _api_messages_to_entries(messages)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["type"], "user-query")
        self.assertEqual(entries[0]["text"], "Hello")
        self.assertEqual(entries[1]["type"], "answer")
        self.assertEqual(entries[1]["text"], "Hi there")

    def test_extract_provider(self):
        self.assertEqual(_extract_provider("claude-sonnet-4-20250514"), "anthropic")
        self.assertEqual(_extract_provider("gpt-4o"), "openai")
        self.assertEqual(_extract_provider("gemini-2.0-flash"), "google")
        self.assertEqual(_extract_provider("unknown-model"), "unknown")


if __name__ == "__main__":
    unittest.main()
