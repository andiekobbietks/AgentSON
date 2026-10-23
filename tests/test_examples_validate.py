"""Validate every committed example against the schema, and hold the line.

WHY: ADR-014 found that a reader emitted a type the schema did not have,
and the reason it went unnoticed is worth repeating: 'neither reader's own
test suite catches this, since neither runs its output through jsonschema
against the real spec'.

The same was true of the committed examples. Nothing validated them, so 17
of 68 did not validate, and nobody knew which 17 or why. ADR-022 decided
the three causes - a side-effect that could not exist without a fabricated
path, a mode that named the file format instead of the stream shape, and a
'context' entry that was not a primitive.

The debt is now paid, and these tests hold the line: every example
validates, and a new one that does not is a regression.
"""
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

REPO = Path(__file__).parent.parent
EXAMPLES = REPO / "examples"
ENTRY_SCHEMA = REPO / "spec" / "v1.2-entries.json"

with open(ENTRY_SCHEMA, encoding="utf-8") as f:
    ENTRY_SCHEMA_DOC = json.load(f)
VALIDATOR = Draft202012Validator(ENTRY_SCHEMA_DOC)


def example_entries(path):
    """The entries of an example, the way the CLI's validate reads them.

    A JSONL file is one entry per line. A single-document JSON file has an
    'entries' array. A one-entry file is still an entry.

    A file that is NOT an AgentSON document returns None and is skipped.
    examples/chatgpt_all_sessions.json is a raw ChatGPT export - it is the
    IMPORTER's input, not a format example, and it is not required to
    validate against the format it is an input to.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return None
    if len(lines) > 1:
        try:
            objs = [json.loads(l) for l in lines]
        except json.JSONDecodeError:
            objs = None
        if objs and all(isinstance(o, dict) and "type" in o for o in objs):
            return objs
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(doc, dict) and isinstance(doc.get("entries"), list):
        return doc["entries"]
    # A bare list of entries.
    if isinstance(doc, list) and doc and all(
            isinstance(o, dict) and "type" in o for o in doc):
        return doc
    if isinstance(doc, dict) and "type" in doc:
        return [doc]
    return None


def collect_failures():
    """Every example that does not validate, and why."""
    failures = {}
    for path in sorted(p for p in EXAMPLES.iterdir() if p.is_file()):
        entries = example_entries(path)
        if entries is None:
            continue
        for i, entry in enumerate(entries):
            errors = list(VALIDATOR.iter_errors(entry))
            if errors:
                failures.setdefault(path.name, []).append(
                    (i, entry.get("type", "?"), errors[0].message)
                )
    return failures


class TestCommittedExamplesValidate:
    """Every committed example must validate against the format's schema."""

    def test_every_committed_example_validates(self):
        failures = collect_failures()
        assert not failures, (
            "these committed examples do not validate against the schema: "
            + ", ".join(
                f"{name} (entries {[e[0] for e in errs]})"
                for name, errs in failures.items()
            )
        )

    def test_the_examples_are_actually_being_checked(self):
        """A check that examines nothing is not a check."""
        checked = 0
        for path in EXAMPLES.iterdir():
            if path.is_file() and example_entries(path) is not None:
                checked += 1
        assert checked >= 60, f"only {checked} examples are entry-shaped"

    def test_the_primitives_are_the_twelve(self):
        """ADR-016: context was demoted, so the entry types are exactly 12."""
        from .spec_types import CANONICAL_PRIMITIVES
        assert len(CANONICAL_PRIMITIVES) == 12
        assert "context" not in CANONICAL_PRIMITIVES


class TestTheThreeCausesStayFixed:
    """The three causes ADR-022 decided must not come back."""

    def test_no_example_carries_a_context_entry(self):
        offenders = []
        for path in EXAMPLES.iterdir():
            if not path.is_file():
                continue
            entries = example_entries(path)
            for entry in entries or []:
                if entry.get("type") == "context":
                    offenders.append(path.name)
        assert not offenders, f"context entries found in: {sorted(set(offenders))}"

    def test_no_example_declares_a_mode_outside_the_enum(self):
        offenders = []
        for path in EXAMPLES.iterdir():
            if not path.is_file():
                continue
            for entry in example_entries(path) or []:
                if entry.get("type") == "stream-meta":
                    mode = entry.get("mode")
                    if mode not in ("single", "multi", "collab"):
                        offenders.append(f"{path.name}:{mode!r}")
        assert not offenders, f"bad stream-meta.mode: {offenders}"

    def test_every_side_effect_identifies_its_change(self):
        """ADR-022: a side-effect needs a path OR an action."""
        offenders = []
        for path in EXAMPLES.iterdir():
            if not path.is_file():
                continue
            for entry in example_entries(path) or []:
                if entry.get("type") == "side-effect":
                    if "path" not in entry and "action" not in entry:
                        offenders.append(path.name)
        assert not offenders, (
            "side-effects with neither path nor action: " f"{sorted(set(offenders))}"
        )

    def test_every_observation_declares_a_source(self):
        offenders = []
        for path in EXAMPLES.iterdir():
            if not path.is_file():
                continue
            for entry in example_entries(path) or []:
                if entry.get("type") == "observation" and "source" not in entry:
                    offenders.append(path.name)
        assert not offenders, f"observations without a source: {sorted(set(offenders))}"
