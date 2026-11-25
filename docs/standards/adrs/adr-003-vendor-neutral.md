# ADR-003: Why Vendor Neutrality Matters

**Status:** Accepted  
**Date:** 04 July 2026  
**Clarified:** 25 November 2026

## Context

Agent-session data is distributed across products with different storage formats, export interfaces and permission models. Tying the interchange contract to one provider would make compatibility and long-term access dependent on that provider.

## Decision

AgentSON's canonical event vocabulary and archive format must remain vendor-neutral. Source-specific details may be retained in namespaced provenance or extension fields, but must not redefine the core contract.

Core archive validation, inspection and transformation should be usable locally without a hosted AgentSON account. Optional readers, destination adapters, registries and platform services may depend on external products or network access; they must remain optional and declare those dependencies.

## Consequences

- Source and destination adapters are separate from the core schema.
- Vendor-specific fields are preserved where safe and identified as source-specific.
- No claim is made that every source exposes an export API or that every field maps cleanly.
- Switching tools may still lose unsupported or unavailable semantics; adapters must report those gaps.
- Vendor neutrality is an architectural goal, not a guarantee that all vendors support import/export.
