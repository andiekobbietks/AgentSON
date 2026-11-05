# AgentSON Production-Readiness Assessment

**Assessment date:** 05 November 2026  
**Baseline:** `master` at `ceef4e83baab2a9eb1a59e6f15fc8c62dbeec70a`  
**Purpose:** Establish an evidence-led gap analysis against an independently operable, production-grade open-source format and catalogue platform.  
**Status:** Initial repository inspection; not a certification, penetration test or independent security audit.

## Executive assessment

AgentSON has meaningful foundations: a versioned JSONL format, readers/importers, a CLI, local scanning/classification/reporting, evidence export and a growing test corpus. The current repository does **not** yet demonstrate a production-grade, multi-tenant knowledge-catalogue service.

The correct comparison has two axes:

- **Core format:** interoperability, schema stability, provenance, portability, conformance and independent implementations.
- **Platform service:** ingestion, indexing, search, identity, authorisation, tenant isolation, policy, audit, resilience and operations.

The project should not claim the second because it has made progress on the first.

## 1. Evidence and scope

This assessment inspected the default-branch tree and selected files, including:

- `README.md`, `AGENTS.md`, `STATUS.md`, `ROADMAP.md`
- `pyproject.toml`, `MANIFEST.in`
- `agentson_platform/crawler.py`, `scan.py`, `server.py`, `report.py`, `netdoctor.py`
- `docs/standards/coding-standards.md`, `spec/okf-digest.md`
- GitHub Actions workflow paths in the default-branch tree
- Open PR #58 (severity v1) and its stated verification

The repository inspection did not execute code, build distributions, run tests, inspect live infrastructure, conduct a penetration test or verify GitHub branch-protection settings. Findings below distinguish observed facts from questions requiring runtime verification.

## 2. Current capability map

| Capability | Observed evidence | Assessment |
|---|---|---|
| Canonical event representation | JSONL and versioned schema documented; ADR-015/016/017 | Foundation present; needs continuous conformance tests |
| Reader/importer ecosystem | Multiple reader and importer packages | Foundation present; real-export regression coverage and compatibility matrix needed |
| Local validation and CLI | CLI and schema tooling in repository | Needs installed-package and cross-version verification |
| Local scan pipeline | Crawler → classifier → report in `agentson_platform/` | Useful local workflow; not a hosted catalogue |
| Evidence export | Report and evidence export paths documented | Needs cryptographic lifecycle, access and retention review |
| Catalogue search/index | Structure/graph exports exist | No evidence yet of a durable, queryable, access-controlled catalogue service |
| REST/MCP service surface | Local server and MCP-related work exist | Contract and service maturity need separate verification |
| Multi-tenancy | No tenant isolation model evidenced in inspected files | Not demonstrated |
| Identity/access control | No production identity/authorisation model evidenced in inspected files | Not demonstrated |
| Operations | Local network diagnostics and runbook material | No demonstrated SLO, backup/restore exercise, incident process or production deployment |
| CI/release engineering | README CI badge points to `.github/workflows/ci.yml`; no such file exists in the default-branch tree | P0 gap |
| Security governance | Apache-2.0 licence exists; no root `SECURITY.md`, `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md` in baseline tree | P1 gap |

## 3. Prioritised findings

### P0 — Release integrity and reproducibility

**P0.1 — No authoritative CI workflow is present on the baseline branch.**

Evidence: the default-branch tree contains `.github/workflows/adr-viewer.yml` and its helper assets, but no `.github/workflows/ci.yml`. The README badge points to `actions/workflows/ci.yml`.

Impact: contributors and maintainers cannot rely on the repository itself to reproduce the reported test/build status on each pull request.

Required action:
- Add pull-request and push CI.
- Run the supported Python matrix, tests and package build.
- Install the built wheel in a clean environment and smoke-test the public CLI.
- Publish the test/build result as a required status check after the repository settings are reviewed.

**P0.2 — Version claims disagree.**

Evidence: README heading identifies v1.2.0, while its warning calls the project Alpha/pre-release. `pyproject.toml` declares version 0.1.0 and the Alpha development-status classifier.

Impact: package consumers, release automation and documentation can infer different release states.

Required action: choose one authoritative release version and define the relationship between format version, Python package version and platform version. Do not change the package version until the release/tag history and PyPI publication are reconciled.

**P0.3 — Distribution contents are not proven.**

Evidence: `pyproject.toml` lists only `spec/v1.json` under `spec` package data; `MANIFEST.in` also explicitly includes only `spec/v1.json`. The repository documents additional schemas and examples.

Impact: a source checkout may work while a wheel or sdist omits files required by installed users.

Required action: build wheel and sdist, inspect their contents, install the wheel outside the repository and test schema/resource discovery. Add a package-data manifest test before changing inclusion patterns.

### P1 — Trust, security and data protection

**P1.1 — Reports can contain sensitive source values.**

Evidence: `agentson_platform/report.py` explicitly states that generated reports contain the sensitive values the scanner finds and must be handled like the source sessions.

Impact: a report directory, exported evidence package or dashboard can become a second store of credentials, personal data, source paths and confidential prompts.

Required action:
- Define data classes and default storage permissions.
- Redact or tokenise secrets in general-purpose reports; provide a separate controlled evidence path when original values are essential.
- Document encryption at rest/in transit, retention, deletion, backup and export controls.
- Add tests proving redaction and access boundaries.
- Never upload real user session data to CI fixtures or third-party review services.

**P1.2 — Security disclosure and contributor governance are incomplete.**

Evidence: no root-level `SECURITY.md`, `CONTRIBUTING.md` or `CODE_OF_CONDUCT.md` appeared in the baseline tree.

Required action: publish a private vulnerability-reporting route, response expectations, contribution checks and community standards.

**P1.3 — Dependency and supply-chain assurance is not yet a release gate.**

Required action: dependency update automation, vulnerability audit, secret scanning, SBOM generation and build provenance. Adopt thresholds and exception handling rather than adding a scanner that fails unpredictably without triage.

### P2 — Platform architecture

**P2.1 — The current platform is a local scan/report workflow, not a complete catalogue service.**

Evidence: `crawler.py`, `scan.py` and `report.py` implement local discovery, classification and report generation. `server.py` describes itself as a local playground server.

Required action: define service boundaries for ingestion, evidence storage, indexing, graph relationships, search, policy, APIs and user interfaces. Keep the existing local workflow useful without requiring the service.

**P2.2 — Identity, authorisation and tenant isolation are not demonstrated.**

Required action: threat-model tenant boundaries; define user, service and workload identities; enforce least privilege on every API and data access path; test cross-tenant isolation; record administrative and evidence-access events.

**P2.3 — Durability and recovery are not demonstrated.**

Required action: define storage guarantees, idempotent ingestion, replay/reconciliation, backup, restore, retention, disaster recovery and migration strategy. Test restore rather than treating a configured backup as proof.

### P3 — Reliability and ecosystem

- Define service SLOs and error budgets for any hosted service.
- Add health/readiness endpoints, structured logs, metrics and trace correlation.
- Document deployment, upgrade, rollback and incident runbooks.
- Version REST/MCP/SDK contracts and publish compatibility guarantees.
- Build a conformance suite and an independent reference consumer.
- Make catalogue indexes rebuildable from retained source evidence where policy permits.

## 4. Target architecture

```text
Runtime adapters / batch import / API / MCP
                  |
          Ingestion boundary
                  |
      Validate, normalise, attest
                  |
       Source evidence repository
                  |
       Index + relationship graph
                  |
      Search + catalogue query API
                  |
       Identity + policy enforcement
                  |
      REST / MCP / CLI / UI / SDK
                  |
       Human and agent consumers
```

Core owns the portable event contract and local tools. Platform owns service operations and governance. A platform index is a derived view, not a replacement for the source evidence.

## 5. Implementation roadmap and exit criteria

| Priority | Work package | Exit criteria |
|---|---|---|
| P0 | CI and package integrity | PR CI green on supported Python versions; tests/build/wheel smoke pass; schema assets verified |
| P0 | Version and release reconciliation | README, pyproject, tags, changelog and published package agree |
| P1 | Security baseline | SECURITY.md, threat model, secret/dependency scanning, SBOM and vulnerability process |
| P1 | Sensitive evidence handling | Redaction, encryption, retention/deletion and export policy tested |
| P2 | Catalogue service MVP | Durable ingestion, indexing, query API, lineage and service-level tests |
| P2 | Identity and tenancy | Authentication, authorisation, tenant isolation and audit verified by negative tests |
| P3 | Operations | SLOs, monitoring, backup/restore, rollback and incident exercises |
| P3 | Ecosystem | Public conformance suite, SDK/API docs and independent consumer |

## 6. Open decisions (do not silently assume)

1. Which deployment target is authoritative: self-hosted single organisation, self-hosted multi-tenant, or managed service?
2. Which data stores are permitted, and what are the retention and deletion guarantees?
3. What are the target workload and SLOs (events/day, ingest latency, query latency, tenant count, availability)?
4. Which identity standards and integrations are required?
5. Which evidence may be indexed, redacted, retained or exported under each customer policy?
6. Which features remain in Apache-2.0 Core, and which belong to separately licensed Platform modules?

These are architectural inputs, not reasons to block the initial CI and documentation foundation.

## 7. Verification ledger

| Claim | Evidence available | Confidence | Next verification |
|---|---|---:|---|
| No `ci.yml` on baseline | Default-branch Git tree | High | CI workflow should appear in this PR |
| README/package version mismatch | README and pyproject contents | High | Reconcile tags and PyPI metadata |
| Package data may be incomplete | pyproject and MANIFEST.in | High for declared patterns; runtime impact untested | Inspect wheel/sdist and clean install |
| Reports contain sensitive values | report.py documentation | High | Test actual output and redaction behaviour |
| Local scan path exists | crawler/scan/report modules | High for code presence; runtime not executed | Run fixtures and integration tests |
| Platform is not yet proven multi-tenant | No tenancy model found in inspected baseline | Medium | Full code/security review and architecture decision |
| No production SLO/recovery evidence | No evidence found in inspected baseline | Medium | Review deployment environment and operational records |

## 8. What this assessment does not claim

- It does not say AgentSON is unusable. The local format, CLI, readers and scan workflow have real value.
- It does not say Google OKF itself supplies catalogue infrastructure.
- It does not certify security or regulatory compliance.
- It does not treat a passing unit-test count as proof of production readiness.
- It does not mark a roadmap item complete merely because a design or runbook exists.

The objective is to make every readiness claim traceable to code, tests, configuration or operational evidence.
