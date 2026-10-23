"""Tests for the Aider reader."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.aider import (
    _split_sessions,
    _parse_session_body,
    _parse_timestamp,
    _infer_tool,
    list_sessions,
    read_session,
)


SAMPLE_CHAT_HISTORY = """# Chat History

## [2026-07-01 10:30:00]

### User

Fix the null pointer exception in auth.py

### Assistant

I found the issue. The `user` variable wasn't being checked before access.

```python
def login(user):
    if user is None:
        return redirect("/login")
    return generate_token(user)
```

The fix adds a None check before accessing `user.id`.

### User

Now add a test for this

### Assistant

```python
def test_login_none_user():
    result = login(None)
    assert result.status_code == 302
```

Done. Added test_login_none_user to test_auth.py.

## [2026-07-01 11:00:00]

### User

/refactor src/utils.py to use pathlib

### Assistant

Ok, I will refactor utils.py to use pathlib instead of os.path.

```python
from pathlib import Path

def get_config_path():
    return Path.home() / ".config" / "myapp" / "config.json"
```

Refactored 3 functions to use pathlib.
"""


class TestAiderReader(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = Path(tempfile.mkdtemp())
        aider_file = self.tmp_dir / ".aider.chat.history.md"
        aider_file.write_text(SAMPLE_CHAT_HISTORY, encoding="utf-8")

    def test_list_sessions(self):
        sessions = list_sessions(str(self.tmp_dir))
        self.assertEqual(len(sessions), 2)
        self.assertIn("auth", sessions[0]["title"].lower())
        self.assertIn("refactor", sessions[1]["title"].lower())

    def test_read_session_structure(self):
        doc = read_session(str(self.tmp_dir))
        self.assertEqual(doc["$schema"], "https://agentson.dev/schema/v1.1.json")
        self.assertEqual(doc["tool"]["name"], "aider")
        self.assertIn("aider-", doc["id"])

    def test_read_session_entries(self):
        doc = read_session(str(self.tmp_dir))
        entries = doc["entries"]
        types = [e["type"] for e in entries]
        self.assertIn("user-query", types)
        self.assertIn("action", types)
        self.assertIn("answer", types)

    def test_read_session_trajectory(self):
        doc = read_session(str(self.tmp_dir))
        self.assertIn("task", doc)
        self.assertIn(doc["outcome"], {"success", "partial", "aborted"})

    def test_read_specific_session(self):
        sessions = list_sessions(str(self.tmp_dir))
        session_id = sessions[0]["id"]
        doc = read_session(str(self.tmp_dir), session_id)
        self.assertEqual(doc["id"], session_id)

    def test_split_sessions(self):
        sessions = _split_sessions(SAMPLE_CHAT_HISTORY)
        self.assertEqual(len(sessions), 2)
        self.assertIn("2026-07-01 10:30:00", sessions[0][0])
        self.assertIn("2026-07-01 11:00:00", sessions[1][0])

    def test_parse_session_body(self):
        _, body = _split_sessions(SAMPLE_CHAT_HISTORY)[0]
        entries = _parse_session_body(body)
        self.assertGreater(len(entries), 0)
        types = [e["type"] for e in entries]
        self.assertIn("user-query", types)

    def test_parse_timestamp(self):
        dt = _parse_timestamp("2026-07-01 10:30:00")
        self.assertIsNotNone(dt)
        self.assertEqual(dt.year, 2026)
        self.assertEqual(dt.month, 7)
        self.assertEqual(dt.day, 1)

    def test_infer_tool(self):
        self.assertEqual(_infer_tool("import os"), "code_edit")
        self.assertEqual(_infer_tool("git status"), "bash")
        self.assertEqual(_infer_tool("npm install"), "bash")
        self.assertEqual(_infer_tool("def hello():"), "code_edit")

    def test_diff_parsing(self):
        diff_text = """Some code:

<<<<<<< SEARCH
old code here
=======
new code here
>>>>>>> REPLACE

Done."""
        entries = _parse_session_body(f"### Assistant\n\n{diff_text}")
        actions = [e for e in entries if e["type"] == "action"]
        self.assertGreater(len(actions), 0)
        self.assertIn("SEARCH", actions[0]["code"])


if __name__ == "__main__":
    unittest.main()
