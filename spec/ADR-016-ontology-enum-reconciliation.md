# ADR-016: Ontology ↔ Enum Reconciliation

**Status:** Accepted
**Date:** 07 July 2026
**Decision Makers:** andiekobbietks

---

## Context

The formal ontology (`spec/ontology.md`) defines 12 primitives. The v1.json schema has an `enum` of 8 types. These lists diverge:

### Types in enum, NOT in ontology
| Type | In v1.json enum | In ontology.md |
|------|----------------|----------------|
| `context` | ✅ | ❌ |
| `querying` | ✅ | ❌ |
| `title` | ✅ | ❌ |

### Types in ontology, NOT in enum
| Type | In ontology.md | In v1.json enum | In v1.2 $defs |
|------|----------------|----------------|---------------|
| `handoff` | ✅ | ❌ | ✅ |
| `presence` | ✅ | ❌ | ✅ |
| `capabilities` | ✅ | ❌ | ✅ |
| `observation` | ✅ | ❌ | ✅ |
| `user-feedback` | ✅ | ❌ | ❌ |
| `system-event` | ✅ | ❌ | ❌ |
| `stream-meta` | ✅ | ❌ | ✅ |

**The v1.2 schema partially fixes this** — it has `handoff`, `presence`, `observation`, `stream-meta` in `$defs`. But it's still missing `user-feedback`, `system-event`, and `capabilities` (as a standalone entry type).

### The 3 types in enum but NOT in ontology

| Type | Purpose | Verdict |
|------|---------|---------|
| `context` | Contextual information about the session | **Demote to metadata** — context is session-level, not an entry type |
| `querying` | Agent is actively querying/thinking | **Demote to thought** — this is a thought subtype, not a separate primitive |
| `title` | Section or step title | **Demote to metadata** — titles are display concerns, not execution events |

---

## Decision

**The 12 ontology primitives are the source of truth. The schema enum must match exactly.**

### Canonical 12 Primitives

```
COORDINATION          EXECUTION              INPUT
───────────           ─────────              ─────
stream-meta           action                 user-query
handoff               observation            user-feedback
presence              thought                system-event
capabilities          side-effect
                     answer
```

### Reconciliation Rules

1. **`context`** → Remove from entry types. Context is session-level metadata (already in `context` field of v1.json top-level). If context changes during a session, use `observation` with `source: "system"`.

2. **`querying`** → Remove from entry types. Replace with `thought` entries. The agent's internal reasoning is always a `thought`, regardless of whether it's "querying" or "planning."

3. **`title`** → Remove from entry types. Titles are display metadata. If a step needs a label, use `thought` with a structured `text` field, or add an optional `label` field to any entry type.

4. **`observation`** → Add to v1.json enum (currently missing). This is the counterpart to `action` — every action produces an observation.

5. **`user-feedback`** → Add to all schemas. This is distinct from `user-query` — it's a correction or clarification, not an initial request.

6. **`system-event`** → Add to all schemas. External triggers (cron, webhook, timer) are not user queries and not agent thoughts.

7. **`capabilities`** → Already in v1.2 as `capabilities-refresh`. Keep as `capabilities` per ontology. Rename the v1.2 `$defs` entry.

---

## Consequences

### Positive
- (+) One source of truth: ontology.md defines the types, schemas enforce them
- (+) No more confusion about which types are valid
- (+) Every entry type has clear semantics and required fields
- (+) Consumers can rely on exactly 12 types

### Negative
- (-) Breaking change for any consumer expecting `context`, `querying`, or `title` entries
- (-) Existing exports with these types need migration
- (-) 3 types removed, 4 types added — significant enum change

### Mitigations
- `agentson convert` command handles type migration:
  - `context` entries → merge into session-level `context` field
  - `querying` entries → rename to `thought`
  - `title` entries → drop or convert to `thought` with structured text
- Deprecation period: 6 months of dual-enum support

---

## Required Fields Per Primitive

| Primitive | Required Fields |
|-----------|----------------|
| `stream-meta` | `stream_id`, `agents[]` |
| `handoff` | `from`, `to`, `conch` |
| `presence` | `status`, `agent` |
| `capabilities` | `agent`, `capabilities` |
| `action` | `tool`, `agent` |
| `observation` | `text`, `source` |
| `thought` | `text`, `agent` |
| `side-effect` | `path`, `agent` |
| `answer` | `text`, `agent` |
| `user-query` | `text`, `agent` |
| `user-feedback` | `text`, `agent` |
| `system-event` | `text`, `source` |

---

## Litmus Test

> "Does this improve fidelity/portability/replayability/analyzability of a captured episode?"

**Yes.** Reconciling the enum with the ontology means:
- Higher fidelity (every event type has clear semantics)
- Better analyzability (consumers know exactly what 12 types exist)
- Better replayability (replay engine can handle all 12 types deterministically)
- Same portability (JSONL format unchanged)

### ISO Litmus Test

> "Is this the only format solving this problem at the international level?"

**Yes.** The 12-primitive ontology is the only formal event model for AI agent sessions. No other standard defines what an agent "did" in a vendor-neutral way. The ontology is the source of truth; the schema enforces it.

---

## References

- `spec/ontology.md` — 12-primitive formal ontology (source of truth)
- `spec/v1.json` lines 111-121 — Current 8-type enum
- `spec/v1.2.json` lines 23-36 — Current `oneOf` with 10 types
- `spec/adapter-spec.md` — Adapter mapping tables (uses ontology types)
