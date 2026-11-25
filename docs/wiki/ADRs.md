# Architecture Decision Records

ADRs capture decisions and their rationale. The checked-in repository documents are authoritative; this page is a navigational index.

Two namespaces exist: operating ADRs live under docs/standards/adrs/ and specification ADRs live under spec/. Some identifiers overlap, so always include the namespace and path.

## Decision index

| ADR | Subject | Status |
|---|---|---|
| Operating ADR-001 to ADR-014 | Project, workflow, integration and historical decisions | See docs/standards/adrs/ |
| Operating ADR-010 | Data portability as a design use case | Accepted with scoped wording; not a legal opinion or compliance claim |
| Operating ADR-011 | AgentSON project name and .agentson extension | Accepted naming decision; not trademark clearance |
| Specification ADR-015 | Canonical v1.2 JSONL interchange format | Accepted |
| Specification ADR-016 | Ontology and enum reconciliation | Accepted |
| Specification ADR-017 | Core format and streaming separation | Accepted |
| Specification ADR-024 | JSON session-envelope-only canonical proposal | Not accepted; conflicts with the maintainer's JSONL decision |
| Specification ADR-025 | Cross-harness context continuation | Proposed implementation baseline |

## Key specification decisions

### Canonical format

The canonical v1.2 interchange wire format is JSONL: one event per line, with stream-meta first. Individual events are validated against spec/v1.2-entries.json. The JSON session envelope in spec/v1.2.json remains a supported materialised/document representation, not the canonical wire format.

See:
- [ADR-015: Canonical Schema](https://github.com/andiekobbietks/AgentSON/blob/master/spec/ADR-015-canonical-schema.md)
- [ADR-016: Ontology and Enum Reconciliation](https://github.com/andiekobbietks/AgentSON/blob/master/spec/ADR-016-ontology-enum-reconciliation.md)
- [ADR-017: Core vs Streaming](https://github.com/andiekobbietks/AgentSON/blob/master/spec/ADR-017-core-vs-streaming.md)
- [ADR-024: Rejected JSON-envelope-only proposal](https://github.com/andiekobbietks/AgentSON/blob/master/spec/ADR-024-canonical-session-archive-and-interoperability.md)

### Data portability and legal boundaries

AgentSON is designed to make supported session records more portable and inspectable. Whether a particular person has a right to obtain particular data, and which organisation must provide it, depends on the applicable law, legal basis, controller/processor roles and facts. The project does not determine those questions or certify GDPR or EU AI Act compliance.

See [Operating ADR-010](https://github.com/andiekobbietks/AgentSON/blob/master/docs/standards/adrs/adr-010-gdpr-data-liberation.md).

### Project naming

The project uses the AgentSON name and .agentson file extension. Historical naming research is not a legal clearance search and must not be presented as proof of trademark availability.

See [Operating ADR-011](https://github.com/andiekobbietks/AgentSON/blob/master/docs/standards/adrs/adr-011-naming-and-file-extension.md).

## Related documents

- [Session Interoperability Architecture](../architecture/session-interoperability.md)
- [Cross-Harness Conformance Test Plan](../architecture/conformance-test-plan.md)
- [Repository instructions](../../AGENTS.md)
- [Repository status](../../STATUS.md)
