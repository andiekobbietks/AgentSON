# ADR-011: AgentSON Project Name and File Extension

**Status:** Accepted  
**Date:** 04 July 2026  
**Clarified:** 25 November 2026

## Context

The project selected AgentSON as its public project name and .agentson as its preferred archive extension. A shorter .ason extension was considered but not adopted because other software projects use that extension and it could create avoidable format and tooling ambiguity.

The original naming research was a manual, point-in-time search. It was not a formal trademark clearance exercise and did not establish that the name is legally available in every jurisdiction or product category.

## Decision

- Retain **AgentSON** as the project name.
- Retain **.agentson** as the preferred filename extension for canonical v1.2 JSONL streams.
- Do not use **.ason** as the project extension.
- Plain JSON may still be used where a distinct extension is not appropriate, provided the representation is identified and validated explicitly.

## Consequences

- Documentation and examples should use the .agentson extension consistently.
- File contents must be detected and validated; the extension alone does not prove that a file is valid JSONL or belongs to a particular schema version.
- No documentation may claim trademark clearance, registration or guaranteed name availability on the basis of the historical manual search.
- Revisit naming and legal advice before significant commercial expansion or formal registration.

## References

- README.md
- PRD.md
- Specification ADR-015: Canonical Schema
