# ADR-024: Canonical Session Archive and Cross-Harness Interoperability

**Status:** Accepted as the documentation architecture baseline; implementation migration remains outstanding  
**Date:** 05 November 2026  
**Decision Makers:** AgentSON maintainer

## Context

AgentSON's documentation and implementation history describe incompatible representations:

- ADR-015 declares v1.2 JSONL the canonical format.
- `spec/v1.2.json` is a JSON Schema for a single JSON object requiring `id`, `tool` and `entries`.
- The README and v1/v1.1 history describe a self-contained session document.
- The repository contains both document-shaped exports and line-oriented stream code.
- The product ambition now explicitly includes cross-harness capture, representation, validation, exchange, inspection and, where possible, reconstruction and resumption.

These are not interchangeable descriptions. A JSON Schema for one JSON object does not validate an entire JSONL stream, and a portable transcript does not recreate a receiving harness's execution state.

## Decision

1. **The canonical v1.2 archive is the single JSON session envelope defined by `spec/v1.2.json`.** It contains session metadata and an ordered `entries` array. The file extension is `.agentson`.
2. **JSONL is not the canonical v1.2 archive representation.** Existing JSONL exporters or stream modules are treated as stream/transport implementations until a separately versioned stream contract defines framing, metadata, validation, ordering, termination and conversion to/from the canonical envelope.
3. **Cross-harness interoperability is the product objective.** Capture, portability, reconstruction and resumption are distinct guarantees and must be claimed and tested separately.
4. **No silent semantic loss.** Adapters and transformations must report whether information was preserved, normalised, retained as a source extension, unavailable, redacted or unsupported.
5. **Provenance is part of the interchange contract.** Source identity, capture method/time, transformation lineage and confidence must remain distinguishable from inferred interpretation and access/audit records.
6. **Resumption is capability- and permission-dependent.** Importing a session does not imply that runtime state, credentials, workspace state or tool access can be restored. Credentials are not portable session content.

## Consequences

### Positive

- Resolves the conflict between the v1.2 schema shape and ADR-015's JSONL declaration.
- Gives readers and consumers one canonical archive contract.
- Makes loss, uncertainty and source-specific information visible.
- Prevents transcript replay from being overstated as live session resumption.
- Establishes measurable conformance requirements for future cross-harness integrations.

### Negative and required follow-up

- Any implementation that emits JSONL as if it were a complete v1.2 archive is not aligned with this decision and must be migrated or documented as a separate stream interface.
- Existing examples, exporters, readers and validation commands need a format-by-format audit.
- A future JSONL stream contract requires its own schema/framing rules and conversion tests; this ADR does not define that wire protocol.
- Resume support requires runtime-specific checkpoint and capability contracts; it is not delivered by the archive format alone.

## Compatibility and migration

- Preserve legacy v1 and v1.1 inputs as explicit legacy formats during the documented migration period.
- Treat v1.2 as the canonical session-envelope schema, not as a JSONL schema.
- Provide explicit format detection; do not infer format solely from the filename extension.
- Conversion must produce a loss report and preserve unknown source fields where safe.
- Do not silently rewrite existing user archives.

## Claims policy

A reader/exporter may claim capture or export only for the paths it has tested. A consumer may claim portability only after validating and importing a canonical archive. Reconstruction and resumption claims require separate evidence from the receiving harness. No feature is considered cross-harness resumable merely because its transcript can be displayed or replayed.

## References

- `spec/v1.2.json` — canonical session envelope schema
- `spec/v1.2-entries.json` — entry validation contract
- `spec/ontology.md` — event vocabulary
- `spec/ADR-015-canonical-schema.md` — superseded JSONL decision
- `spec/ADR-016-ontology-enum-reconciliation.md` — ontology alignment
- `spec/ADR-017-core-vs-streaming.md` — core and streaming primitives
- `docs/architecture/session-interoperability.md` — interoperability architecture
