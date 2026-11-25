# ADR-024: Canonical Session Envelope Proposal

**Status:** Not accepted  
**Recorded:** 5 November 2026  
**Decision authority:** AgentSON maintainer  
**Related:** Specification ADR-015, ADR-016 and ADR-017

## Context

A proposal was made to treat the single JSON session envelope described by spec/v1.2.json as the canonical v1.2 archive and to demote JSONL to a separate transport. This would conflict with the existing v1.2 JSONL-canonical decision in Specification ADR-015 and with the maintainer's explicit decision recorded in the PR #60 conversation.

## Decision

This proposal is **not accepted**.

The canonical v1.2 interchange wire format remains JSONL: one event per line, with stream-meta first, using the established .agentson extension. Individual events are validated against spec/v1.2-entries.json.

The JSON session envelope described by spec/v1.2.json remains a supported materialised/document representation for compatibility and projection paths. It is not the canonical JSONL wire format and its schema does not validate an entire JSONL stream.

## Consequences

- Specification ADR-015 remains the canonical-format decision.
- Specification ADR-016 remains the ontology/enum alignment decision.
- Specification ADR-017 continues to distinguish core and streaming concerns.
- Documentation must distinguish JSONL stream validation from JSON-envelope validation.
- No branch or document may describe this proposal as an accepted decision.
- Any implementation that emits the JSON envelope must identify that representation explicitly; it must not be described as the canonical JSONL interchange stream.

## References

- spec/ADR-015-canonical-schema.md
- spec/ADR-016-ontology-enum-reconciliation.md
- spec/ADR-017-core-vs-streaming.md
- spec/v1.2-entries.json
- spec/v1.2.json
- PR #60 maintainer format decision (5 November 2026)
