# AgentSON Schema Reference

## Canonical representation

The canonical v1.2 archive is a **single JSON session envelope** defined by [`spec/v1.2.json`](../spec/v1.2.json). It contains session-level metadata and an ordered `entries` array. The individual entry contract is [`spec/v1.2-entries.json`](../spec/v1.2-entries.json); the event vocabulary is defined by [`spec/ontology.md`](../spec/ontology.md).

This is not a JSONL schema. The earlier [ADR-015](../spec/ADR-015-canonical-schema.md) declared JSONL canonical, but that decision was superseded by [ADR-024](../spec/ADR-024-canonical-session-archive-and-interoperability.md) because the v1.2 schema itself defines a JSON object envelope. Existing JSONL exporters/stream code are separate stream or transport implementations until a dedicated stream contract is published.

## Version history

| Version | Representation | Status |
|---|---|---|
| v1.0 | Single JSON document with an entries array | Legacy input |
| v1.1 | Single JSON document with trajectory fields | Legacy input |
| v1.2 | Single JSON session envelope with ordered entries | Canonical archive contract |

Do not infer the format from the filename alone. Detect and validate the actual representation.

## Session envelope

The v1.2 schema defines the envelope fields, including:

- `id`: session identifier.
- `tool`: originating harness and source session identity.
- `agent`: model/agent identity where exposed by the source.
- `task`, `outcome`, `started_at`, `ended_at`: session-level context where known.
- `context`: environment information actually captured.
- `entries`: ordered event records.
- `metadata`: optional session metadata.
- `compliance`, `reconstruct_mode`, `digest`: optional declared metadata; their presence does not prove legal compliance or successful reconstruction.

See the schema for exact types, required fields and constraints. This page is explanatory, not a substitute for the schema.

## Event vocabulary

The ontology and v1.2 schema define these twelve event primitives:

| Primitive | Meaning |
|---|---|
| `stream-meta` | Stream/session header and participant/capability metadata |
| `handoff` | Transfer of control between agents |
| `presence` | Agent presence/status |
| `capabilities` | Agent capability declaration |
| `action` | Tool or agent action |
| `observation` | Result or observation from a tool, user or system |
| `thought` | Agent reasoning/working note, only where source capture and policy permit |
| `side-effect` | Persistent state change |
| `answer` | Agent response |
| `user-query` | User request |
| `user-feedback` | User correction or clarification |
| `system-event` | External runtime/system trigger |

A source adapter must not invent an event because the target vocabulary has a matching type. If the source does not expose the information, mark it unavailable or preserve it as source-specific data where safe.

## Semantic fidelity and provenance

Every adapter/transform must report whether information was:

- preserved without semantic change;
- normalised to a documented canonical equivalent;
- retained as source-specific extension data;
- unavailable at source or capture time;
- redacted under a documented privacy/security rule; or
- unsupported by the target contract.

Preserve source identifiers, source timestamps and ordering semantics where available. Distinguish source event time from AgentSON capture time. Do not fabricate missing values. Unknown is not equivalent to absent, false, empty or zero.

## Portability, reconstruction and resumption

- **Portable:** another conforming consumer can parse and understand the archive.
- **Reconstructable:** a consumer can rebuild a useful representation of recorded work while reporting missing state.
- **Resumable:** a compatible receiving harness can continue from a validated checkpoint after capability and permission checks.

These are separate guarantees. A transcript that can be displayed is not proof that runtime state can be resumed. Credentials and reusable secrets must never be embedded in portable archives. Imported commands and tool outputs are untrusted and must not execute during parsing or inspection.

## Validation

Validate the complete session envelope against `spec/v1.2.json` and validate entry-level constraints against `spec/v1.2-entries.json` using the project's supported validator. A schema-valid archive is not automatically complete, authentic, safe to execute or resumable.

A JSON Schema document does not, by itself, validate a multi-line JSONL stream. Any stream transport requires its own framing, ordering, metadata and conformance contract.

## Related documents

- [Session Interoperability Architecture](../docs/architecture/session-interoperability.md)
- [ADR-024: Canonical Session Archive and Interoperability](../spec/ADR-024-canonical-session-archive-and-interoperability.md)
- [ADR-015: Historical Canonical Schema Decision](../spec/ADR-015-canonical-schema.md)
- [Readers and adapter inventory](Readers)
- [Coding Standards](Coding-Standards)
