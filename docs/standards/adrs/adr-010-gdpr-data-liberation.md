# ADR-010: Data Portability as a Design Use Case

**Status:** Accepted (scoped)  
**Date:** 05 July 2026; wording clarified 25 November 2026  
**Author:** Andrea Enning

## Context

AI-agent sessions can contain prompts, generated content, tool interactions, observations, code and metadata. Depending on the source product, user, account type and export interface, some of this information may be difficult to inspect or move into another tool.

Data portability is therefore a useful design motivation for AgentSON: provide a documented, machine-readable representation for information that a supported adapter can lawfully and technically obtain.

The original version of this ADR overstated the legal position by implying that GDPR Article 20 automatically covers every AI interaction and that AgentSON itself fulfils GDPR or EU AI Act obligations. Those conclusions are not supported by the format or repository.

## Decision

AgentSON will support data portability as a technical design use case, while making no blanket legal claim.

1. Build local export and inspection paths for supported source formats.
2. Preserve provenance and make conversion loss visible.
3. Keep the format open and vendor-neutral.
4. Avoid requiring a hosted AgentSON service for core archive operations.
5. Document that access, collection, retention, disclosure and deletion depend on applicable law, product terms, permissions and the facts of each use.

## Legal and regulatory boundary

GDPR Article 20 is conditional. Its application depends on the data subject, the processing basis, whether processing is automated, and whether the relevant personal data was provided by the data subject, among other conditions. It does not create an automatic right to every internal record, every inferred field or every AI interaction.

The EU AI Act contains transparency obligations that depend on the system, provider/deployer role, use case and applicable provision. A machine-readable session archive does not, by itself, satisfy those obligations.

AgentSON:
- is not a legal service or legal opinion;
- does not determine whether a user is entitled to a source export;
- does not compel a vendor to expose data;
- does not guarantee that an adapter captures every relevant record;
- does not certify GDPR, EU AI Act or other regulatory compliance.

Users and organisations remain responsible for lawful access, processing, minimisation, retention, security and disclosure.

## Consequences

- Product copy must describe technical portability and inspectability, not guaranteed legal rights.
- Compliance claims require a separate, scoped assessment by qualified people against the actual system and use case.
- The project must not claim that it captures every thought, action or private runtime state.
- The Unsloth analogy may be used as a product-positioning metaphor, not as evidence of legal entitlement or equivalent technical capability.

## References

- GDPR Article 20 and relevant supervisory-authority guidance.
- EU AI Act provisions applicable to the particular system and role.
- README.md, PRD.md and the reader conformance matrix.
