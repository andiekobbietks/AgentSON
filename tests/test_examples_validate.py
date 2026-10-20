"""Validate every committed example against the schema, and report the debt.

WHY: ADR-014 found that a reader emitted a type the schema did not have,
and the reason it went unnoticed is that 'neither reader's own test suite
catches this, since neither runs its output through jsonschema against the
real spec'. The same is true of the committed examples: nothing validates
them, so 17 of them do not validate, and nobody knows which 17.

This test documents the current state exactly. It is marked xfail because
the failures are real and known, and each one is named. The moment a reader
is fixed, its example starts passing and the xfail turns into a PASS - which
is the signal to remove the marker for that case.

It is deliberately not a plain assert: a test that fails tells you
something broke, and this is a statement of standing debt.
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
    'entries' array. A whole-session document in the v1 shape has neither,
    and is not entry-shaped - it is not validated against the entry schema.

    The order matters: try JSONL first (every line parses as JSON), then
    fall back to the whole file as one JSON document. A pretty-printed
    document must not be mistaken for JSONL, and a JSONL file must not be
    mistaken for a document.
    """
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = [l for l in text.splitlines() if l.strip()]
    if not lines:
        return None

    # JSONL: every line parses, and there is more than one.
    if len(lines) > 1:
        try:
            objs = [json.loads(l) for l in lines]
        except json.JSONDecodeError:
            objs = None
        if objs and all(isinstance(o, dict) and "type" in o for o in objs):
            return objs

    # A single JSON document.
    try:
        doc = json.loads(text)
    except json.JSONDecodeError:
        return None
    if isinstance(doc, dict) and isinstance(doc.get("entries"), list):
        return doc["entries"]
    # A one-entry JSONL stream is still a stream: a single line that is an
    # entry. Treating it as a document would skip it, and a skipped file is
    # an unvalidated file.
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
    """The standing debt, stated so it cannot grow unnoticed."""

    def test_no_example_validates_worse_than_the_known_set(self):
        """A new failure is a regression even while the old ones stand."""
        known = {
            "agentson_discussion.agentson",
            "all_sessions.agentson",
            "chatgpt_export.agentson",
            "cursor-cline-aider-readers-session.agentson",
            "devtools_download_this_video_in_the_scene.agentson",
            "dogfood-session-2026-07-06.agentson",
            "mcp_demo.agentson",
            "opencode_ses_0d4353448ffeDBNFtOt7z7aLX1.agentson",
            "opencode_ses_0d4353d85ffeT1ToT6xZ2EVGHz.agentson",
            "opencode_ses_0d4353dabffeNmaCxop6RmH4Ij.agentson",
            "opencode_ses_0d4353dd1ffelvqC3iqvDzf5WB.agentson",
            "opencode_ses_0d4356d58ffe6WA0D4tWZ5oZRG.agentson",
            "opencode_ses_0d4356d67ffe540oAPmGMH4G6c.agentson",
            "opencode_ses_0d43bc3efffeznwLmVK2asGUGB.agentson",
            "opencode_ses_101f8ef45ffeF0WIZRMuVigCA0.agentson",
            "opencode_ses_1338ee51effejvBlWyDNW4CHW5.agentson",
            "opencode_ses_134764a37ffexh1CtQcREJqLds.agentson",
        }
        failures = collect_failures()
        unexpected = set(failures) - known
        assert not unexpected, (
            "new example(s) fail validation that did not before: "
            f"{sorted(unexpected)}"
        )

    def test_the_known_failures_are_still_the_known_failures(self):
        """The known set must not shrink silently either.

        If a reader is fixed and its example starts passing, this fails -
        which is the prompt to move it out of the known set and to the
        passing set below.
        """
        known = {
            "agentson_discussion.agentson",
            "all_sessions.agentson",
            "chatgpt_export.agentson",
            "cursor-cline-aider-readers-session.agentson",
            "devtools_download_this_video_in_the_scene.agentson",
            "dogfood-session-2026-07-06.agentson",
            "mcp_demo.agentson",
            "opencode_ses_0d4353448ffeDBNFtOt7z7aLX1.agentson",
            "opencode_ses_0d4353d85ffeT1ToT6xZ2EVGHz.agentson",
            "opencode_ses_0d4353dabffeNmaCxop6RmH4Ij.agentson",
            "opencode_ses_0d4353dd1ffelvqC3iqvDzf5WB.agentson",
            "opencode_ses_0d4356d58ffe6WA0D4tWZ5oZRG.agentson",
            "opencode_ses_0d4356d67ffe540oAPmGMH4G6c.agentson",
            "opencode_ses_0d43bc3efffeznwLmVK2asGUGB.agentson",
            "opencode_ses_101f8ef45ffeF0WIZRMuVigCA0.agentson",
            "opencode_ses_1338ee51effejvBlWyDNW4CHW5.agentson",
            "opencode_ses_134764a37ffexh1CtQcREJqLds.agentson",
        }
        failures = collect_failures()
        fixed = known - set(failures)
        assert not fixed, (
            "these examples now validate - move them out of the known-failing "
            f"set and into the passing set: {sorted(fixed)}"
        )

    def test_the_documented_causes_still_apply(self):
        """The three causes, by name. If a cause is fixed, this fails.

        1. side-effect requires 'path' (ADR-016) but the readers write
           'action' / 'text' / 'result' - a todo_update is a persistent
           state change with no path.
        2. stream-meta.mode is 'jsonl', but the enum is single|multi|collab.
        3. 'context' was demoted to metadata by ADR-016 but one example
           still carries it as an entry type.

        The entry schema is a oneOf over the twelve primitives, so a
        jsonschema error for a failing entry reads 'is not valid under any
        of the given schemas' and does not say WHICH constraint failed. The
        cause is therefore identified from the entry's own content, which is
        the thing that has to change anyway.
        """
        failures = collect_failures()
        causes = {
            "side-effect without 'path'": [],
            "stream-meta.mode == 'jsonl'": [],
            "'context' as an entry type": [],
        }
        for name, entries in failures.items():
            for _, entry_type, _ in entries:
                if entry_type == "side-effect":
                    causes["side-effect without 'path'"].append(name)
                elif entry_type == "stream-meta":
                    causes["stream-meta.mode == 'jsonl'"].append(name)
                elif entry_type == "context":
                    causes["'context' as an entry type"].append(name)
        missing = {c: v for c, v in causes.items() if not v}
        assert not missing, (
            f"these failure causes no longer appear: {sorted(missing)} - "
            "the readers or the schema were fixed; update this test"
        )
