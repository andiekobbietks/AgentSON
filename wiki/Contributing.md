# Contributing to AgentSON

## Before changing code or documentation

1. Read the root `STATUS.md`.
2. Read [SOP-016: Work-In-Progress Governance](../SOPs/SOP-016-Work-In-Progress-Governance.md).
3. Read [SOP-015: Repository Operating Procedure](../SOPs/SOP-015-AI-Agent-Repository-Operating-Procedure.md).
4. Read [Coding Standards](Coding-Standards) and the relevant architecture/ADR.
5. Check open PRs, active branches and current master before creating work.

The repository's `master` branch is protected. Use branch → commit → PR; do not push directly to master. Respect the WIP limit and verify repository state between dependent actions.

## Adding a reader or adapter

1. Identify the exact source harness and source-format version.
2. Document what the source exposes and what it does not expose.
3. Implement a source-specific adapter that maps into the canonical v1.2 JSON session envelope.
4. Preserve source identity, ordering, timestamps and provenance where available.
5. Report data as preserved, normalised, retained as source extension, unavailable, redacted or unsupported.
6. Add tests for real-world source variations. Use sanitised, provenance-labelled real fixtures only when publication is approved; otherwise use synthetic fixtures and label them honestly.
7. Test malformed records, unknown fields, missing timestamps, partial exports and version skew.
8. Update [Readers](Readers) with implementation status, exact tests and limitations.

## Cross-harness claims

Do not label an adapter "interoperable" simply because it exports a file. State which capabilities are implemented:

- capture;
- canonical export;
- import;
- validation;
- inspection;
- reconstruction;
- checkpoint-based resumption.

Portability, reconstruction and resumption require separate tests. A receiving harness must not execute imported tool calls during inspection. Resumption requires compatible capabilities, explicit authorisation and safe execution controls.

## Documentation

- Product requirements: [PRD.md](../PRD.md)
- Architecture: [Session Interoperability Architecture](../docs/architecture/session-interoperability.md)
- Canonical schema: [spec/v1.2.json](../spec/v1.2.json)
- Event ontology: [spec/ontology.md](../spec/ontology.md)
- ADR index: [ADRs](ADRs)
- Engineering policy: [Coding Standards](Coding-Standards)

Update the source-of-truth document and the relevant wiki mirror in the same change. Do not leave stale examples, schema versions or feature-status claims behind.

## Pull request checklist

- [ ] Scope matches an existing requirement or approved ADR.
- [ ] No secrets, PII or raw private sessions included.
- [ ] Real and synthetic fixtures are clearly distinguished.
- [ ] Tests and static checks actually ran; results are reported accurately.
- [ ] Semantic loss and provenance behaviour are documented.
- [ ] Feature labels match implementation and evidence.
- [ ] README, PRD, schema docs and wiki are aligned where affected.
- [ ] CHANGELOG and STATUS updated where required.
