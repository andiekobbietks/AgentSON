# ADR-001: Why AgentSON Exists as a Format

**Status:** Accepted as product intent; original format description superseded by Specification ADR-015  
**Date:** 04 July 2026  
**Author:** Andrea Enning  
**Clarified:** 25 November 2026

## Context

AI-agent tools store session information in different formats, databases and export interfaces. The available records and their fidelity vary by product and version. Moving between tools can make it difficult to retain useful history, inspect tool activity or compare sessions.

The original ADR described a single JSON document that captured the full structure of a session. That description is historical product intent, not a current completeness guarantee or the canonical v1.2 wire-format definition.

## Decision

Continue developing AgentSON as an open, vendor-neutral interchange format and local toolset for supported AI-agent session records.

The current canonical v1.2 interchange wire format is JSONL: one typed event per line, with stream-meta first. The .agentson extension is retained. Individual events are validated against spec/v1.2-entries.json. The JSON session envelope in spec/v1.2.json remains a supported materialised/document compatibility representation.

AgentSON preserves only what a source exposes and an adapter captures. It does not guarantee complete session capture, private reasoning capture, lossless conversion, or arbitrary cross-harness resumption.

## Consequences

- Source readers must document supported source versions, provenance and known losses.
- Unknown or unsupported source data must not be silently discarded or fabricated.
- Portability, reconstruction and resumption require separate evidence.
- The canonical format decision is governed by Specification ADR-015, not this historical product-intent record.

## References

- Specification ADR-015: Canonical Schema
- Specification ADR-016: Ontology and Enum Reconciliation
- Specification ADR-017: Core vs Streaming
- PRD.md
- docs/standards/reader-conformance-v1.2.md
