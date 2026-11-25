# ADR-014: Observation Event Type in the Specification

**Status:** Resolved by the v1.2 specification; historical proposal  
**Date:** 06 July 2026  
**Resolution recorded:** 25 November 2026

## Context

A reader validation exercise identified that source adapters emitted observation events while the early v1 schema did not include observation in its event-type vocabulary. This exposed a mismatch between reader output and the then-current schema.

## Resolution

The observation primitive is part of the current v1.2 ontology and event schema. The original proposal to add observation has therefore been implemented in the v1.2 contract and is no longer an open design question.

- The canonical interchange format is v1.2 JSONL.
- Each line is a typed event; the stream begins with stream-meta.
- Individual events are validated against spec/v1.2-entries.json.
- The materialised/document representation is described by spec/v1.2.json.
- Observation remains distinct from action (an invocation) and side-effect (a persistent change), but adapters must not fabricate an observation when the source did not expose one.

## Consequences

- New producers should emit the v1.2 vocabulary.
- Legacy v1/v1.1 inputs may require explicit compatibility handling.
- Reader fixtures must exercise observation mapping and correlation where the source provides the relevant evidence.
- This ADR is retained as historical rationale; the accepted current contract is governed by Specification ADR-015, ADR-016 and ADR-017.

## References

- spec/ontology.md
- spec/v1.2-entries.json
- spec/v1.2.json
- Specification ADR-015: Canonical Schema
