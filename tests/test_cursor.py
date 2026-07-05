"""Tests for the Cursor reader."""
from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.cursor import (
    _bubbles_to_entries,
    _load_json_value,
    _ms_to_iso,
    _extract_model_name,
    list_sessions,
    read_session,
)


def _make_test_db(tmp_dir: Path) -> Path:
    """Create a minimal Cursor state.vscdb with test data."""
    db_path = tmp_dir / "state.vscdb"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE cursorDiskKV (
            key TEXT UNIQUE,
            value BLOB
        )
    """)

    # Session header
    header = {
        "composerId": "test-composer-001",
        "name": "Fix authentication bug",
        "createdAt": 1720000000000,
        "lastUpdatedAt": 1720000060000,
        "status": "completed",
        "unifiedMode": "agent",
        "fullConversationHeadersOnly": [
            {"bubbleId": "bub-1", "type": 1},
            {"bubbleId": "bub-2", "type": 2},
            {"bubbleId": "bub-3", "type": 1},
            {"bubbleId": "bub-4", "type": 2},
        ],
        "usageData": {"default": {"costInCents": 12, "amount": 3}},
    }
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("composerData:test-composer-001", json.dumps(header)),
    )

    # User bubble
    user_bubble = {
        "_v": 3,
        "type": 1,
        "bubbleId": "bub-1",
        "text": "Fix the auth bug in login.py",
        "createdAt": 1720000000000,
    }
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("bubbleId:test-composer-001:bub-1", json.dumps(user_bubble)),
    )

    # Assistant bubble with thinking + tool result
    assistant_bubble = {
        "_v": 3,
        "type": 2,
        "bubbleId": "bub-2",
        "text": "I found the bug. The null check was missing.",
        "createdAt": 1720000030000,
        "modelInfo": {"modelName": "claude-sonnet-4-5"},
        "thinking": {"text": "The user wants me to fix an auth bug. Let me look at login.py."},
        "toolResults": [
            {
                "toolName": "read_file",
                "params": '{"targetFile": "login.py"}',
                "result": "def login(user): ...",
                "status": "completed",
            }
        ],
    }
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("bubbleId:test-composer-001:bub-2", json.dumps(assistant_bubble)),
    )

    # Second user message
    user_bubble2 = {
        "_v": 3,
        "type": 1,
        "bubbleId": "bub-3",
        "text": "Now add tests",
        "createdAt": 1720000040000,
    }
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("bubbleId:test-composer-001:bub-3", json.dumps(user_bubble2)),
    )

    # Final assistant answer
    assistant_bubble2 = {
        "_v": 3,
        "type": 2,
        "bubbleId": "bub-4",
        "text": "Done. Added test_login.py with 3 test cases.",
        "createdAt": 1720000055000,
        "modelInfo": {"modelName": "claude-sonnet-4-5"},
    }
    conn.execute(
        "INSERT INTO cursorDiskKV (key, value) VALUES (?, ?)",
        ("bubbleId:test-composer-001:bub-4", json.dumps(assistant_bubble2)),
    )

    conn.commit()
    conn.close()
    return db_path


class TestCursorReader(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        self.db_path = _make_test_db(self.tmp_dir)

    def test_list_sessions(self):
        sessions = list_sessions(str(self.db_path))
        self.assertEqual(len(sessions), 1)
        self.assertEqual(sessions[0]["id"], "test-composer-001")
        self.assertEqual(sessions[0]["title"], "Fix authentication bug")
        self.assertEqual(sessions[0]["mode"], "agent")

    def test_read_session_structure(self):
        doc = read_session(str(self.db_path), "test-composer-001")
        self.assertEqual(doc["$schema"], "https://agentson.dev/schema/v1.1.json")
        self.assertEqual(doc["tool"]["name"], "cursor")
        self.assertEqual(doc["tool"]["session_id"], "test-composer-001")
        self.assertEqual(doc["id"], "test-composer-001")

    def test_read_session_entries(self):
        doc = read_session(str(self.db_path), "test-composer-001")
        entries = doc["entries"]
        # 2 user-queries, 1 thought, 1 action, 1 answer
        types = [e["type"] for e in entries]
        self.assertIn("user-query", types)
        self.assertIn("thought", types)
        self.assertIn("action", types)
        self.assertIn("answer", types)

    def test_read_session_trajectory(self):
        doc = read_session(str(self.db_path), "test-composer-001")
        self.assertIn("auth", doc["task"].lower())
        self.assertIn(doc["outcome"], {"success", "partial", "aborted"})

    def test_read_session_model(self):
        doc = read_session(str(self.db_path), "test-composer-001")
        self.assertIn("claude", doc["agent"]["name"].lower())

    def test_read_session_timestamps(self):
        doc = read_session(str(self.db_path), "test-composer-001")
        self.assertIn("started_at", doc)
        self.assertIn("ended_at", doc)

    def test_read_nonexistent_session(self):
        with self.assertRaises(ValueError):
            read_session(str(self.db_path), "nonexistent")

    def test_ms_to_iso(self):
        result = _ms_to_iso(1720000000000)
        self.assertIn("2024", result)
        self.assertTrue(result.endswith("Z"))

    def test_load_json_value(self):
        data = _load_json_value('{"key": "value"}')
        self.assertEqual(data["key"], "value")
        self.assertIsNone(_load_json_value(None))
        self.assertIsNone(_load_json_value("invalid json"))

    def test_extract_model_name(self):
        bubbles = [{"type": 2, "modelInfo": {"modelName": "gpt-4o"}}]
        self.assertEqual(_extract_model_name(bubbles), "gpt-4o")
        self.assertEqual(_extract_model_name([]), "unknown")


if __name__ == "__main__":
    unittest.main()
