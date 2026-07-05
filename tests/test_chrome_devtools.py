"""Tests for the Chrome DevTools AI reader.

Run from repo root:
    python -m pytest tests/test_chrome_devtools.py -v
or:
    python tests/test_chrome_devtools.py
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

# Make the readers package importable when running this file directly.
sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.chrome_devtools import parse_markdown, read, read_dir, list_exports


SAMPLE_MD = """# Exported Chat from Chrome DevTools AI Assistance

**Export Timestamp (UTC):** 2026-06-02T14:17:27.115Z

---

## User

download me through console this video

User attached an image

## AI

### Analyzing data

**Data used:**
* Element's uid is 4.
* Its selector is `video.video-stream.html5-main-video`

### Checking video source

Get the source URL of the video element to determine if it's a direct link.

**Code executed:**
```
const video = document.querySelector('video.video-stream.html5-main-video');
const data = { src: video ? video.src : null };
```

**Data returned:**
```
{"src":"blob:https://www.youtube.com/1c824f99-bdc5"}
```

### Answer

The video uses MSE streaming so direct console download is not possible.

## User

cool try anyway

## AI

### Capturing current video frame

Saving the current frame as an image workaround.

**Code executed:**
```
video.pause();
const canvas = document.createElement('canvas');
canvas.getContext('2d').drawImage(video, 0, 0);
canvas.toDataURL('image/png');
```

**Data returned:**
```
"data:image/png;base64,iVBORw0KG..."
```

### Answer

I saved the current frame for you. Direct video download requires browser extensions.
"""


class TestChromeDevtoolsReader(unittest.TestCase):

    def test_parses_user_query_with_attachment(self):
        doc = parse_markdown(SAMPLE_MD, source_filename="devtools_demo.md")
        self.assertEqual(doc["$schema"], "https://agentson.dev/schema/v1.1.json")
        self.assertEqual(doc["tool"]["name"], "chrome-devtools")
        self.assertEqual(doc["tool"]["session_id"], "demo-20260602")
        # Task + outcome populated from analysis
        self.assertIn("download me through console this video", doc["task"])
        self.assertIn(doc["outcome"], {"success", "partial", "aborted", "error"})
        # First user-query has the image attachment
        first = doc["entries"][0]
        self.assertEqual(first["type"], "user-query")
        self.assertIn("download me through console this video", first["text"])
        self.assertTrue(any(a.get("kind") == "image" for a in first.get("attachments", [])))

    def test_parses_context_data_used(self):
        doc = parse_markdown(SAMPLE_MD, source_filename="devtools_demo.md")
        contexts = [e for e in doc["entries"] if e["type"] == "context"]
        self.assertGreaterEqual(len(contexts), 1)
        c = contexts[0]
        self.assertIn("details", c)
        self.assertGreaterEqual(len(c["details"]), 2)
        # Check a detail element
        texts = [d.get("text", "") for d in c["details"]]
        self.assertTrue(any("uid is 4" in t for t in texts))

    def test_parses_action_with_code_and_output(self):
        doc = parse_markdown(SAMPLE_MD, source_filename="devtools_demo.md")
        actions = [e for e in doc["entries"] if e["type"] == "action"]
        self.assertGreaterEqual(len(actions), 2)
        # First action has code + output
        a1 = actions[0]
        self.assertIn("code", a1)
        self.assertIn("output", a1)
        self.assertIn("querySelector", a1["code"])
        self.assertIn("blob:", a1["output"])
        self.assertEqual(a1.get("tool"), "browser.evaluate")
        self.assertTrue(a1.get("tool_call_id", "").startswith("tc_"))

    def test_parses_answers_and_outcome(self):
        doc = parse_markdown(SAMPLE_MD)
        answers = [e for e in doc["entries"] if e["type"] == "answer"]
        self.assertEqual(len(answers), 2)
        self.assertIn("MSE streaming", answers[0]["text"])
        self.assertIn("current frame", answers[1]["text"])
        # Single-trajectory, last entry is an answer -> success
        self.assertEqual(doc["outcome"], "success")

    def test_metadata_includes_counts(self):
        doc = parse_markdown(SAMPLE_MD, source_filename="devtools_demo.md")
        m = doc.get("metadata", {})
        self.assertEqual(m.get("users"), 2)
        self.assertEqual(m.get("answers"), 2)
        self.assertEqual(m.get("source_filename"), "devtools_demo.md")

    def test_read_function_returns_agentson_doc(self):
        # Write the sample to a temp file and use read()
        import tempfile, os
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write(SAMPLE_MD)
            tmp = f.name
        try:
            doc = read(tmp)
            self.assertEqual(doc["tool"]["name"], "chrome-devtools")
            self.assertIn("download me through console", doc["task"])
        finally:
            os.unlink(tmp)

    def test_handles_minimal_session(self):
        minimal = """# Exported Chat from Chrome DevTools AI Assistance

**Export Timestamp (UTC):** 2026-07-01T00:00:00.000Z

---

## User

hi

## AI

### Answer

hello
"""
        doc = parse_markdown(minimal)
        self.assertEqual(len(doc["entries"]), 2)
        self.assertEqual(doc["outcome"], "success")

    def test_outcome_partial_when_unfinished(self):
        # Session with answers mid-stream but ends on a user-query (no final answer yet) -> partial
        multi = SAMPLE_MD + "\n## User\n\nand one more thing?"
        # No closing AI block + answer -> ends on a user-query
        doc = parse_markdown(multi)
        self.assertEqual(doc["outcome"], "partial")

    def test_outcome_aborted_when_no_answers(self):
        no_answer = """# Exported Chat from Chrome DevTools AI Assistance
**Export Timestamp (UTC):** 2026-07-01T00:00:00.000Z
---
## User

half a question
## AI

### Analyzing the prompt

Working on it...
"""
        doc = parse_markdown(no_answer)
        self.assertEqual(doc["outcome"], "aborted")


if __name__ == "__main__":
    unittest.main()