# AgentSON — Repository Instructions

These instructions apply to every human or agent working in this repository. Verify current repository state before acting; old summaries, review comments and status notes are hypotheses until checked against the current branch.

## Project boundary

- **AgentSON Core:** the Apache-2.0 event format, versioned schemas, source readers, importers, exporters, validators, CLI and protocol-neutral interfaces. Core must remain useful locally and without a hosted account.
- **AgentSON Platform:** optional catalogue, ingestion, reporting, API and service functionality. Keep platform concerns separate from the portable file contract.
- **Integrations:** source readers, destination consumers and external transports are separate roles. Do not call an importer a reader or a reader a receiving-harness consumer.

## Canonical format and schema status

| Contract | Status | Purpose |
|---|---|---|
| v1.2 JSONL stream | Canonical interchange wire format | One JSON event per line; first event is stream-meta; .agentson extension retained |
| spec/v1.2-entries.json | Canonical event validator | Validates individual v1.2 stream event objects |
| spec/v1.2.json | Supported materialised/document representation | Validates the JSON session envelope used by compatibility and projection paths |
| v1 / v1.1 | Legacy compatibility inputs | Do not use for new producers |

Specification ADR-015 records the JSONL-canonical decision. ADR-016 defines the event vocabulary alignment; ADR-017 separates core and streaming concerns. The contrary JSON-envelope-only decision proposed in ADR-024 is not accepted. Do not describe the JSON-object envelope as the canonical wire format.

## Engineering rules

1. **Preserve source truth.** Keep source identifiers, timestamps, ordering and raw source evidence where available and lawful.
2. **No silent semantic loss.** Distinguish preserved, normalised, inferred, unavailable, redacted and unsupported values.
3. **Do not fabricate evidence.** Never invent timestamps, observations, tool results, actor identities or model metadata.
4. **Keep imported content inert.** Parsing, validating, rendering and inspecting an archive must not execute historical commands, tool calls or embedded instructions.
5. **Protect sensitive data.** Treat sessions, fixtures, logs, reports and continuation packets as potentially sensitive. Do not commit raw personal sessions, credentials or private paths.
6. **Do not overstate maturity.** A module, CLI selector, schema-valid file, unit test or digest read-back does not prove complete capture, lossless portability, reconstruction, resumption, production readiness or regulatory compliance.
7. **Redaction is best-effort.** Pattern/model redaction is not a guarantee. Review output before sharing; test nested lists, structured source payloads, credentials and failure-safe writes.
8. **Keep documentation honest.** Separate implemented, tested, experimental, designed, planned and unsupported capabilities. Align README, PRD, schemas, ADRs, changelog, roadmap, wiki and package metadata.
9. **Keep Core offline-capable.** Hosted storage, dashboards and platform services must remain optional.
10. **Prefer documented interfaces.** Do not depend on undocumented database layouts or private APIs without version pinning, fixtures and explicit compatibility warnings.

## Required workflow

### Before work

1. Read STATUS.md and the relevant SOPs.
2. Check the current default branch, open PR count, active branches and target PR head.
3. Follow SOP-016: maximum three open PRs unless the maintainer explicitly approves an exception.
4. Re-read the exact file and current review thread before acting on a finding.

### Bug fixes

1. Reproduce the issue against the current code.
2. Identify and fix the root cause, not only the symptom.
3. Add a focused regression test.
4. Run the focused test and full test suite where feasible.
5. Record commands and results accurately; distinguish tested commit from later commits.

### Schema or adapter changes

1. Update the applicable schema and ontology.
2. Add sanitised, version-identified source fixtures; synthetic fixtures must be labelled synthetic.
3. Preserve unknown source data where safe and report semantic loss.
4. Update reader conformance, examples and compatibility notes.
5. Test malformed, partial, unknown and version-skewed records.

### Documentation changes

1. Check statements against current implementation, schemas and tests.
2. Use repository-relative links for repository files.
3. Mark dated inventories as snapshots and identify their branch/commit.
4. Remove unsupported legal, market-share, performance and compatibility claims.
5. Keep docs/wiki/ as the wiki source; root wiki/ is a historical redirect only.
6. Update the relevant root index and changelog when the source-of-truth structure changes.

### Architecture changes

Add or update an ADR when a change affects a stable contract, compatibility boundary, security model or service responsibility. Never leave two conflicting decisions marked accepted.

## Local verification

    python -m pip install -e ".[dev]"
    python -m pip check
    python -m pytest -q
    python -m build

Use focused tests during iteration, then the complete suite before merge. Validate JSON and JSONL separately. Run installed-wheel checks outside the repository checkout.

## Packaging and release

- Keep schemas and runtime resources in wheel and source distributions.
- Test resource discovery from an installed wheel outside the checkout.
- Keep the Python package version separate from the AgentSON schema version.
- Do not change release metadata or tags without checking PyPI and Git history.
- A release note must not imply that a PR's unmerged changes are already present on the default branch.

## Key references

- Canonical stream schema: spec/v1.2-entries.json
- Session-envelope compatibility schema: spec/v1.2.json
- Ontology: spec/ontology.md
- ADR-015: spec/ADR-015-canonical-schema.md
- ADR-016: spec/ADR-016-ontology-enum-reconciliation.md
- ADR-017: spec/ADR-017-core-vs-streaming.md
- ADR-025: spec/ADR-025-cross-harness-context-continuation.md
- Reader conformance: docs/standards/reader-conformance-v1.2.md
- Security policy: SECURITY.md
- Contributing: CONTRIBUTING.md
