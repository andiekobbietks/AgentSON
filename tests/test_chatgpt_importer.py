"""
Tests for importers/chatgpt.py.

No test file for this importer existed before this one, despite
CHANGELOG.md claiming it was "validated against a real export
including its edge cases (hidden system-injected profile data,
that had to be correctly excluded rather than leaked)." That claim
could not have reflected the code's actual state: the module had a
hard IndentationError (missing indent under a `with` block) that
made it fail to import at all, and a separate bug where
`node.get("message", {})` returned None instead of {} for ChatGPT's
root node (which has an explicit "message": null, not a missing
key), crashing `_detect_model` on any real export.

Both are fixed here. This test uses a minimal but structurally
faithful ChatGPT export shape (mapping tree with a null-message root
node, matching real exports) rather than skipping the root-node case.
"""
import json
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from importers.chatgpt import import_chatgpt


def _write_fixture(data: dict) -> str:
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def _minimal_export() -> dict:
    """
    A minimal but structurally real ChatGPT export: a mapping tree
    with a null-message root node (the exact shape that crashed
    _detect_model before the fix) followed by a user/assistant pair.
    """
    return {
        "title": "Test conversation",
        "create_time": 1783100000.0,
        "update_time": 1783100060.0,
        "mapping": {
            "root": {
                "id": "root",
                "message": None,
                "parent": None,
                "children": ["node-1"]
            },
            "node-1": {
                "id": "node-1",
                "message": {
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": ["Hello, what is 2+2?"]},
                    "create_time": 1783100000.0
                },
                "parent": "root",
                "children": ["node-2"]
            },
            "node-2": {
                "id": "node-2",
                "message": {
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": ["4"]},
                    "create_time": 1783100010.0,
                    "metadata": {"model_slug": "gpt-4o"}
                },
                "parent": "node-1",
                "children": []
            }
        }
    }


def test_import_does_not_crash_on_null_root_message():
    """The exact bug: root node has message: null, not a missing key."""
    path = _write_fixture(_minimal_export())
    try:
        result = import_chatgpt(path)
        assert result is not None
        print("PASS: test_import_does_not_crash_on_null_root_message")
    finally:
        os.unlink(path)


def test_import_extracts_user_and_assistant_entries():
    path = _write_fixture(_minimal_export())
    try:
        result = import_chatgpt(path)
        entry_types = [e["type"] for e in result["entries"]]
        assert "user-query" in entry_types
        assert "answer" in entry_types
        assert len(result["entries"]) == 2
        print("PASS: test_import_extracts_user_and_assistant_entries")
    finally:
        os.unlink(path)


def test_import_detects_model_from_metadata():
    path = _write_fixture(_minimal_export())
    try:
        result = import_chatgpt(path)
        assert result["agent"]["name"] == "gpt-4o"
        print("PASS: test_import_detects_model_from_metadata")
    finally:
        os.unlink(path)


def test_import_defaults_model_when_no_metadata_present():
    """Confirms the gpt-4 fallback still works when no model_slug exists anywhere."""
    data = _minimal_export()
    del data["mapping"]["node-2"]["message"]["metadata"]
    path = _write_fixture(data)
    try:
        result = import_chatgpt(path)
        assert result["agent"]["name"] == "gpt-4"
        print("PASS: test_import_defaults_model_when_no_metadata_present")
    finally:
        os.unlink(path)


def test_import_raises_on_empty_conversations():
    path = _write_fixture({"conversations": []})
    try:
        try:
            import_chatgpt(path)
            assert False, "Expected ValueError for empty conversations list"
        except ValueError:
            pass
        print("PASS: test_import_raises_on_empty_conversations")
    finally:
        os.unlink(path)


if __name__ == "__main__":
    test_import_does_not_crash_on_null_root_message()
    test_import_extracts_user_and_assistant_entries()
    test_import_detects_model_from_metadata()
    test_import_defaults_model_when_no_metadata_present()
    test_import_raises_on_empty_conversations()
    print("\nAll chatgpt importer tests passed!")
