# Contributing to AgentSON

Thank you for considering a contribution. AgentSON is an open, vendor-neutral project; changes should preserve portability, provenance and honest feature status.

## Before opening a pull request

1. Read [AGENTS.md](AGENTS.md), the relevant specification and the applicable ADRs.
2. Check existing issues and pull requests to avoid duplicate work.
3. For a behaviour change, identify the contract being changed and update or propose an ADR where the decision is architectural.
4. Keep Core independent of optional hosted services. External services must not become mandatory for local reading, validation or export.
5. Do not commit real session exports, secrets, personal data, health data, private file paths or customer evidence.

## Required evidence

For a bug:
- provide a minimal reproduction;
- establish whether it exists on the base branch;
- add a regression test;
- rerun the same reproduction after the fix.

For a feature:
- describe the user problem and intended behaviour;
- add tests for normal, boundary and failure cases;
- update schemas, examples and documentation where relevant;
- state what is implemented versus planned.

For reader/importer changes:
- use a sanitised real-world fixture where permission allows;
- document synthetic fixtures as synthetic;
- test missing, malformed and unexpected source fields.

## Local checks

Use the project's supported Python version and run:

```bash
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest -q
python -m build
```

The pull-request CI workflow is authoritative for the checks it actually runs. Do not report a check as passing unless its command or workflow result was observed.

## Pull-request expectations

- Keep a pull request focused and explain why the change is needed.
- Link related issues and ADRs.
- Include compatibility and migration notes for public schema/API changes.
- Treat automated review comments as findings to verify, not instructions to accept blindly.
- Do not merge a breaking format change without an explicit compatibility decision.

## Security reports

Follow [SECURITY.md](SECURITY.md). Do not use public issues for undisclosed vulnerabilities or include sensitive session material in review fixtures.
