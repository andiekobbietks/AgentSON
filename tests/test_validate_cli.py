"""Regression tests for the AgentSON validation CLI."""
import json
from argparse import Namespace

import pytest

from cli.main import cmd_validate


def write(path, content):
    path.write_text(content, encoding="utf-8")
    return path


def test_validate_single_line_jsonl_stream(tmp_path):
    event = {
        "type": "stream-meta",
        "stream_id": "session-001",
        "mode": "single",
        "agents": [{"id": "assistant"}],
    }
    source = write(tmp_path / "one-line.agentson", json.dumps(event))
    cmd_validate(Namespace(input=str(source)))


def test_validate_multiline_jsonl_stream(tmp_path):
    events = [
        {"type": "stream-meta", "stream_id": "s1", "mode": "single", "agents": [{"id": "a1"}]},
        {"type": "user-query", "text": "Check the test"},
    ]
    source = write(tmp_path / "stream.agentson", chr(10).join(json.dumps(e) for e in events))
    cmd_validate(Namespace(input=str(source)))


def test_validate_session_document(tmp_path):
    document = {
        "id": "session-001",
        "tool": {"name": "opencode", "session_id": "source-001"},
        "entries": [{"type": "action", "tool": "shell.run"}],
    }
    source = write(tmp_path / "document.agentson", json.dumps(document))
    cmd_validate(Namespace(input=str(source)))


def test_rejects_jsonl_without_stream_meta_first(tmp_path):
    event = {"type": "user-query", "text": "Missing stream header"}
    source = write(tmp_path / "bad-stream.agentson", json.dumps(event))
    with pytest.raises(SystemExit) as error:
        cmd_validate(Namespace(input=str(source)))
    assert error.value.code == 1


def test_rejects_invalid_session_document(tmp_path):
    document = {"id": "session-001", "tool": {"name": "opencode"}, "entries": []}
    source = write(tmp_path / "bad-document.agentson", json.dumps(document))
    with pytest.raises(SystemExit) as error:
        cmd_validate(Namespace(input=str(source)))
    assert error.value.code == 1


def test_rejects_empty_directory(tmp_path):
    with pytest.raises(SystemExit) as error:
        cmd_validate(Namespace(input=str(tmp_path)))
    assert error.value.code == 1
