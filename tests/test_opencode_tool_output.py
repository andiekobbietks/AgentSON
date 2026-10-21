"""Regression tests for the ``type: "tool"`` branch of the opencode reader.

That branch calls ``OpencodeReader._resolve_truncated_output``. The method
was missing until 2026-10-21, so the call raised AttributeError and
``agentson export --tool opencode`` exited 1 having written no file, for any
session containing a current-schema tool part.

Nothing caught it:

* ``tests/test_opencode.py`` builds only ``tool-invocation`` parts -- the
  legacy shape, which never reaches the call.
* ``tests/test_opencode_real_sample.py`` holds a *real* fixture containing
  exactly this shape, but re-implements the mapping inside the test file
  rather than calling the production method, so it cannot fail on a defect
  in it. A repo-wide grep for ``_resolve_truncated_output`` matched only
  readers/opencode.py and readers/minimax.py -- no test file.

These tests exercise the real code path end to end. The database builder is
imported from test_opencode so the schema is declared once.
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from readers.opencode import read  # noqa: E402
from tests.test_opencode import create_test_db  # noqa: E402

MARKER = "...output truncated..."
SAVED_TO = "Full output saved to: "


def _write_db_with_tool_part(output_text: str) -> str:
    """Materialise a db holding one current-schema ``tool`` part.

    ``output_text`` is what opencode stored in ``state.output`` -- truncated
    or not, depending on the case under test.
    """
    conn = create_test_db()
    cursor = conn.cursor()

    part_data = {
        "type": "tool",
        "tool": "bash",
        "state": {
            "status": "completed",
            "input": {"command": "npm test"},
            "output": output_text,
        },
    }
    cursor.execute(
        """
        INSERT INTO part (id, message_id, session_id, time_created,
                          time_updated, data)
        VALUES ('part-tool', 'msg-2', 'test-session-1', 1783100002000,
                1783100002000, ?)
        """,
        (json.dumps(part_data),),
    )
    conn.commit()

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        temp_path = f.name

    on_disk = sqlite3.connect(temp_path)
    conn.backup(on_disk)
    on_disk.close()
    conn.close()
    return temp_path


# This file's own tool part, so it can be told apart from the legacy
# `tool-invocation` part the shared builder already contributes.
MINE = '{"command": "npm test"}'


def _tool_output(path: str):
    """The ``output`` of the one tool part this file inserts.

    Filtering on tool name alone returns the shared builder's legacy
    bash entry first, which would make every assertion here inspect the
    wrong row. Matching on this part's own input disambiguates.
    """
    doc = read(path, "test-session-1")
    for entry in doc["entries"]:
        if entry["type"] == "action" and entry.get("code") == MINE:
            return entry["output"]
    return None


def test_reader_now_defines_the_method():
    """The call site's target must exist on the class."""
    from readers.opencode import OpencodeReader

    assert hasattr(OpencodeReader, "_resolve_truncated_output")


def test_truncated_output_is_inlined_from_side_file():
    """Marker + side file present -> the real content replaces the preview."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    ) as side:
        side.write("FULL OUTPUT FROM SIDE FILE")
        side_path = side.name

    truncated = (
        "line one\n"
        + MARKER
        + "\n\n"
        + SAVED_TO
        + side_path
        + "\n(and more preview text)"
    )
    db_path = _write_db_with_tool_part(truncated)
    try:
        output = _tool_output(db_path)
        assert output is not None, "the tool part produced no action entry"
        assert "FULL OUTPUT FROM SIDE FILE" in output
        assert MARKER not in output
    finally:
        os.unlink(db_path)
        os.unlink(side_path)


def test_missing_side_file_falls_back_to_preview():
    """Marker + side file gone -> the truncated preview survives, no crash."""
    truncated = (
        MARKER
        + "\n\n"
        + SAVED_TO
        + r"C:\nowhere\already-deleted-output.txt"
        + "\n"
    )
    db_path = _write_db_with_tool_part(truncated)
    try:
        output = _tool_output(db_path)
        assert output is not None
        assert MARKER in output
    finally:
        os.unlink(db_path)


def test_untruncated_output_passes_through():
    """No marker at all -> output returned exactly as stored."""
    db_path = _write_db_with_tool_part("3 passed, 0 failed")
    try:
        assert _tool_output(db_path) == "3 passed, 0 failed"
    finally:
        os.unlink(db_path)


def test_marker_without_path_returns_preview():
    """A marker with no parseable side path must not raise."""
    db_path = _write_db_with_tool_part(MARKER + "\n\n" + SAVED_TO)
    try:
        output = _tool_output(db_path)
        assert output is not None
        assert MARKER in output
    finally:
        os.unlink(db_path)


def test_empty_output_is_safe():
    db_path = _write_db_with_tool_part("")
    try:
        assert _tool_output(db_path) == ""
    finally:
        os.unlink(db_path)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("PASS:", name)
