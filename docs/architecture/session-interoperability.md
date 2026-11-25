# AgentSON Session Interoperability Architecture

**Status:** Architecture baseline aligned with the maintainer's format decision  
**Canonical wire format:** AgentSON v1.2 JSONL  
**Implementation status:** Capability claims remain adapter- and evidence-specific.

## 1. Product objective

AgentSON provides an open, vendor-neutral way to capture, represent, validate, inspect and exchange AI-agent session histories. Its purpose is to preserve source evidence and provenance across tools without implying that every source is fully observable or every destination can recreate the original runtime.

AgentSON is not an AI harness, execution sandbox, credential manager or guarantee that two agents will behave identically.

## 2. Interoperability guarantees

| Guarantee | Meaning | Minimum evidence |
|---|---|---|
| Capture fidelity | A source adapter extracts available activity with source identity and relevant ordering. | Versioned source fixture, production-reader test and limitations. |
| Archive validity | The exported stream conforms to the declared v1.2 contract. | Stream framing and event-schema validation. |
| Portability | An independent consumer can parse and understand the exchanged stream. | Live producer-to-consumer import and semantic comparison. |
| Reconstruction | A destination rebuilds a useful representation of recorded activity and reports unavailable state. | Destination reconstruction test and explicit loss report. |
| Resumption | A compatible destination continues from a validated checkpoint under explicit authorisation. | Runtime-specific restore test, capability negotiation and approval evidence. |

Portability does not imply reconstruction; reconstruction does not imply resumption.

## 3. Canonical representation

The canonical v1.2 interchange wire format is **JSONL**: one JSON event per line, with a stream-meta event first. The established .agentson extension is retained.

- spec/v1.2-entries.json validates individual v1.2 event objects.
- spec/v1.2.json defines the materialised JSON session-envelope/document representation used by compatibility and projection paths. It is not a validator for an entire JSONL stream.
- Specification ADR-015 records the canonical JSONL decision.
- ADR-016 defines ontology/enum alignment.
- ADR-017 separates core and streaming concerns.

The maintainer explicitly retained JSONL as the canonical interchange wire format and rejected the contrary envelope-only decision proposed in ADR-024. Documentation must not present both decisions as accepted.

## 4. Conceptual pipeline

1. **Capture:** obtain source-native records through a supported export, API or reader.
2. **Preserve:** retain source identifiers, timestamps, raw source fields and extraction method where available and lawful.
3. **Map:** translate source records into v1.2 event primitives with explicit mapping and provenance.
4. **Validate:** check JSONL framing and each event against the applicable contract.
5. **Exchange:** transfer the .agentson stream through an explicitly defined channel.
6. **Inspect:** review the timeline, actors, actions, observations, side effects, provenance and omissions.
7. **Continue / reconstruct / resume:** use a destination-specific capability only where its contract, safety and permission checks are satisfied.

MCP, REST APIs, CLI commands, databases and hosted services are integration or transport surfaces. They do not replace the canonical interchange contract.

## 5. Semantic fidelity and loss accounting

Every adapter and transformation must distinguish:

- **Preserved:** retained without semantic change.
- **Normalised:** mapped to a documented canonical equivalent.
- **Inferred:** assigned by adapter logic rather than explicit source evidence.
- **Source extension:** retained in a namespaced source-specific field.
- **Unavailable:** not exposed by the source or not obtainable by the adapter.
- **Redacted:** deliberately removed or masked.
- **Unsupported:** recognised but not represented by the target contract.

Do not fabricate timestamps, observations, tool results, model identifiers, actor identities or execution state. Unknown is not equivalent to absent, false, empty or zero. Preserve source ordering where available; where clocks differ or timestamps are missing, retain sequence information and declare uncertainty.

## 6. Provenance and integrity

The record should distinguish origin, source identity, capture time, source event time, adapter/version, transformation lineage and confidence. Hashes or signatures may support integrity checks where implemented, but a digest alone does not prove who created an event or whether the source was truthful.

Source payloads can contain personal data, credentials, private paths and confidential code. Redaction is best-effort and must be reviewed before sharing. Imported prompts, commands, tool arguments and outputs are untrusted data and must remain inert during parsing and inspection.

## 7. Continuation and destination safety

A continuation packet is a selected representation of recorded context, not a runtime checkpoint. It cannot restore hidden prompts, credentials, permissions, live processes, unsaved buffers, provider-private state or model cache unless a destination explicitly exposes and validates a compatible mechanism.

The experimental OpenCode consumer queues a synthetic item with immediate resumption disabled. Its content may enter model context on a later turn. The live integration test uses a synthetic ChatGPT-shaped source fixture and demonstrates the tested archive-capsule handoff/read-back path; it does not prove real-source C2 semantics, native event reconstruction or C4 resumption.

## 8. Evidence levels

| Level | Meaning | Required evidence |
|---|---|---|
| C0 | Archive validity | Schema and structural conformance |
| C1 | Source capture | Production adapter exercised against a versioned fixture |
| C2 | Cross-harness portability | Live producer-to-consumer import with semantic comparison |
| C3 | Reconstruction | Destination rebuilds recorded context and reports missing state |
| C4 | Resumption | Destination resumes a validated checkpoint under explicit approval |

C0 or C1 must never be described as C2. C2 does not imply C3 or C4.

## 9. Related documents

- README.md
- PRD.md
- STATUS.md
- spec/v1.2-entries.json
- spec/v1.2.json
- spec/ontology.md
- spec/ADR-015-canonical-schema.md
- spec/ADR-016-ontology-enum-reconciliation.md
- spec/ADR-017-core-vs-streaming.md
- spec/ADR-025-cross-harness-context-continuation.md
- docs/standards/reader-conformance-v1.2.md
