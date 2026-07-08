# ADR-015: Canonical Schema Decision

**Status:** Accepted
**Date:** 07 July 2026
**Decision Makers:** andiekobbietks

---

## Context

AgentSON has three schema versions that define incompatible data shapes:

| Schema | Shape | Format | Required Fields |
|--------|-------|--------|----------------|
| `v1.json` | Single JSON document | `{"id": "...", "entries": [...]}` | `id`, `tool`, `entries` |
| `v1.1.json` | Single JSON document | Same as v1 + trajectory | `id`, `tool`, `entries` |
| `v1.2.json` | NDJSON stream (JSONL) | One JSON object per line | **None** (`required: []`) |

Two incompatible shapes coexist:
1. **Single-document** (v1, v1.1): One JSON file = one complete session. Entries is an array inside the document.
2. **NDJSON stream** (v1.2): One JSON object per line. Each line is an independent event. The `stream-meta` entry declares agents and capabilities.

The current codebase produces **both shapes**:
- `cli/main.py` exports v1 format (single-document JSON)
- `stream/lib/agentson_export.cjs` exports v1.2 format (JSONL)
- `examples/*.agentson` files are mixed — some v1, some v1.2

**The problem:** Consumers cannot know which shape they're reading. A JSONL file with `required: []` validates anything, including `{}`.

---

## Decision

**Adopt v1.2 JSONL as the canonical format. Deprecate v1/v1.1 single-document shape.**

### Rationale

1. **Streaming is the primary use case.** Agent sessions are append-only event traces. JSONL is append-only by design. Single-document JSON requires rewriting the entire file on every new entry.

2. **v1.2 already has the richer type system.** The `oneOf` discriminated union with `$defs` for each primitive is more expressive than v1's flat `entries` array with a simple `type` enum.

3. **Interop is simpler with JSONL.** Each line is a valid JSON object. `cat stream1.jsonl stream2.jsonl > merged.jsonl` just works. Single-document JSON requires merge logic.

4. **The streaming collaboration features (handoff, presence, capabilities) are not optional add-ons — they are the core value proposition.** Stripping them to "keep things simple" would remove AgentSON's differentiator.

---

## Consequences

### Positive
- (+) One format to maintain, test, and document
- (+) JSONL is trivially appendable (no rewrite cost)
- (+) `cat`/`grep`/`jq` work on raw files
- (+) Each line validates independently
- (+) Streaming collaboration (handoff, presence) is first-class

### Negative
- (-) Breaking change from v1/v1.1 single-document exports
- (-) All existing v1/v1.1 files need conversion
- (-) `cli/main.py` must be updated to emit JSONL
- (-) Readers must handle JSONL, not JSON array

### Mitigations
- Provide a `agentson convert --from v1 --to v1.2` migration command
- Mark v1/v1.1 as deprecated but still readable for 6 months
- Update `cli/main.py` to emit JSONL by default

---

## Migration Path

1. Add `agentson convert` command that reads v1 JSON and emits v1.2 JSONL
2. Update `cli/main.py` export to emit JSONL (add `"type"` field per entry)
3. Update all example files to v1.2 format
4. Update readers to parse JSONL (line-by-line)
5. Remove v1/v1.1 schema files after deprecation period

---

## Alternatives Considered

### Alternative A: Keep both shapes
**Rejected.** Two shapes means every consumer needs dual parsing. The `required: []` in v1.2 makes it useless for validation. This is the worst of both worlds.

### Alternative B: Single-document JSON with streaming extensions
**Rejected.** Single-document JSON cannot stream. You must rewrite the entire file on every entry. This defeats the purpose of an append-only trace.

### Alternative C: Binary format (MessagePack, CBOR)
**Rejected.** Human readability is a core requirement. `grep` and `jq` must work on raw files.

---

## Litmus Test

> "Does this improve fidelity/portability/replayability/analyzability of a captured episode?"

**Yes.** JSONL is more portable (line-by-line), more analyzable (`grep`, `jq`), more replayable (stream processing), and maintains fidelity (each entry is self-contained).

### ISO Litmus Test

> "Is this the only format solving this problem at the international level?"

**Yes.** AgentSON is the only provenance format for AI agent sessions. No ISO standard exists for agent session recording. No non-ISO standard does this either. JSONL is already a de facto standard (IETF RFC 8259). AgentSON builds on JSONL and adds the 12-primitive ontology that makes agent traces machine-readable and human-analyzable.

---

## References

- `spec/v1.json` — Single-document schema (deprecated)
- `spec/v1.1.json` — Single-document schema with trajectory (deprecated)
- `spec/v1.2.json` — JSONL streaming schema (canonical)
- `spec/ontology.md` — 12-primitive formal ontology (source of truth for types)
