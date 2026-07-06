# ADR-014: `"observation"` is missing from the entry `type` enum

**Status:** Proposed
**Date:** 2026-07-06

## Context

While hand-building a real `.agentson` file (a dogfooding exercise —
reconstructing an actual agent session as a validation test, not a
synthetic demo) and validating it against `spec/v1.json` with the
`jsonschema` library, validation failed with:

```
'observation' is not one of ['user-query', 'context', 'querying',
'title', 'thought', 'action', 'answer', 'side-effect']
```

Checking why revealed the entry type was used deliberately, not a
typo: **`readers/claude_code.py`** (on `master`) and
**`readers/copilot_chat.py`** (PR #20) both emit
`{"type": "observation", ...}` entries for tool-result/system-feedback
content — distinct from `action` (the tool invocation itself) and
`side-effect` (a file diff or external change).

This means every real session either of these readers has ever
produced is schema-invalid against `spec/v1.json` as it currently
stands. The mismatch was silent until an actual validation run against
the schema surfaced it — neither reader's own test suite catches this,
since neither runs its output through `jsonschema` against the real
spec.

## Decision

**Proposed, not yet actioned.** Applying the project's own spec-only
litmus test:

> Does this improve fidelity, portability, replayability, or
> analyzability of a captured episode?

An agent's trace is naturally a thought → action → observation loop
(the ReAct pattern this project's own tooling already produces).
Folding "observation" into `action` loses the distinction between *what
the agent did* and *what it learned as a result* — a real fidelity
loss. Folding it into `side-effect` is worse: `side-effect` already has
a specific, narrower meaning (a diff/external change), and observation
entries aren't always diffs (e.g. "the search returned 3 results").

This suggests `"observation"` should be **added to the enum**, not that
the readers should be changed to avoid it — the readers reflect a real,
useful distinction the spec is currently missing, not a bug in the
readers.

**Two implementation paths, either acceptable:**

1. Add `"observation"` directly to the `entries[].type` enum in
   `spec/v1.json`, alongside a description matching how it's already
   used in practice (result/feedback from a tool or system, with
   optional `source` and `correlation_id` fields — both already used by
   `readers/claude_code.py` and not currently documented in the schema
   at all).
2. If a schema version bump is preferred over a patch to v1, this could
   land as part of a `v1.1` schema (note: `readers/copilot_chat.py`
   already references `"$schema": "https://agentson.dev/schema/v1.1.json"`
   in its output — a version that doesn't yet exist in `spec/`, which is
   its own small inconsistency worth resolving as part of this decision).

## Consequences

- **Positive:** Real session files produced by existing readers become
  actually schema-valid. Closes a silent fidelity gap between what the
  format claims to capture and what a compliant validator will accept.
- **Negative:** Any external tooling that already validates strictly
  against the current enum (unlikely, given pre-launch status) would
  need to accept the new value.
- **Neutral:** `source` and `correlation_id` (already used by
  `readers/claude_code.py`'s observation entries) should be added to
  the entry schema's documented properties at the same time, since
  they're currently accepted only because the schema doesn't set
  `additionalProperties: false` — undocumented, not intentionally
  supported.

## Open question for Andie

Patch `v1.json`'s enum directly, or formalize this as the first real
change under a `v1.1` schema version (which `readers/copilot_chat.py`
already assumes exists)?
