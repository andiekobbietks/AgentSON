# AgentSON Roadmap

**Status:** Proposed product and engineering roadmap  
**Last updated:** 25 November 2026  
**Current canonical schema:** v1.2  
**Implementation status:** The capabilities below are proposals unless explicitly marked as existing in the repository.

> This document expands AgentSON's strategic and engineering direction. It complements [ROADMAP.md](ROADMAP.md), which retains the existing RICE-scored reader-priority matrix. It does not replace the project overview in [README.md](README.md).

## 1. Product direction

AgentSON is an open, vendor-neutral format and tooling layer for preserving, correlating and exchanging operational execution evidence.

The current project focuses on AI-agent sessions: capturing activity from supported runtimes and preserving it in portable `.AgentSON` records. The next architectural step is to make the event model useful across a wider operational environment, where work is performed by:

- AI agents and multi-agent workflows;
- human engineers and service operators;
- applications, services and infrastructure components;
- monitoring, deployment, identity and automation systems.

The intended outcome is a coherent, portable operational history connecting observations, hypotheses, decisions, approvals, actions, changes and outcomes across tools and providers.

**AgentSON is not intended to replace** Azure Monitor, Application Insights, Log Analytics, Microsoft Sentinel, OpenTelemetry, ITSM platforms, agent frameworks or incident-command processes. It should interoperate with those systems and preserve useful evidence across their boundaries.

> Preserve what happened, who or what did it, what it affected, why the action was taken, what evidence supports the record, and what happened next — independently of the platform that produced the event.

## 2. Why the roadmap is expanding

### November 2026 Microsoft 365 incident

The Microsoft 365 / Exchange Online outage of 12–13 November 2026 is a motivating operational case study.

Reuters reported on 24 November that internal Microsoft memos described responders exchanging more than 11,000 messages across 11 Teams chats while struggling to maintain a cohesive picture of hypotheses and decisions because diagnostic information was spread across internal tracking systems. The reporting also described Microsoft's subsequent Code Red response.

This is **not evidence that Microsoft lacks observability or incident-management tooling**. Microsoft has extensive monitoring, diagnostics, service-health, security and engineering systems. Nor does the reporting establish that a new event format alone would have prevented the outage.

The product question is narrower:

**Can AgentSON help organisations assemble a trustworthy, correlated and portable operational record from evidence already produced by their agents, people, services and infrastructure?**

Such a record could help responders reconstruct:
- what was observed, and by which system;
- which hypotheses were raised, changed or ruled out;
- which decisions were made, by whom and when;
- which approvals or overrides were given;
- which automated or manual actions were attempted;
- which services, resources and dependencies were affected;
- what changed during mitigation and recovery;
- what evidence supports the reported outcome.

The outage is a design motivation and validation scenario, not evidence of customer endorsement, product-market fit or a proven gap in Microsoft's product portfolio.

**Context and reporting**
- [Reuters: Microsoft declares 'Code Red' after historic outage, internal memos show (24 November 2026)](https://www.reuters.com/business/microsoft-declares-code-red-after-historic-outage-internal-memos-show-2026-11-24/)
- [Microsoft 365 outage: post-incident reporting and technical context](https://www.bleepingcomputer.com/news/microsoft/microsoft-says-months-old-bug-caused-global-microsoft-365-outage/)

## 3. Scope and boundaries

### In scope

1. Portable records of agent execution and tool interactions.
2. A common event envelope for human, agent, service and infrastructure actors.
3. Correlation of events from multiple systems while retaining original identifiers and provenance.
4. Import and export adapters for established telemetry and operational systems.
5. Incident timelines connecting observations, hypotheses, decisions, approvals, actions and outcomes.
6. Evidence integrity, access control, redaction, retention and audit-oriented workflows.
7. Optional integration with AKTCloud for infrastructure dependency and recovery-assurance workflows.

### Out of scope

- Replacing native monitoring, alerting, SIEM, APM or ITSM products.
- Replacing Microsoft Agent Framework, Copilot Studio, Foundry Agent Service or other agent runtimes.
- Becoming a general-purpose incident-command SaaS platform by default.
- Claiming that a log or trace proves an event was complete, correct or authorised.
- Capturing every Teams message, prompt, tool argument or infrastructure event indiscriminately.
- Claiming regulatory compliance or certification solely because data is exported to AgentSON.
- Executing production remediation without explicit integrations, policy controls and operator authorisation.

## 4. Architecture principles

### 4.1 Preserve the current format; extend deliberately

The v1.2 schema is the current canonical schema. Do not silently redefine existing entry types or make existing files invalid.

First produce a schema-gap analysis and compatibility proposal. Prefer additive, optional fields where they preserve v1.2 semantics. If the required actor, resource, causality or evidence model cannot be added safely, introduce a separately versioned schema with migration guidance rather than forcing a breaking change into v1.2.

### 4.2 One event model, multiple actor types

The event model should distinguish the actor from the event:

| Dimension | Proposed values / examples |
|---|---|
| Actor type | `human`, `ai_agent`, `service`, `system`, `device` |
| Event kind | observation, hypothesis, decision, approval, action, change, handoff, outcome |
| Resource | service, host, cluster, network path, deployment, identity, API, dataset |
| Correlation | incident ID, trace ID, span ID, workflow ID, parent event ID |
| Provenance | source system, adapter/version, original event ID, collection time |
| Evidence | references to logs, metrics, traces, change records or artifacts, with integrity metadata |

These are design candidates, not a declaration that all fields or event kinds are already supported by v1.2.

### 4.3 Preserve source truth

- Retain original source IDs, timestamps, trace/span IDs and relevant attributes.
- Distinguish event time from ingestion time; preserve clock and timestamp uncertainty where known.
- Record the adapter and transformation version.
- Make lossy mappings explicit.
- Do not turn inferred relationships into facts.
- Represent missing or unavailable evidence honestly.
- Support deduplication and late-arriving events without silently rewriting history.

### 4.4 Evidence integrity and privacy by design

Investigate append-only storage patterns, content digests, signed checkpoints or manifests, and verifiable export bundles. A hash alone does not prove who created an event or whether the source was truthful; identity, key management, access control and collection provenance remain necessary.

Provide data minimisation, configurable redaction, secret detection, access controls, retention and deletion policies. Prompts, chat messages, tool arguments, telemetry and infrastructure identifiers may contain personal or confidential information.

## 5. Roadmap workstreams

### A — Agent interoperability (continue existing core)

**Objective:** Preserve AgentSON's existing value as a portable record of AI-agent execution.

- Maintain and improve current readers and importers.
- Expand coverage for relevant coding agents and agent frameworks using supported interfaces.
- Improve fidelity tests for prompts, actions, observations, tool results, handoffs, errors and outcomes.
- Document what each reader can and cannot capture.
- Preserve source provenance and disclose unsupported or lossy fields.
- Keep replay and fine-tuning exports separate from claims about complete runtime capture.

**Exit criteria:** Each supported reader has fixtures, compatibility tests, documented limitations and a reproducible validation path.

### B — OpenTelemetry interoperability

**Objective:** Consume and correlate standard telemetry rather than invent a replacement tracing ecosystem.

- Define mappings from OpenTelemetry traces, spans, events and resource attributes.
- Preserve trace IDs, span IDs, parent relationships, timestamps and source attributes.
- Build a read-only OTLP or supported export-path proof of concept.
- Test partial traces, retries, clock skew, duplicate events and missing attributes.
- Define how telemetry references link to richer AgentSON operational events.
- Document that OpenTelemetry only captures what the source instrumented and emitted.

**Exit criteria:** A reproducible adapter imports representative telemetry into validated AgentSON output while preserving original identifiers and documenting transformation loss.

### C — Human and operational actors

**Objective:** Represent human operators and ordinary services alongside AI agents.

- Define actor identity and actor-type semantics.
- Model observations, hypotheses, decisions, approvals, actions, changes and outcomes.
- Represent delegation and handoffs between people, agents and services.
- Link events to services, infrastructure resources and configuration items.
- Distinguish an action being proposed, approved, attempted, completed, failed or independently verified.
- Define identity references without copying credentials or unnecessary personal data.

**Exit criteria:** A schema proposal and sample dataset represent a human engineer, an AI agent, an automation service and an infrastructure event in one correlated workflow without misrepresenting their authority or provenance.

### D — Incident reconstruction and coordination

**Objective:** Produce a useful, evidence-backed incident history.

- Introduce an incident/workflow correlation model.
- Link alerts and observations to hypotheses and investigation steps.
- Record hypothesis status and the evidence supporting or contradicting it.
- Record decisions, decision owners, approvals, timestamps and rationale where available.
- Link mitigation actions, configuration changes, rollbacks and recovery checks.
- Produce a chronological incident timeline and machine-readable evidence bundle.
- Support multiple teams and systems without requiring all collaboration to happen inside AgentSON.
- Investigate ITSM and collaboration connectors using documented APIs and explicit permissions.

**Exit criteria:** A synthetic multi-team incident can be reconstructed from events emitted by at least two independent source systems, with provenance, gaps and inferred relationships clearly distinguished.

### E — Microsoft ecosystem interoperability

**Objective:** Work alongside Microsoft's existing agent, observability and operations products.

Potential integration targets:
- Microsoft Agent Framework;
- Microsoft Foundry Agent Service;
- Microsoft Copilot Studio;
- Microsoft Agent 365 where supported interfaces are available;
- Azure Monitor and Application Insights;
- Log Analytics and Microsoft Sentinel;
- Microsoft Teams / Microsoft Graph for explicitly authorised collaboration records.

Implementation rules:
- Prefer OpenTelemetry, documented SDK middleware, supported APIs, export mechanisms and webhooks.
- Do not assume every product exposes every event or supports arbitrary OTLP export.
- Do not scrape private databases or depend on undocumented internals.
- Respect tenant permissions, data residency, retention, licensing and administrative consent.
- Keep native Microsoft monitoring and governance controls in place.
- Treat Microsoft integrations as adapters, not dependencies of the AgentSON format.

**Exit criteria:** At least one documented Microsoft integration proof of concept imports a supported event or trace source into AgentSON, with a permission model, field mapping, test fixtures and known limitations.

### F — Cross-provider operations

**Objective:** Correlate operational evidence across a customer's technology estate.

Candidate source families:
- cloud-provider monitoring and audit events;
- application performance and distributed tracing;
- network, DNS, identity and endpoint systems;
- CI/CD, deployment and change-management platforms;
- ITSM incident, problem and change records;
- agent frameworks, tool gateways and automation platforms.

Prioritise integrations based on user interviews and accessible supported interfaces, not the number of logos on a compatibility list.

**Exit criteria:** A demonstration correlates a single incident across at least two providers or independent platforms without discarding source provenance.

### G — Recovery evidence and AKTCloud integration

**Objective:** Support operational resilience assessment without turning AgentSON into an unqualified recovery product.

- Record recovery objectives and the source of those objectives.
- Capture backup, restore, failover and rollback test events where integrations permit.
- Link recovery actions to approvals, affected resources and verification results.
- Distinguish a documented plan from an implemented control and a successfully tested recovery.
- Export evidence bundles for customer review and assurance.
- Keep AKTCloud provisioning and managed-service responsibilities separate from AgentSON's open event format.

**Exit criteria:** A controlled demonstration records a recovery test from initiation through verification, including failed checks and unresolved gaps.

## 6. Delivery sequence and gates

The sequence below is a proposed order, not a committed release schedule.

| Phase | Focus | Deliverables | Gate |
|---|---|---|---|
| 0 | Requirements and schema review | Incident use cases, actor model, schema-gap analysis, threat/privacy review | No breaking change without a versioning decision |
| 1 | Telemetry foundation | OpenTelemetry mapping, fixtures, read-only adapter prototype | Source IDs and trace relationships preserved |
| 2 | Actor and event model | Human/service/system actor proposal, decisions, approvals and outcomes | Backward-compatibility tests pass |
| 3 | Incident reconstruction | Correlation model, timeline export, evidence bundle | Multi-source synthetic incident reconstructs correctly |
| 4 | Microsoft integration | One supported Microsoft source adapter and documented permissions | Demonstrated with real supported interfaces |
| 5 | Cross-provider integrations | Second provider/platform adapter, correlation tests | Cross-platform evidence remains portable |
| 6 | Recovery assurance | Recovery-test event model and AKTCloud integration proof of concept | Tested recovery is distinguishable from an untested plan |
| 7 | Hardening and adoption | Security review, retention guidance, documentation, SDK stability | Independent users can integrate and validate records |

Do not assign release numbers or delivery dates until schema review, implementation effort and user validation have been completed.

## 7. Validation scenarios

Use reproducible synthetic scenarios before handling production incident data.

1. **Agent tool failure:** an agent calls a tool, receives an error, retries and hands off to a human.
2. **Human-approved change:** an engineer reviews a proposed change, approves it, and a deployment service executes it.
3. **Distributed service degradation:** telemetry from two services shares trace and incident correlation identifiers.
4. **Conflicting hypotheses:** two teams record competing explanations, evidence changes their status, and the final conclusion links to supporting records.
5. **Failover and recovery:** traffic is redirected, a capacity constraint is observed, recovery is attempted, and service health is independently checked.
6. **Partial evidence:** a source is unavailable or emits incomplete telemetry; the exported timeline marks the gap instead of implying completeness.
7. **Provider migration:** an event bundle is exported and validated without access to the original monitoring platform.

For each scenario test ordering, duplicate delivery, late events, clock skew, missing fields, provenance, redaction and access permissions.

## 8. Product success measures

Measure whether AgentSON improves the quality and portability of operational evidence, not vanity metrics alone.

| Measure | What it demonstrates |
|---|---|
| Source coverage | Number of documented, tested adapters and event families |
| Correlation fidelity | Known relationships correctly retained in controlled fixtures |
| Provenance completeness | Events retaining source IDs, source identity and transformation metadata |
| Reconstruction accuracy | Whether a reviewer can reproduce the known sequence from exported evidence |
| Evidence gap disclosure | Whether missing, delayed or unsupported events are clearly marked |
| Portability | Whether records validate and remain useful without the originating platform |
| Integration effort | Time and complexity required for a third party to produce valid events |
| Privacy and security | Results of redaction, access-control, retention and threat-model tests |

Set quantitative targets after baseline measurements and user research.

## 9. Risks and open questions

- **Schema scope:** Can the existing v1.2 envelope be extended additively, or is a new major schema version required?
- **Semantic mismatch:** How should an agent trace, human decision, monitoring alert and cloud audit event be represented without flattening their meaning?
- **Evidence completeness:** How will consumers know what a source did not capture?
- **Identity:** How can human and workload identity be referenced safely across tenants and providers?
- **Causality:** Which relationships are explicit source facts and which are inferred?
- **Time:** How should clock skew, event time, ingestion time and ordering uncertainty be represented?
- **Privacy:** What should be retained, redacted, encrypted or excluded by default?
- **Integrity:** Which threat model justifies signed manifests, append-only storage or external anchoring?
- **Interoperability:** Which OpenTelemetry and Microsoft interfaces are actually available for each target product and licence?
- **Market validation:** Do incident commanders, SRE teams and MSPs want an independent evidence layer, and will they pay to deploy and maintain it?

## 10. What AgentSON should not become

AgentSON should remain an open interoperability and evidence project. It should not become:
- a proprietary replacement for OpenTelemetry;
- a competing cloud monitoring suite;
- a replacement for Microsoft or third-party agent runtimes;
- a centralised repository that indiscriminately copies prompts and operational data;
- an automated incident commander making unreviewed production decisions;
- a compliance badge without evidence and independent assessment.

The durable value should come from a trustworthy event model, high-quality adapters, preserved provenance, useful correlation and portable evidence.

## 11. Relationship to the existing roadmap

- [`ROADMAP.md`](ROADMAP.md) retains the existing reader-priority matrix and RICE estimates.
- [`README.md`](README.md) remains the project overview, quick start and current implementation summary.
- `STRATEGIC_ROADMAP.md` is the expanded strategic and engineering roadmap.
- [`CHANGELOG.md`](CHANGELOG.md) remains the source for shipped release changes.
- Issues and pull requests remain the source of implementation status; roadmap proposals must not be presented as completed capabilities.

---

*This roadmap is a planning document. Proposed integrations, schema changes and product capabilities are not implemented merely because they appear here.*
