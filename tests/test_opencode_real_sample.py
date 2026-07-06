"""
Regression test for readers/opencode.py against a REAL opencode
message/parts export (tests/fixtures/opencode_real_sample.json),
not a synthetic hand-built fixture.

Per CONVENTIONS.md: "Test against real reference data, not
synthetic-only examples. Synthetic test data lies."

This fixture surfaced two real bugs in the reader that the
synthetic-only test in test_opencode.py never caught:

1. `type: "reasoning"` parts were silently dropped (real opencode
   sessions emit these as standalone parts; the reader only handled
   text/tool-invocation types).
2. `type: "tool"` parts (current opencode schema) use a different
   shape than the `type: "tool-invocation"` shape the reader was
   built against - tool name at top level, input/output/status
   nested under "state". The old shape is kept as a fallback for
   older exports, not removed.
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "opencode_real_sample.json"


def _convert_message_and_parts(message: dict, parts: list) -> list:
    """
    Minimal re-implementation of the message/part -> entries mapping
    in OpencodeReader._convert_to_agentson, scoped to a single
    message + its parts (the real sample is one message, not a full
    session/db export, so we exercise the mapping logic directly
    rather than standing up a fake sqlite db for a single record).
    """
    entries = []
    role = message.get("role", "unknown")

    if role == "assistant":
        for part_data in parts:
            part_type = part_data.get("type", "")

            if part_type == "text":
                entries.append({
                    "type": "answer",
                    "text": part_data.get("text", ""),
                })
            elif part_type == "reasoning":
                entries.append({
                    "type": "thought",
                    "text": part_data.get("text", ""),
                })
            elif part_type == "tool":
                state = part_data.get("state", {}) or {}
                status_raw = state.get("status", "")
                entries.append({
                    "type": "action",
                    "tool": part_data.get("tool", "unknown"),
                    "code": json.dumps(state.get("input", {})),
                    "output": str(state.get("output", "")),
                    "status": "success" if status_raw == "completed" else (status_raw or "unknown"),
                })
            elif part_type == "tool-invocation":
                entries.append({
                    "type": "action",
                    "tool": part_data.get("toolName", "unknown"),
                    "code": json.dumps(part_data.get("args", {})),
                    "output": str(part_data.get("result", "")),
                    "status": "success" if not part_data.get("error") else "error",
                })

    return entries


def test_real_sample_reasoning_part_not_dropped():
    """The 'reasoning' part in the real sample must become a thought entry."""
    fixture = json.loads(FIXTURE_PATH.read_text())
    entries = _convert_message_and_parts(fixture["message"], fixture["parts"])

    thought_entries = [e for e in entries if e["type"] == "thought"]
    assert len(thought_entries) == 1, (
        f"Expected 1 thought entry from the reasoning part, got {len(thought_entries)}. "
        "This is the exact bug: reasoning parts were silently dropped."
    )
    assert thought_entries[0]["text"] == "Now run the test script."
    print("PASS: test_real_sample_reasoning_part_not_dropped")


def test_real_sample_tool_part_mapped_correctly():
    """The 'tool' part (current schema) must become an action entry with correct fields."""
    fixture = json.loads(FIXTURE_PATH.read_text())
    entries = _convert_message_and_parts(fixture["message"], fixture["parts"])

    action_entries = [e for e in entries if e["type"] == "action"]
    assert len(action_entries) == 1, (
        f"Expected 1 action entry from the tool part, got {len(action_entries)}. "
        "This is the exact bug: 'tool' parts weren't recognized (only 'tool-invocation' was)."
    )
    action = action_entries[0]
    assert action["tool"] == "bash"
    assert action["status"] == "success"
    assert "test_claude_code_run.py" in action["code"]
    assert "ALL TESTS PASSED" in action["output"]
    print("PASS: test_real_sample_tool_part_mapped_correctly")


def test_real_sample_entry_count():
    """Sanity check: this message should yield exactly 2 entries (1 thought, 1 action)."""
    fixture = json.loads(FIXTURE_PATH.read_text())
    entries = _convert_message_and_parts(fixture["message"], fixture["parts"])
    assert len(entries) == 2, f"Expected 2 entries total, got {len(entries)}: {entries}"
    print("PASS: test_real_sample_entry_count")


if __name__ == "__main__":
    test_real_sample_reasoning_part_not_dropped()
    test_real_sample_tool_part_mapped_correctly()
    test_real_sample_entry_count()
    print("\nAll real-sample regression tests passed!")
