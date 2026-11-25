# AgentSON Schema Reference

## Canonical representation

The canonical v1.2 interchange wire format is **JSONL**: one JSON event per line, with a stream-meta event first. The established .agentson extension is retained.

- spec/v1.2-entries.json validates individual event objects in the stream.
- spec/v1.2.json describes the materialised JSON session-envelope/document representation used by compatibility and projection paths. It is not a JSONL stream schema.
- Specification ADR-015 records the JSONL-canonical decision; ADR-016 aligns the ontology and enum; ADR-017 separates core and streaming concerns.

The maintainer explicitly retained JSONL as the canonical interchange wire format. The contrary envelope-only decision proposed in ADR-024 is not accepted. Do not present both decisions as accepted.

## Version history

| Version | Representation | Status |
|---|---|---|
| v1.0 | Single JSON document | Legacy compatibility input |
| v1.1 | Single JSON document with trajectory fields | Legacy compatibility input |
| v1.2 | JSONL stream of typed events | Canonical interchange wire format |
| v1.2 document envelope | Single JSON session envelope | Supported materialised/document compatibility representation |

Detect the actual representation and validate it with the matching contract. Do not infer format from the filename alone.

## Event framing

1. The first line is a stream-meta event declaring stream/session metadata.
2. Subsequent lines are v1.2 event objects.
3. Preserve event ordering and source sequence where available.
4. Validate each event against spec/v1.2-entries.json.
5. Validate any materialised session-envelope document against spec/v1.2.json.

## Event vocabulary

The v1.2 ontology defines twelve event primitives:

| Primitive | Meaning |
|---|---|
| stream-meta | Stream header and participant/capability metadata |
| user-query | User input |
| thought | Reasoning-related content supplied by the source |
| action | Tool or agent action |
| observation | Information observed from a tool, user, system or sensor |
| answer | Agent response |
| side-effect | Persistent state or artefact change |
| user-feedback | User correction or clarification |
| system-event | Runtime or system signal |
| capabilities | Agent capability declaration |
| handoff | Transfer of control |
| presence | Agent presence or status |

A thought event does not imply access to private model reasoning. Adapters must not invent events merely because the vocabulary has a matching primitive.

## Semantic fidelity and provenance

Every adapter/transform should classify relevant information as:

- preserved without semantic change;
- normalised to a documented canonical equivalent;
- inferred by adapter logic rather than explicitly present in the source;
- retained as source-specific extension data;
- unavailable at source or capture time;
- redacted under a documented privacy/security rule; or
- unsupported by the target contract.

Preserve source identifiers, source timestamps and ordering semantics where available. Distinguish source event time from capture time. Do not fabricate missing values. Unknown is not equivalent to absent, false, empty or zero.

## Portability, reconstruction and resumption

- **Portable:** another conforming consumer can parse and understand the archive.
- **Reconstructable:** a consumer can rebuild a useful representation of recorded work while reporting missing state.
- **Resumable:** a compatible receiving harness can continue from a validated checkpoint after capability and permission checks.

These are separate guarantees. A transcript that can be displayed is not proof that runtime state can be resumed. Credentials and reusable secrets must never be embedded in portable archives. Imported commands and tool outputs are untrusted and must not execute during parsing or inspection.

## Validation

Validate JSONL framing and every event against spec/v1.2-entries.json. Use spec/v1.2.json only for the materialised/document envelope representation. A schema-valid archive is not automatically complete, authentic, safe to execute or resumable.

## Related documents

- Session Interoperability Architecture
- Cross-Harness Conformance Test Plan
- ADR-015: Canonical Schema
- ADR-016: Ontology and Enum Reconciliation
- ADR-017: Core vs Streaming Separation
- ADR-025: Cross-Harness Context Continuation
- Reader and Adapter Inventory
- Coding Standards
