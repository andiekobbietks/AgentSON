# ADR-017: Core vs Streaming Primitive Separation

**Status:** Accepted for event-vocabulary grouping; stream framing is governed by ADR-024
**Date:** 07 July 2026
**Decision Makers:** andiekobbietks

---

> Clarification, 05 November 2026: this ADR separates core event primitives from collaboration/streaming primitives. It does not define the canonical archive container or establish JSONL as the canonical v1.2 archive. See ADR-024 for the canonical JSON session envelope and the separate status of JSONL stream transport.

## Context

The 12 ontology primitives split naturally into two groups:

### Core Primitives (9) — Available Across Session Modes
These event types may occur in either single-agent or multi-agent sessions. They are not a checklist of entries that every session must contain; capture only events the source actually exposes.

| Primitive | Layer | Purpose |
|-----------|-------|---------|
| `action` | Execution | Tool invocation |
| `observation` | Execution | Result from action |
| `thought` | Execution | Agent reasoning |
| `side-effect` | Execution | Persistent state change |
| `answer` | Execution | Final response |
| `user-query` | Input | User request |
| `user-feedback` | Input | User correction |
| `system-event` | Input | External trigger |
| `stream-meta` | Coordination | Session header |

### Collaboration Primitives (3) — Multi-Agent Semantics
These describe collaboration events and should be retained when the source records them. They must not be synthesised merely to make a session appear complete.

| Primitive | Layer | Purpose |
|-----------|-------|---------|
| `handoff` | Coordination | Transfer control |
| `presence` | Coordination | Agent status |
| `capabilities` | Coordination | Agent self-description |

### The Question

Should streaming primitives be **optional** (only in multi-agent streams) or **always required** (even in single-agent streams)?

---

## Decision

**Collaboration primitives are optional when the corresponding event did not occur or was not exposed.** In multi-agent sessions, preserve actual handoffs and presence transitions; include capability declarations when the source provides or negotiates them. Do not require all three event types to appear in every multi-agent session.

### Rationale

1. **Inter-agent handoffs are not required in a single-agent session.** A user-to-agent handoff may still be meaningful and must be preserved if the source records it. Do not invent handoffs merely to satisfy a template.

2. **Presence is meaningless without multiple agents.** "Agent X is online" is only useful when you need to know which agent is active. In a single-agent stream, the agent is always active.

3. **Capabilities are useful but not required.** A single-agent stream from OpenCode doesn't need to advertise "I can use bash" — the consumer already knows what OpenCode can do.

4. **stream-meta is a stream-profile header, not a required entry in every canonical archive.** The v1.2 JSON envelope carries session identity and tool metadata at the top level. A future JSONL stream profile may require a `stream-meta` first record.

### Validation Rules

| Scenario | Event requirements |
|----------|--------------------|
| Single-agent archive | Capture only source-observed events; no collaboration events are required. |
| Multi-agent archive | Preserve actual collaboration events and actor references; do not fabricate missing event types. |
| Line-oriented stream profile | Framing/header requirements must be defined by a separate stream contract. |

### Detection Rule

For a line-oriented stream profile, participant metadata may identify multi-agent operation. For the canonical archive, use the envelope and recorded actor references. Do not infer collaboration events solely from a participant count.

---

## Consequences

### Positive
- (+) Single-agent exports stay simple (no meaningless handoff/presence entries)
- (+) Multi-agent streams get full coordination primitives
- (+) A future stream profile can declare participant/mode metadata without changing the canonical archive envelope
- (+) Backward compatible with existing single-agent exports

### Negative
- (-) Two validation modes (single vs multi-agent) adds complexity
- (-) Consumers must distinguish event vocabulary from stream framing and must not assume every primitive occurs
- (-) Edge case: stream starts single-agent, becomes multi-agent mid-stream

### Mitigations
- A future stream profile may define `mode` in its stream header.
- Stream-level validation may check consistency between declared mode and actual collaboration events.
- The canonical archive validator checks the envelope and entries; it does not impose unimplemented stream-wide cardinality rules.

---

## Schema Impact

### Current v1.2 archive

The v1.2 JSON Schema defines a JSON session envelope with an ordered `entries` array. It includes the `stream-meta` entry definition and its optional `mode` property, but the archive schema does not require a `stream-meta` entry to be first and does not enforce stream-wide event cardinality or collaboration-mode rules.

The `mode` value, when present, is descriptive metadata. It does not require every primitive to occur, and it must not be used to fabricate missing events.

### Future line-oriented stream profile

A separate stream contract may define a first-record header, participant declarations, framing, ordering, termination and stream-level validation. It must preserve user-to-agent handoffs where recorded and distinguish them from inter-agent transfers.

Example validation responsibilities:

- Validate the canonical archive envelope and each entry against the v1.2 contracts.
- Validate a line-oriented stream only against its separately versioned framing contract.
- Check that handoff references resolve to declared actors when the relevant profile provides actor declarations.
- Do not require an observation where the source provides no result.
- Do not require every primitive to occur in every session.
- Do not treat `mode` as permission to reject valid source-observed events without a documented semantic rule.

---

## Litmus Test

> "Does this improve fidelity/portability/replayability/analyzability of a captured episode?"

**Yes.** Separating core from streaming primitives means:
- Higher fidelity (no noise entries in single-agent streams)
- Better analyzability (consumers know what to expect based on mode)
- Same replayability (replay engine handles all 12 types)
- Same portability (the canonical v1.2 JSON envelope is unchanged; stream transport is separate)

### ISO Litmus Test

> "Is this the only format solving this problem at the international level?"

**Yes.** No other format distinguishes single-agent vs multi-agent session traces. The `mode` field in `stream-meta` is a unique capability that makes AgentSON adaptable to any agent architecture.

---

## References

- `spec/ontology.md` lines 12-37 — 12 primitives grouped by layer
- `spec/v1.2.json` lines 59-101 — `streamMeta` definition
- `spec/replay-semantics.md` lines 56-70 — Handoff processing rules
