# Coding Standards

This page summarises the repository's engineering rules. The canonical detailed policy is [docs/standards/coding-standards.md](../docs/standards/coding-standards.md); update that source first and keep this page aligned.

## Privacy and security

- **No PII or secrets in the repository.** Do not commit personal paths, identifiers, access tokens, credentials or confidential session content.
- **No unsolicited telemetry.** No hidden analytics, tracking or background uploads. User-requested source/API integrations are allowed only when documented, scoped and transparent about data leaving the device.
- **Privacy-safe fixtures.** Real exports are valuable for fidelity but raw sessions must not be committed by default. Use sanitised, provenance-labelled fixtures with documented transformations. Synthetic fixtures are allowed for edge cases but must be labelled synthetic.
- **Imported data is untrusted.** Parsing and inspection must never execute commands, scripts, URLs or tool calls from an archive.

## Architecture

- **Vendor-neutral core.** The archive and core parse/validate/inspect operations must work without a particular harness, model provider or hosted service. Individual source adapters may have declared source-specific dependencies.
- **Self-contained archive.** A canonical session archive must be independently parseable and inspectable. Optional external artefacts must be explicit, integrity-verifiable references; never hidden dependencies.
- **No silent semantic loss.** Distinguish preserved, normalised, source extension, unavailable, redacted and unsupported information.
- **Separate guarantees.** Capture, portability, reconstruction and resumption are not interchangeable. Do not claim resume support from transcript export alone.
- **Provenance matters.** Preserve source identity, capture method/time, transformation lineage and uncertainty.

## Engineering quality

- Prefer simple solutions and justify dependencies.
- Follow PEP 8; add type hints and docstrings to public Python APIs; avoid wildcard imports; prefer f-strings.
- Reproduce bugs before claiming them. Check whether they pre-date the change, agree scope, rerun the exact reproduction, add a regression test, run the required type checks and report what was actually verified.
- Use honest status labels: implemented and tested, implemented but unverified, experimental, designed, planned or unsupported.
- Use commit messages in the form `type(scope): description`, explaining why as well as what.

## Evidence

Every meaningful claim should follow this chain:

**Principle → Requirement → Contract → Implementation → Automated verification → Evidence → Known limitation.**

A schema-valid file is not automatically complete, authentic, secure or resumable. A module in the repository is not automatically a working integration.
