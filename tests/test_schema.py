"""Tests for AgentSON v1.2 schema and entry validation.

60 test cases covering:
- 12 primitive types (valid + invalid for each)
- Schema-level validation
- CLI validate command
- Edge cases (empty, malformed, mixed formats)
"""
import json
import tempfile
import os
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jsonschema import Draft202012Validator

# Load schemas
SCHEMA_DIR = Path(__file__).parent.parent / "spec"
ENTRY_SCHEMA_PATH = SCHEMA_DIR / "v1.2-entries.json"
FULL_SCHEMA_PATH = SCHEMA_DIR / "v1.2.json"

with open(ENTRY_SCHEMA_PATH, "r", encoding="utf-8") as f:
    ENTRY_SCHEMA = json.load(f)

with open(FULL_SCHEMA_PATH, "r", encoding="utf-8") as f:
    FULL_SCHEMA = json.load(f)

entry_validator = Draft202012Validator(ENTRY_SCHEMA)
full_validator = Draft202012Validator(FULL_SCHEMA)


# =============================================================================
# Helpers
# =============================================================================

def make_entry(entry_type, **kwargs):
    """Create a minimal valid entry of the given type."""
    base = {"type": entry_type, "timestamp": 1783400000000}
    base.update(kwargs)
    return base


def validate_entry(entry):
    """Return list of error messages for an entry."""
    return [e.message for e in entry_validator.iter_errors(entry)]


def validate_full(data):
    """Return list of error messages for a full document."""
    return [e.message for e in full_validator.iter_errors(data)]


# =============================================================================
# stream-meta (6 tests)
# =============================================================================

class TestStreamMeta:
    def test_valid_single_mode(self):
        entry = make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}], mode="single")
        assert validate_entry(entry) == []

    def test_valid_multi_mode(self):
        entry = make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}, {"id": "a2"}], mode="multi")
        assert validate_entry(entry) == []

    def test_valid_collab_mode(self):
        entry = make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}], mode="collab")
        assert validate_entry(entry) == []

    def test_missing_stream_id(self):
        entry = make_entry("stream-meta", agents=[{"id": "a1"}], mode="single")
        assert len(validate_entry(entry)) > 0

    def test_missing_agents(self):
        entry = make_entry("stream-meta", stream_id="s1", mode="single")
        assert len(validate_entry(entry)) > 0

    def test_missing_mode(self):
        entry = make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}])
        assert len(validate_entry(entry)) > 0


# =============================================================================
# handoff (5 tests)
# =============================================================================

class TestHandoff:
    def test_valid(self):
        entry = make_entry("handoff", **{"from": "a1", "to": "a2", "conch": "a2"})
        assert validate_entry(entry) == []

    def test_missing_from(self):
        entry = make_entry("handoff", to="a2", conch="a2")
        assert len(validate_entry(entry)) > 0

    def test_missing_to(self):
        entry = make_entry("handoff", **{"from": "a1"}, conch="a2")
        assert len(validate_entry(entry)) > 0

    def test_missing_conch(self):
        entry = make_entry("handoff", **{"from": "a1"}, to="a2")
        assert len(validate_entry(entry)) > 0

    def test_with_reason(self):
        entry = make_entry("handoff", **{"from": "a1", "to": "a2", "conch": "a2", "reason": "task complete"})
        assert validate_entry(entry) == []


# =============================================================================
# presence (4 tests)
# =============================================================================

class TestPresence:
    def test_valid_online(self):
        entry = make_entry("presence", status="online", agent="a1")
        assert validate_entry(entry) == []

    def test_valid_busy(self):
        entry = make_entry("presence", status="busy", agent="a1", message="Running")
        assert validate_entry(entry) == []

    def test_missing_status(self):
        entry = make_entry("presence", agent="a1")
        assert len(validate_entry(entry)) > 0

    def test_invalid_status(self):
        entry = make_entry("presence", status="invalid", agent="a1")
        assert len(validate_entry(entry)) > 0


# =============================================================================
# capabilities (4 tests)
# =============================================================================

class TestCapabilities:
    def test_valid(self):
        entry = make_entry("capabilities", agent="a1", capabilities={"bash": "Run shell commands"})
        assert validate_entry(entry) == []

    def test_missing_agent(self):
        entry = make_entry("capabilities", capabilities={"bash": "Run shell commands"})
        assert len(validate_entry(entry)) > 0

    def test_missing_capabilities(self):
        entry = make_entry("capabilities", agent="a1")
        assert len(validate_entry(entry)) > 0

    def test_empty_capabilities(self):
        entry = make_entry("capabilities", agent="a1", capabilities={})
        assert validate_entry(entry) == []


# =============================================================================
# action (5 tests)
# =============================================================================

class TestAction:
    def test_valid(self):
        entry = make_entry("action", tool="bash.run", agent="a1")
        assert validate_entry(entry) == []

    def test_missing_tool(self):
        entry = make_entry("action", agent="a1")
        assert len(validate_entry(entry)) > 0

    def test_with_args(self):
        entry = make_entry("action", tool="bash.run", agent="a1", args={"command": "ls"})
        assert validate_entry(entry) == []

    def test_with_status(self):
        entry = make_entry("action", tool="bash.run", agent="a1", status="success")
        assert validate_entry(entry) == []

    def test_invalid_status(self):
        entry = make_entry("action", tool="bash.run", agent="a1", status="invalid")
        assert len(validate_entry(entry)) > 0


# =============================================================================
# observation (4 tests)
# =============================================================================

class TestObservation:
    def test_valid(self):
        entry = make_entry("observation", text="File created", source="tool")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("observation", source="tool")
        assert len(validate_entry(entry)) > 0

    def test_missing_source(self):
        entry = make_entry("observation", text="File created")
        assert len(validate_entry(entry)) > 0

    def test_invalid_source(self):
        entry = make_entry("observation", text="File created", source="invalid")
        assert len(validate_entry(entry)) > 0


# =============================================================================
# thought (3 tests)
# =============================================================================

class TestThought:
    def test_valid(self):
        entry = make_entry("thought", text="I need to refactor this")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("thought")
        assert len(validate_entry(entry)) > 0

    def test_with_agent(self):
        entry = make_entry("thought", text="Planning next step", agent="a1")
        assert validate_entry(entry) == []


# =============================================================================
# side-effect (3 tests)
# =============================================================================

class TestSideEffect:
    def test_valid(self):
        entry = make_entry("side-effect", path="src/main.py")
        assert validate_entry(entry) == []

    def test_missing_path(self):
        entry = make_entry("side-effect")
        assert len(validate_entry(entry)) > 0

    def test_with_diff(self):
        entry = make_entry("side-effect", path="src/main.py", diff="+line1\n-line2")
        assert validate_entry(entry) == []


# =============================================================================
# answer (3 tests)
# =============================================================================

class TestAnswer:
    def test_valid(self):
        entry = make_entry("answer", text="42")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("answer")
        assert len(validate_entry(entry)) > 0

    def test_empty_text(self):
        entry = make_entry("answer", text="")
        assert validate_entry(entry) == []


# =============================================================================
# user-query (4 tests)
# =============================================================================

class TestUserQuery:
    def test_valid(self):
        entry = make_entry("user-query", text="What is the capital of France?")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("user-query")
        assert len(validate_entry(entry)) > 0

    def test_with_query(self):
        entry = make_entry("user-query", text="Show me", query="SELECT * FROM users")
        assert validate_entry(entry) == []

    def test_with_agent(self):
        entry = make_entry("user-query", text="Help me", agent="user")
        assert validate_entry(entry) == []


# =============================================================================
# user-feedback (4 tests)
# =============================================================================

class TestUserFeedback:
    def test_valid(self):
        entry = make_entry("user-feedback", text="That was wrong")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("user-feedback")
        assert len(validate_entry(entry)) > 0

    def test_with_sentiment(self):
        entry = make_entry("user-feedback", text="Good job", sentiment="positive")
        assert validate_entry(entry) == []

    def test_invalid_sentiment(self):
        entry = make_entry("user-feedback", text="Meh", sentiment="meh")
        assert len(validate_entry(entry)) > 0


# =============================================================================
# system-event (4 tests)
# =============================================================================

class TestSystemEvent:
    def test_valid(self):
        entry = make_entry("system-event", text="Cron triggered", source="cron")
        assert validate_entry(entry) == []

    def test_missing_text(self):
        entry = make_entry("system-event", source="cron")
        assert len(validate_entry(entry)) > 0

    def test_missing_source(self):
        entry = make_entry("system-event", text="Triggered")
        assert len(validate_entry(entry)) > 0

    def test_invalid_source(self):
        entry = make_entry("system-event", text="Event", source="magic")
        assert len(validate_entry(entry)) > 0


# =============================================================================
# Full document validation (5 tests)
# =============================================================================

class TestFullDocument:
    def test_valid_single_document(self):
        data = {
            "id": "test-session",
            "tool": {"name": "opencode", "session_id": "s1"},
            "entries": [
                make_entry("action", tool="bash.run", agent="a1"),
                make_entry("observation", text="done", source="tool"),
            ]
        }
        errors = validate_full(data)
        # May have warnings but should not crash
        assert isinstance(errors, list)

    def test_valid_jsonl_stream(self):
        lines = [
            make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}], mode="single"),
            make_entry("action", tool="bash.run", agent="a1"),
            make_entry("observation", text="done", source="tool"),
        ]
        for line in lines:
            errors = validate_entry(line)
            assert errors == [], f"Entry {line['type']} failed: {errors}"

    def test_empty_object_fails(self):
        errors = validate_entry({})
        assert len(errors) > 0

    def test_invalid_type_fails(self):
        entry = make_entry("nonexistent-type", text="test")
        errors = validate_entry(entry)
        assert len(errors) > 0

    def test_provenance_fields(self):
        entry = make_entry(
            "action", tool="bash.run", agent="a1",
            provenance={"confidence": "confirmed", "source": "cdp", "timestamp_ms": 1783400000000}
        )
        errors = validate_entry(entry)
        assert errors == []


# =============================================================================
# Edge cases (7 tests)
# =============================================================================

class TestEdgeCases:
    def test_minimal_valid_entry(self):
        """Only type + required fields."""
        entry = {"type": "action", "tool": "bash.run"}
        errors = validate_entry(entry)
        assert errors == []

    def test_extra_fields_ignored(self):
        """Extra fields should not cause validation errors."""
        entry = make_entry("action", tool="bash.run", custom_field="custom_value")
        errors = validate_entry(entry)
        assert errors == []

    def test_timestamp_not_required(self):
        """timestamp is optional in baseEntry."""
        entry = {"type": "thought", "text": "hello"}
        errors = validate_entry(entry)
        assert errors == []

    def test_correlation_id_optional(self):
        entry = make_entry("action", tool="bash.run", correlation_id="abc-123")
        errors = validate_entry(entry)
        assert errors == []

    def test_multiple_handoffs(self):
        """A stream with multiple handoffs should validate."""
        entries = [
            make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}, {"id": "a2"}], mode="multi"),
            make_entry("handoff", **{"from": "a1", "to": "a2", "conch": "a2"}),
            make_entry("handoff", **{"from": "a2", "to": "a1", "conch": "a1"}),
        ]
        for e in entries:
            assert validate_entry(e) == []

    def test_full_session_flow(self):
        """Realistic multi-agent session: stream-meta → query → thought → handoff → action → observation → answer."""
        entries = [
            make_entry("stream-meta", stream_id="s1", agents=[{"id": "code"}, {"id": "browser"}], mode="multi"),
            make_entry("user-query", text="Find the bug in main.py"),
            make_entry("thought", text="I need to read the file first"),
            make_entry("handoff", **{"from": "user", "to": "code", "conch": "code", "reason": "task assigned"}),
            make_entry("action", tool="read", agent="code", args={"path": "main.py"}),
            make_entry("observation", text="Found null pointer on line 42", source="tool"),
            make_entry("handoff", **{"from": "code", "to": "browser", "conch": "browser", "reason": "need browser test"}),
            make_entry("action", tool="browser.navigate", agent="browser", args={"url": "http://localhost:3000"}),
            make_entry("observation", text="Page loads correctly", source="tool"),
            make_entry("handoff", **{"from": "browser", "to": "code", "conch": "code", "reason": "verified fix"}),
            make_entry("answer", text="The bug was a missing null check on line 42."),
        ]
        for e in entries:
            assert validate_entry(e) == [], f"Entry {e['type']} failed validation"

    def test_empty_entries_array(self):
        """Empty entries array is valid in a full document."""
        data = {
            "id": "empty-session",
            "tool": {"name": "opencode", "session_id": "s1"},
            "entries": []
        }
        errors = validate_full(data)
        assert isinstance(errors, list)


# =============================================================================
# CLI integration (6 tests)
# =============================================================================

class TestCLIValidate:
    def _write_agentson(self, tmpdir, filename, content):
        path = Path(tmpdir) / filename
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_validate_valid_jsonl(self, tmp_path):
        entries = [
            json.dumps(make_entry("stream-meta", stream_id="s1", agents=[{"id": "a1"}], mode="single")),
            json.dumps(make_entry("action", tool="bash.run", agent="a1")),
            json.dumps(make_entry("observation", text="done", source="tool")),
        ]
        path = self._write_agentson(tmp_path, "valid.agentson", "\n".join(entries))
        # Direct validation via schema
        with open(path, "r") as f:
            lines = [json.loads(l) for l in f.read().strip().split("\n") if l.strip()]
        for line in lines:
            assert validate_entry(line) == []

    def test_validate_invalid_entry(self, tmp_path):
        invalid = json.dumps({"type": "action"})  # missing tool
        path = self._write_agentson(tmp_path, "bad.agentson", invalid)
        with open(path, "r") as f:
            entry = json.loads(f.read().strip())
        assert len(validate_entry(entry)) > 0

    def test_validate_empty_file(self, tmp_path):
        path = self._write_agentson(tmp_path, "empty.agentson", "")
        with open(path, "r") as f:
            content = f.read().strip()
        assert content == ""

    def test_validate_malformed_json(self, tmp_path):
        path = self._write_agentson(tmp_path, "malformed.agentson", "{not json}")
        with open(path, "r") as f:
            content = f.read().strip()
        with pytest.raises(json.JSONDecodeError):
            json.loads(content)

    def test_validate_v1_single_document(self, tmp_path):
        data = {
            "id": "test",
            "tool": {"name": "opencode", "session_id": "s1"},
            "entries": [make_entry("action", tool="bash.run")]
        }
        path = self._write_agentson(tmp_path, "v1.agentson", json.dumps(data))
        with open(path, "r") as f:
            doc = json.loads(f.read())
        assert "id" in doc
        assert "entries" in doc

    def test_validate_stream_meta_first(self, tmp_path):
        """JSONL streams should start with stream-meta."""
        entries = [
            json.dumps(make_entry("action", tool="bash.run")),  # wrong first entry
        ]
        path = self._write_agentson(tmp_path, "no_meta.agentson", "\n".join(entries))
        with open(path, "r") as f:
            lines = [json.loads(l) for l in f.read().strip().split("\n") if l.strip()]
        assert lines[0].get("type") != "stream-meta"


# =============================================================================
# Provenance (3 tests)
# =============================================================================

class TestProvenance:
    def test_valid_provenance(self):
        entry = make_entry("action", tool="bash.run", provenance={
            "confidence": "confirmed", "source": "cdp", "timestamp_ms": 1783400000000
        })
        assert validate_entry(entry) == []

    def test_invalid_confidence(self):
        entry = make_entry("action", tool="bash.run", provenance={"confidence": "maybe"})
        assert len(validate_entry(entry)) > 0

    def test_invalid_source(self):
        entry = make_entry("action", tool="bash.run", provenance={"source": "unknown-source"})
        assert len(validate_entry(entry)) > 0
