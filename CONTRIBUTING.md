# Contributing to AgentSON

Thank you for considering a contribution. AgentSON is an evolving interoperability project; clear evidence, careful scope and compatibility matter more than the size of a change.

## Before you start

- Read [PROJECT_CHARTER.md](PROJECT_CHARTER.md), the relevant schema and ontology, and the applicable Architecture Decision Records.
- Search existing issues before opening a new one.
- For a substantial change, open an issue or discussion first so the problem and proposed direction can be reviewed.
- Do not publish private session exports, personal data, credentials, access tokens, proprietary source material or unredacted logs.

## Contribution workflow

1. Describe the problem and expected behaviour.
2. Keep changes focused and explain any compatibility impact.
3. Add or update tests, including negative cases where appropriate.
4. Update schema documentation, examples, ADRs and changelog entries when affected.
5. Run the relevant test suite and report the exact commands and results.
6. Submit a pull request with a concise summary, rationale, test evidence and known limitations.

## Schema and format changes

- Do not silently change the meaning of an existing event type or field.
- Prefer additive, versioned changes where possible.
- Update the canonical schema and any generated/flattened schema together.
- Include representative fixtures and validation tests.
- Document migration requirements and information loss.
- Record material decisions in an ADR.
- Do not claim cross-runtime compatibility without testing at least the relevant producer and consumer paths.

## Security and privacy

Treat all session data as potentially sensitive. Prompts, model outputs, tool arguments, command output, local paths, identifiers and environment metadata may expose personal, organisational or security-sensitive information.

Use synthetic or deliberately sanitised fixtures. Never commit secrets or live customer data. Report suspected vulnerabilities privately using the process in [SECURITY.md](SECURITY.md).

## Pull request checklist

- [ ] The change addresses a clearly described problem.
- [ ] Tests have been added or updated.
- [ ] Relevant tests pass, or failures are explained.
- [ ] Documentation and changelog are updated where needed.
- [ ] Schema compatibility and migration impact are stated.
- [ ] Sensitive data and secrets have been excluded.
- [ ] Claims distinguish implemented behaviour from proposals.

## Licensing

By intentionally submitting a contribution for inclusion, you agree that it is provided under the repository's Apache License 2.0, unless a separate written agreement with the project owner states otherwise. Please do not submit material you do not have the right to contribute.
