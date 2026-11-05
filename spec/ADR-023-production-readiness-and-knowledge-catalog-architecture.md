# ADR-023: Production Readiness and the Knowledge-Catalogue Boundary

**Status:** Proposed
**Date:** 05 November 2026
**Decision Makers:** Andrea Enning
**Related:** ADR-001 (format purpose), ADR-003 (vendor neutrality), ADR-009 (open interchange), ADR-010 (data liberation), ADR-015 (canonical schema), ADR-016 (ontology), ADR-017 (core/streaming separation), ADR-022 (reader/schema reconciliation)

---

## 1. Context

AgentSON is an open, vendor-neutral representation of agent-session events. The repository also contains a growing Python CLI and an `agentson_platform/` package for local discovery, scanning, classification, reporting and evidence export.

The project is being benchmarked against Google's Open Knowledge Format (OKF) and the knowledge-catalogue work associated with it. That comparison raises a useful architectural question:

> If an open format can participate in a knowledge-catalogue system, what must AgentSON provide before organisations can depend on it as a production service?

The question cannot be answered by comparing format features alone. A format, an ingestion pipeline, a catalogue application and a managed operational service are different architectural layers. A repository that demonstrates their integration is evidence that the layers can be composed; it is not, by itself, evidence that the format supplies every service capability.

This ADR records both the architecture decision and the reasoning correction that led to it. It is intended to make the decision independently reviewable, not to claim that every proposed capability has already been implemented.

## 2. Decision

AgentSON will be developed as **two deliberately separated but interoperable products**:

1. **AgentSON Core (Apache-2.0):** the portable event format, schemas, validators, readers, writers, CLI and protocol-neutral interfaces. It must remain useful offline and without a hosted account.
2. **AgentSON Platform (separately deployable):** optional ingestion, indexing, search, graph/catalogue views, governance, identity, policy enforcement, audit, integrations and operational services. It may be self-hosted or managed, but must not be required to read or validate a core AgentSON file.

The platform may add capabilities around the format. It must not silently redefine the format, make cloud access a condition of data ownership, or make a proprietary service the only conformant consumer.

The production target is not “copy Google's stack”. It is to demonstrate an independently operable, secure, observable and interoperable catalogue service whose source evidence remains portable.

## 3. Reasoning trace: from initial claim to revised decision

This section preserves the decision's public rationale in a form that can be checked. It records premises, evidence, assumptions, inference and correction. It is a decision trace, not a transcript of private deliberation.

### 3.1 Initial observation

**Observation:** Google's OKF work demonstrates an open knowledge representation that can be consumed by catalogue-oriented tooling. AgentSON already has a different but complementary concern: preserving the provenance and temporal sequence of agent execution.

This observation is valid and useful.

### 3.2 Initial premise

**Premise used in the discussion:** “Google has built an entire infrastructure-catalogue service on OKF.”

This sentence compressed at least three claims into one:

- OKF defines a representation for knowledge resources.
- A catalogue implementation can ingest and index resources represented using OKF.
- The surrounding catalogue system supplies operational capabilities such as discovery, identity, permissions, lineage, storage, APIs and service operations.

The first two do not logically establish that OKF itself implements the third.

### 3.3 The inference that failed

**Initial inference:** If Google can build a catalogue around OKF, then OKF itself is effectively the production catalogue architecture, and AgentSON should be production-grade by reaching the same format/repository level.

**Problem:** This conflates an interoperability contract with the system that consumes it. It is a category error and an invalid transfer of capability from an implementation to its input format.

A file format can describe resources and relationships. It does not automatically provide:
- durable ingestion and indexing;
- query execution and search relevance;
- authentication, authorisation and tenant isolation;
- policy evaluation and enforcement;
- audit retention, operational monitoring and incident response;
- availability, backup, recovery, upgrades and support.

Those capabilities may be built by the catalogue implementation, delegated to existing infrastructure, or split across services. They must be evidenced at the correct layer.

### 3.4 What was flawed, precisely

The flaw was **not** the ambition to benchmark AgentSON against Google's work. The flaw was treating the existence of an integrated example as proof that the underlying format owns the integrated system's capabilities.

The reasoning skipped a layer-boundary test:

> Which component defines the data contract, which component performs the operation, and which component is accountable when that operation fails?

It also treated “production-grade” as a single property. In reality, production readiness is contextual and must be assessed against a named workload, threat model, service boundary, SLO and operating model.

### 3.5 Corrected reasoning

The revised argument is:

1. AgentSON's portable event model can be a stable evidence substrate.
2. A catalogue can index AgentSON records and derived entities without changing the canonical event format.
3. The catalogue needs explicit ingestion, indexing, search, access-control, governance and operational components.
4. Those components must have their own contracts, tests, threat model and service-level objectives.
5. Therefore, AgentSON should benchmark **Core against open-format interoperability** and **Platform against catalogue/service engineering** separately.

This preserves the valuable insight while removing the unsupported leap.

### 3.6 What evidence would change this decision?

The decision should be revisited if a reproducible reference implementation demonstrates that a capability currently assigned to the platform is already guaranteed by the OKF contract itself, or if a documented interoperability requirement makes the proposed boundary impractical.

Evidence required for such a change:
- the exact specification clause or implementation component;
- a minimal reproducible example;
- the observable behaviour and failure mode;
- compatibility impact on existing AgentSON consumers;
- a test that would fail if the claim were false.

A product announcement, diagram or marketing description alone is insufficient to move a responsibility into Core.

## 4. Architecture and responsibility boundaries

| Capability | Core responsibility | Platform responsibility |
|---|---|---|
| Event vocabulary and schema | Define and version | Consume and validate |
| Provenance and event identity | Define semantics | Preserve and query |
| Local validation and conversion | Provide | Reuse |
| Reader/importer contracts | Define stable interfaces | Operate ingestion adapters |
| Search | Provide portable local primitives where appropriate | Index and serve multi-source queries |
| Graph/lineage | Define identifiers and relationship semantics | Build and query catalogue graph |
| Identity and access | No mandatory hosted identity | Authenticate and authorise users/services |
| Tenancy | No tenant requirement in file format | Isolate tenant data and operations |
| Retention/deletion | Document file-level handling | Enforce configured lifecycle policies |
| Audit | Preserve event-level provenance | Record administrative and access events |
| Deployment/operations | No cloud dependency | SLOs, monitoring, backup, recovery, upgrades |
| APIs/MCP | Publish stable contracts | Host and govern service endpoints |

### 4.1 Target platform flow

```text
Agent runtimes / tools / external systems
                  |
          Readers and adapters
                  |
       Ingestion API / batch import
                  |
       Validate + normalise + attest
                  |
      Immutable source evidence store
                  |
        Indexing and relationship graph
                  |
      Search / catalogue / policy layer
                  |
       REST API / MCP / CLI / UI / SDK
                  |
         Governed agent and human use
```

Derived indexes and catalogue records must be rebuildable from retained source evidence where the configured retention policy permits. Derived summaries must link back to source event identifiers and record the transformation/version that produced them.

## 5. Production-readiness gates

A production claim must be supported by evidence at each gate. Passing one gate does not imply the others have passed.

| Gate | Required evidence | Release condition |
|---|---|---|
| P0 — Reproducible engineering | CI on supported Python versions; test, schema, build and installed-wheel checks | No merge on failing required checks |
| P1 — Contract integrity | Versioned schemas, compatibility tests, reader fixtures, deterministic validation | No undocumented breaking change |
| P2 — Supply-chain security | Dependency review, secret scanning, SBOM, provenance/attestation, vulnerability response | No untriaged critical/high release blocker |
| P3 — Data protection | Threat model, data classification, redaction policy, encryption, retention/deletion, export controls | Sensitive evidence has an approved handling path |
| P4 — Service security | Authentication, authorisation, tenant isolation, rate limits, secure defaults, audit events | Independent security review for exposed service |
| P5 — Reliability | SLOs, health/readiness checks, structured logs/metrics, backup/restore, recovery exercise | Measured recovery and availability targets |
| P6 — Interoperability | Public API/MCP contracts, SDK examples, conformance suite, independent consumer | A second implementation can consume the contract |
| P7 — Operations and governance | Runbooks, support ownership, incident process, release policy, deprecation policy | Named operator accepts service responsibility |

These gates are a roadmap, not a declaration that AgentSON currently passes them.

## 6. Immediate evidence from the repository review

The accompanying `docs/production-readiness-assessment.md` records the detailed baseline. The most material findings at this decision date are:

- The README advertises v1.2.0 while warning that the project is Alpha/pre-release; `pyproject.toml` still declares package version 0.1.0 and the Alpha classifier.
- The README links to a `ci.yml` badge, but the default-branch tree contains no `.github/workflows/ci.yml`. The workflows present are ADR-viewer workflows, not a test/build pipeline.
- `pyproject.toml` declares only `spec/v1.json` as package data. Distribution contents therefore need an explicit wheel/sdist test before claiming that all schemas and examples are available after installation.
- The platform server describes itself as a local playground/preview. The crawler, scan and report modules form a useful local crawl → classify → report path, but this is not yet evidence of a multi-tenant catalogue service.
- The report module explicitly notes that reports contain sensitive values found during scanning. Data classification, redaction, access control, retention and secure export are therefore release-critical, not optional polish.
- A maintainer-reported local test result is not the same as a reproducible CI result. The repository needs an authoritative workflow and retained run evidence.

## 7. Consequences

### Positive
- Core remains portable, independently useful and vendor-neutral.
- The platform can evolve without forcing hosted-service assumptions into the file format.
- Production readiness becomes a set of observable gates rather than a marketing adjective.
- Reviewers can trace why an architectural conclusion was reached and what evidence would falsify it.

### Costs and trade-offs
- Two release surfaces require compatibility and versioning discipline.
- The platform must implement capabilities that a local prototype can reasonably omit.
- Multi-tenant operation introduces security, privacy and support obligations that are absent from a single-user local tool.
- The project must resist promoting planned capabilities as completed features.

### Rejected alternatives

**A. Put catalogue operations directly into the core format.** Rejected because schemas cannot supply runtime identity, durable indexing, authorisation or service operations.

**B. Make a managed cloud service mandatory.** Rejected because it conflicts with the vendor-neutral and offline-first principles in ADR-003 and the project's data-ownership goals.

**C. Claim production readiness from test count or a successful demo.** Rejected because tests and demos do not establish security, reliability, recovery, governance or independent interoperability.

**D. Copy Google's architecture wholesale.** Rejected because the service boundary, workload, trust model and operational constraints differ. Reuse patterns only where evidence supports them.

## 8. Traceability requirements for future decisions

Every material architecture ADR should record:

1. **Claim:** the proposition being considered.
2. **Evidence:** source files, tests, specifications, measurements or external references.
3. **Assumptions:** what is not yet proven.
4. **Inference:** how the evidence supports the decision.
5. **Counterargument:** the strongest plausible alternative.
6. **Failure mode:** what would make the decision harmful or incorrect.
7. **Falsification test:** what observation would disprove the rationale.
8. **Consequences:** migration, compatibility, security and operational costs.
9. **Review trigger:** when the decision must be revisited.

This is the project's public decision record. It should explain the reasoning sufficiently for another engineer to audit and challenge it without implying that unobservable internal model reasoning is a source of authority.

## 9. References

- AgentSON repository: https://github.com/andiekobbietks/AgentSON
- AgentSON coding standards and bug-response procedure: `docs/standards/coding-standards.md`
- AgentSON OKF reference digest: `spec/okf-digest.md` (to be revalidated against the upstream repository before further claims are made)
- Google Cloud Platform knowledge-catalogue repository: https://github.com/GoogleCloudPlatform/knowledge-catalog

**Review trigger:** Revisit this ADR when the platform has an implemented ingestion/indexing service, when a production deployment target is selected, or when upstream OKF changes materially affect interoperability.

## 10. Scoped standards assessment: AgentSON Severity v1

The Severity v1 deliverable on `feat/severity-v1` was assessed against the GOV.UK API Technical and Data Standards and the Technology Code of Practice (TCoP). This is a **data-contract assessment**, not an API-service assessment. The deliverable consists of `SEVERITY.md`, a Pydantic model, a JSON Schema 2020-12 document, package metadata and tests. It does not expose an HTTP endpoint.

That scope distinction is mandatory. Requirements for REST resource design, OpenAPI, HTTPS/TLS, OAuth, API sandbox services and API endpoint versioning cannot be marked as failures of a deliverable with no HTTP API surface. Where a later AgentSON Platform API exposes this contract, those requirements must be assessed against that API separately.

### 10.1 GDS API Technical and Data Standards — scoped result

| Requirement | Result for Severity v1 | Evidence / qualification |
|---|---|---|
| REST API style | Not applicable | No HTTP API surface exists. |
| OpenAPI specification | Not applicable | The deliverable publishes JSON Schema 2020-12, not an API description. |
| UTF-8 | Met | Source and tests open JSON files with UTF-8; JSON interchange is Unicode. |
| JSON response formats | Scope-qualified | JSON is the contract/document format. There are no HTTP responses to assess. |
| Consistent resource naming | Met within the contract | Stable severity and priority identifiers and consistent field naming; this does not establish REST resource naming. |
| ISO 8601 date/time | Partially met | `assessed_at` is described and generated as ISO 8601 UTC, but the schema uses a plain string without `format: date-time`. |
| Input validation / unknown attributes | Partially met | Required fields and enumerations are validated, but unknown properties are not explicitly rejected by the schema or Pydantic configuration. |
| Versioning / older versions | Partially met | `schema_version: agentson.severity.v1` and the schema path version the data contract. URI versioning and API backward-compatibility policy are not applicable until an API exists. |
| HTTPS / TLS 1.2+ / OAuth 2.0 | Not applicable | No hosted endpoint or transport layer is part of this deliverable. |
| Access control / authentication | Not applicable at contract layer | The schema does not authenticate consumers. A service that stores or serves assessments must implement access control. |
| Sensitive-data access logging | Partially met, with boundary | Assessment provenance records who/what assessed a finding and when. It does not record who later accessed the assessment or evidence. |
| API test service / sandbox | Not applicable | No runtime API is supplied. Contract fixtures and validation tests are the relevant current test mechanism. |
| API documentation | Scope-qualified | `SEVERITY.md` documents the data contract; it is not API endpoint documentation. |
| User needs / iteration | Not met in inspected evidence | Consumer groups and their needs are not documented as research or validated requirements. |
| Check for existing APIs | Not assessed | No evidence of a cross-government API catalogue review was included in this deliverable. |
| Data Standards Catalogue / TCoP mapping | Partially met | Uses open JSON/JSON Schema and ISO 8601 intent, but does not provide an explicit standards-catalogue mapping. |

### 10.2 Technology Code of Practice — scoped result

| TCoP point | Result for Severity v1 | Evidence / qualification |
|---|---|---|
| 1. Define user needs | Not met | No documented user-needs research for the severity contract. |
| 2. Make things accessible and inclusive | Partially met | Markdown is human-readable; no accessibility or plain-language review is evidenced. |
| 3. Be open and use open source | Met | Package metadata declares Apache-2.0. |
| 4. Make use of open standards | Partially met | JSON, JSON Schema 2020-12 and ISO 8601 intent are present; no OpenAPI is required for a non-API contract. |
| 5. Use cloud first | Not applicable to this deliverable | No deployment or hosting component is in scope. Reassess at platform/service level. |
| 6. Make things secure | Partially met | Assessment method and human override concepts are represented; no formal threat model or complete input-hardening policy is evidenced. TLS is outside this schema's scope. |
| 7. Make privacy integral | Partially met | Evidence references are read-only, but excerpts can contain personal data and pseudonymisation is not required by the contract. |
| 8. Share, reuse and collaborate | Partially met | Apache-2.0 supports reuse; cross-government reuse discovery is not evidenced. |
| 9. Integrate and adapt technology | Not applicable to this deliverable | No integration with government systems is claimed. |
| 10. Make better use of data | Partially met | Separating severity, priority and confidence improves structured interpretation; data quality and lineage controls remain limited. |
| 11. Define your purchasing strategy | Not applicable | No procurement decision is part of this schema deliverable. |
| 12. Make your technology sustainable | Not applicable to this deliverable | No operational hosting or environmental claim is in scope. |
| 13. Meet the Service Standard | Not applicable | This is a data specification, not a public-facing government service. |

### 10.3 Corrective actions for Severity v1

1. **Document consumers and user needs.** Add a concise section to `SEVERITY.md` identifying CLI users, report readers and platform analysts, the decisions they need to make, and the problems the contract is intended to solve. Distinguish evidenced user research from maintainer assumptions.
2. **Enforce timestamp semantics.** Add `format: date-time` to `assessed_at` in the JSON Schema and enforce timezone-aware ISO 8601 timestamps in Pydantic. Add positive and negative fixtures. Confirm the chosen JSON Schema validator checks format assertions rather than merely recognising the keyword.
3. **Decide unknown-field policy explicitly.** If forward-compatible extension is not intended in v1, configure Pydantic with `extra="forbid"` and set `additionalProperties: false` at the top level and in every object definition. Add parity tests proving both validators reject the same unknown properties. Treat this as a contract-tightening change and review compatibility before merging; do not silently make it a breaking change.
4. **State the interface boundary.** In `SEVERITY.md`, explicitly say this is a JSON Schema/Pydantic data contract, not a REST API or OpenAPI description. If a REST API is introduced later, publish a separate OpenAPI document and assess the API against the relevant GDS requirements.
5. **Separate assessment provenance from access audit.** Keep `assessed_by`, `assessed_at`, `method`, `rule_id`, evidence references and overrides as provenance of the assessment. Record reads, exports and administrative access in the service/platform audit layer, where identity and access events actually occur.
6. **Address privacy in evidence excerpts.** Define whether excerpts are optional, redacted, pseudonymised or excluded by default, and add tests for the selected policy.

### 10.4 Reasoning correction and decision boundary

The standards review must not turn into a checklist exercise where every GDS API requirement is forced onto every JSON document. The correct method is:

- identify the artefact and its actual interface;
- determine which requirement applies to that artefact;
- assess the evidence at that boundary;
- mark genuinely out-of-scope requirements as not applicable, not as failed;
- carry service-level requirements forward to the service that will expose or process the contract.

This is the same layer-boundary discipline adopted in this ADR's Core/Platform decision. It also corrects the earlier production-readiness assessment, which referred too broadly to API and service controls without always distinguishing the severity data contract from the future platform API.

The Severity v1 findings above are scoped to the reviewed `feat/severity-v1` deliverable. They do not certify a later API or the AgentSON Platform as GDS-compliant.

