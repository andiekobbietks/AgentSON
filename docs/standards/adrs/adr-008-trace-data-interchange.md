# ADR-008: AgentSON as an Open Interchange Layer for AI Workflow Traces

**Status:** Accepted as product positioning; claims narrowed 25 November 2026  
**Date:** 05 July 2026  
**Author:** Andrea Enning

## Context

AI coding and agent tools can produce session records, tool interactions and related metadata in different proprietary or product-specific formats. Export availability and the fields exposed vary by vendor, product version, account type and interface.

The original ADR included time-sensitive acquisition and market figures, broad claims that no tools export session data, and statements that AgentSON captures every part of a session. Those claims were not suitable as durable architecture evidence and are not maintained here.

## Decision

Position AgentSON as an open interchange layer for the session records that supported source adapters can obtain and represent.

AgentSON does not claim to capture every prompt, thought, action, result, hidden runtime field or provider-side state. It does not replace source-native monitoring, telemetry, agent runtimes or security tools. It aims to preserve source provenance and make conversion limits explicit.

The canonical v1.2 interchange wire format is JSONL. Exporters for downstream analysis or training formats are optional transformations and must not be confused with the canonical archive.

## Consequences

1. The format contract, not a hosted viewer or service, is the interoperability boundary.
2. Each reader is a source-specific mapping with documented provenance, version support and known losses.
3. Each downstream exporter must identify its target format and any transformations.
4. Portability is a technical capability, not a guarantee that a user can legally obtain every source record or that every vendor exposes an export API.
5. Do not make unsupported market-size, competitor, vendor-export, full-capture or training-readiness claims in product documentation.

## References

- README.md
- PRD.md
- Specification ADR-015: Canonical Schema
- docs/standards/reader-conformance-v1.2.md
