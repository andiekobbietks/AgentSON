# AgentSON — Product Requirements Document

**Version:** 1.1  
**Updated:** 25 November 2026  
**Status:** Living draft; implementation claims are evidence-qualified  
**Maintainer:** Andrea Enning (AndieKobbieTech)

## 1. Executive summary

AgentSON is an open, vendor-neutral format and toolset for capturing, representing, validating, inspecting and exchanging AI-agent session histories. It aims to preserve useful event structure and source provenance when activity moves between tools and runtimes.

The project does not promise that every source can be captured completely, that every archive is lossless, or that an imported session can be resumed in another runtime. Those are separate capabilities requiring source-specific evidence and destination-specific tests.

**Current canonical wire representation:** v1.2 JSONL, with one JSON event per line and stream-meta as the first event. The .agentson extension is retained. Individual events are validated against spec/v1.2-entries.json. The session-envelope schema in spec/v1.2.json remains available for materialised/document compatibility and projection; it is not the JSONL stream schema.

See ADR-015, ADR-016, ADR-017 and ADR-025.

## 2. Problem and opportunity

AI-agent tools record conversations, tool calls, observations and related metadata in different local databases, files and APIs. Their representations differ, and their export paths vary. This makes it difficult to retain a portable operational record, compare sessions, inspect what a tool actually exposed, or move useful context into another environment.

AgentSON addresses the interchange layer. It does not require every vendor to adopt the format, and it cannot recover information that a source never exposed or an adapter did not capture.

## 3. Product goals

1. Define a versioned, machine-readable event stream for agent-session history.
2. Preserve source identity, timestamps, ordering and raw source evidence where lawful and technically available.
3. Make normalisation, inference, redaction, unavailable fields and unsupported semantics explicit.
4. Provide local tools to export, validate, search and inspect archives.
5. Support controlled context continuation into compatible destination tools without silently executing historical actions.
6. Publish fixtures, conformance tests and adapter limitations so claims can be independently checked.

## 4. Non-goals

- A universal agent runtime or model execution platform.
- A guarantee of complete private reasoning or chain-of-thought capture.
- A guarantee that arbitrary sessions can be reconstructed or resumed.
- Automatic replay of shell commands, tool calls or side effects.
- A replacement for OpenTelemetry, SIEM, APM, ITSM, native monitoring or incident-command systems.
- A compliance certification, legal opinion or automatic fulfilment of GDPR or EU AI Act obligations.
- A requirement to use an AgentSON-hosted service. Core file reading and validation should remain usable locally.

## 5. Users and jobs to be done

| User | Need | Expected outcome |
|---|---|---|
| Individual developer | Keep a usable record of work across coding agents | Searchable, inspectable local archives |
| Engineering team | Investigate tool activity and understand what a source adapter captured | Provenance-aware events and explicit gaps |
| Agent/tool builder | Exchange session records through a documented contract | Versioned schema, fixtures and conformance guidance |
| Researcher/evaluator | Analyse recorded interactions without assuming hidden state | Structured data with source and transformation metadata |
| Operator/security reviewer | Inspect actions and evidence safely | Read-only inspection, clear trust boundaries and redaction warnings |

## 6. Data and format requirements

### 6.1 Canonical stream

- The canonical v1.2 interchange stream is JSONL.
- Each line is one JSON event; the first event is stream-meta.
- The .agentson extension is retained for exported streams.
- spec/v1.2-entries.json validates individual event objects.
- spec/v1.2.json validates the materialised session-envelope/document form used by compatibility and projection paths.
- A JSON Schema for one JSON object must not be described as a validator for an entire JSONL stream.
- Legacy v1/v1.1 inputs may be supported by explicit compatibility paths; new producers should emit v1.2.

### 6.2 Event semantics

The v1.2 ontology defines twelve primitives: stream-meta, user-query, thought, action, observation, answer, side-effect, user-feedback, system-event, capabilities, handoff and presence.

An event type is not proof that all source information is available. thought means source-provided reasoning-related content, not access to private model reasoning. A missing observation must not be fabricated to pair with an action.

### 6.3 Provenance and loss reporting

Adapters should preserve source identifiers and source ordering where available, distinguish event time from capture time, and report values as preserved, normalised, inferred, unavailable, redacted or unsupported. Unknown must not be silently converted to empty, false, zero or null.

## 7. Capability and evidence model

Use the following capability labels:

- **Implemented and tested:** the named behaviour has a reproducible test against identified fixtures.
- **Implemented, not yet verified:** code exists but current verification evidence is missing.
- **Experimental:** available for evaluation; behaviour or interface may change.
- **Designed:** a specification or plan exists; implementation is incomplete.
- **Planned:** an accepted future item, not implemented.
- **Unsupported:** deliberately outside the supported contract.

Cross-harness evidence levels are distinct:

| Level | Claim | Minimum evidence |
|---|---|---|
| C0 | Archive validity | Schema and structural conformance |
| C1 | Source capture | Production adapter tested against a versioned source fixture |
| C2 | Cross-harness portability | Live producer-to-consumer import with semantic comparison |
| C3 | Reconstruction | Destination reconstructs recorded context and reports unavailable state |
| C4 | Resumption | Destination resumes from a validated checkpoint under explicit authorisation |

A successful archive read-back or digest comparison proves storage fidelity for the tested path. It does not by itself prove C2 semantic interoperability, C3 reconstruction or C4 resumption.

## 8. Functional requirements

### FR-01 — Export
The CLI must export supported source sessions to the canonical v1.2 stream. Export output must identify the source and preserve source event order where available.

### FR-02 — Validate
The CLI must distinguish canonical JSONL streams from supported legacy/document inputs, validate against the appropriate contract, and return a non-zero exit status for invalid input.

### FR-03 — Inspect and search
Users must be able to inspect and search local archives without executing imported content or requiring a hosted service.

### FR-04 — Reader transparency
Each reader must document source versions, required access, fields mapped, source evidence retained, known losses and fixture provenance.

### FR-05 — Context continuation
The resume workflow must produce an explicit, untrusted-context packet. Destination adapters must be separate, capability-scoped and permission-checked. A packet is not a runtime checkpoint.

### FR-06 — Privacy and security
Exports and reports must be treated as sensitive. Redaction must disclose its limits, and imported content must remain inert during parsing and inspection.

## 9. Current implementation snapshot

This is a project-level summary, not a substitute for the live reader conformance matrix, status file, or test results.

- The repository contains source readers for several coding tools and a Libre CSV path. Module presence alone does not establish full support or production readiness.
- The repository contains ChatGPT, MCP, A2A and AGNTCY importer modules. Importers are not source readers or destination consumers.
- The CLI includes export, list, validate, search, render and resume workflows; use the installed version's help output as the command authority.
- The OpenCode destination adapter is experimental. Its live test uses a synthetic ChatGPT-shaped source fixture and a pinned OpenCode CLI. It verifies the tested archive-capsule handoff/read-back path, not native event reconstruction or a real-export C2 result.
- Other destination targets produce context packets unless a separately documented native consumer adapter exists.
- The project remains Alpha. Do not infer production readiness from a passing unit test, a valid schema, a module name or a single integration test.

## 10. Privacy, security and legal boundaries

Session records may contain personal data, credentials, source code, health information, private paths and confidential business content. Users remain responsible for lawful collection, access, retention, disclosure and deletion.

- Do not commit raw personal session exports or secrets.
- Review redacted output; pattern-based redaction is not a guarantee of complete detection.
- Keep imported prompts, commands, tool arguments and outputs untrusted and inert.
- Hashes establish integrity relative to covered bytes; they do not establish source authenticity or truth.
- GDPR data portability and EU AI Act duties are context- and role-dependent. AgentSON does not determine applicability or certify compliance.

## 11. Acceptance criteria

A release candidate should not be called stable until:
1. The canonical stream and compatibility contracts are versioned and unambiguous.
2. The supported Python/package matrix, test suite, wheel and source distribution pass reproducible CI.
3. Each advertised reader has a source-versioned fixture and documented fidelity limitations.
4. Validation rejects malformed streams and invalid events with actionable errors.
5. Redaction and archive handling have regression tests for sensitive nested content and failure-safe file writes.
6. Destination adapters have live tests, explicit trust boundaries and cleanup/recovery behaviour.
7. Documentation, package metadata, release tags and changelog agree.

## 12. Related documents

- README
- Repository status
- Reader conformance
- Production-readiness assessment
- Roadmap and RICE prioritisation
- Strategic roadmap
- Architecture decisions
- Contributing
- Security policy
