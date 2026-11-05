# AgentSON — Repository Instructions

These instructions apply to changes in this repository. Treat checked-in code, schemas, tests and accepted ADRs as the source of truth; do not rely on old summaries or release notes when they conflict with the current implementation.

## Project boundary

AgentSON has two deliberately separate layers:

- **AgentSON Core:** the Apache-2.0 event format, versioned schemas, readers, importers, exporters, validators, CLI and protocol-neutral interfaces. Core must remain useful offline and without a hosted account.
- **AgentSON Platform:** optional discovery, ingestion, indexing, catalogue, governance and service functionality. Platform features must not become mandatory dependencies for reading or validating local AgentSON files.

Do not move a platform/service responsibility into the file format merely because a reference implementation uses it. See [ADR-023](spec/ADR-023-production-readiness-and-knowledge-catalog-architecture.md).

## Schema status

| Schema | Status | Use |
|---|---|---|
| `spec/v1.json` | Deprecated | Legacy compatibility only |
| `spec/v1.1.json` | Deprecated | Legacy compatibility only |
| `spec/v1.2.json` | Canonical version family | Session-document schema |
| `spec/v1.2-entries.json` | Canonical version family | Flattened per-event validator for JSONL streams |

**v1.2 is the canonical format decision.** JSONL is the canonical interchange stream, with one event per line and `stream-meta` as its first event. The session-document representation remains supported by document-oriented tooling; do not confuse that representation with the canonical JSONL wire shape.

The 12 event primitives are defined by `spec/ontology.md` and reconciled with the schemas by ADR-016. Update the ontology, schemas, fixtures, tests and examples together when changing the event contract.

The separate Severity v1 specification is a JSON Schema 2020-12 / Pydantic data contract. It is not a REST API or OpenAPI document.

## Engineering rules

1. **Preserve source evidence.** Do not silently discard, invent or coerce source events. Preserve unknown source fields or record an explicit mapping/loss warning.
2. **Preserve provenance.** Distinguish source-observed data from inferred, reconstructed, normalised or redacted data.
3. **Keep boundaries explicit.** Format, adapters, transport, storage, viewer and managed service are separate concerns.
4. **Avoid hidden dependencies.** Declare every runtime and development dependency in `pyproject.toml`. Optional functionality should use an explicit extra and fail with an actionable message when absent.
5. **Protect sensitive data.** Never commit real session exports, credentials, tokens, personal data, health data, private file paths or customer evidence. Use synthetic or sanitised fixtures and label them accurately.
6. **Do not overstate maturity.** A CLI selector, schema-valid file, passing unit test or local demo does not prove lossless interoperability, safe replay, production readiness or regulatory compliance.
7. **Keep documentation honest.** Separate implemented, tested, experimental, planned and not-implemented capabilities. Keep README, schemas, ADRs, changelog, roadmap and package metadata aligned.
8. **Avoid unnecessary service coupling.** Local read, validation and export must not require a hosted service or network access.

## Required workflow for changes

### Bug fixes

- Reproduce the defect and identify the failing contract or code path.
- Add a regression test that fails before the fix.
- Make the smallest coherent correction.
- Run the same test after the fix and run the complete test suite.

### Schema or adapter changes

- Identify the source and target schema versions.
- Add valid, invalid, boundary and malformed-input fixtures.
- Test missing, null, unexpected and vendor-specific fields.
- Preserve native source data or document conversion loss.
- Update the ontology, schema, examples, reader documentation and compatibility notes where relevant.

### CLI and packaging changes

- Test the public command through its entry point, not only by calling internal functions.
- Build both wheel and source distribution.
- Confirm that required schemas and data files are included in both artefacts.
- Install the wheel outside the repository and smoke-test the installed CLI.

### Architecture changes

- Add or update an ADR when a change affects a stable contract, compatibility boundary, security model or service responsibility.
- Record claims, evidence, assumptions, inference, counterarguments, failure modes, falsification tests and consequences.
- Treat automated review comments as hypotheses to verify against source and tests.

## Local verification

Run the checks that apply to the change:

```bash
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest -q
python -m build
agentson --help
agentson validate examples/
```

The GitHub Actions workflow is authoritative for the checks it actually executes. Do not report a check as passing until its result has been observed. If a command is not run, state that clearly.

## Packaging requirements

The v1.2 schemas are required at runtime by the validator. Keep `spec/v1.2.json` and `spec/v1.2-entries.json` in both wheel and source distribution artefacts. Any new runtime resource must have an explicit package-data/manifest rule and an installed-wheel regression check.

## Release and compatibility policy

- Schema version and Python package version are independent.
- Do not infer a package release from the schema version or a changelog heading.
- Do not bump package versions without reconciling published releases, tags, changelog entries and package metadata.
- Do not introduce a breaking schema change without an explicit compatibility decision and migration notes.
- Treat production readiness as workload- and service-boundary-specific evidence, not a generic project label.

## Key references

- [README](README.md)
- [Canonical schema](spec/v1.2.json)
- [Event schema](spec/v1.2-entries.json)
- [Ontology](spec/ontology.md)
- [Architecture decisions](spec/)
- [Production-readiness assessment](docs/production-readiness-assessment.md)
- [Security policy](SECURITY.md)
- [Contribution guide](CONTRIBUTING.md)
