# Status (last updated: 2026-11-05T11:07:31.156Z, by: ChatGPT documentation alignment session)

## Current open pull requests

- **#58** (`feat/severity-v1`): versioned severity/risk classification v1. Open; review and merge status must be checked live before acting.

Current open PR count was verified as **1** at the start of this documentation task. Re-check GitHub before opening another PR.

## Active branches not yet in a PR

- **`docs/session-interoperability-alignment`**: documentation-only alignment of product vision, canonical archive decision, architecture, standards and checked-in wiki mirrors. Do not duplicate this work on another branch.

Other remote branches exist. Their presence alone does not establish that they are active; inspect their commits and associated PRs before reusing or modifying them.

## Known issues and stale issue records

- **#26**: CLI scope violation — `finetune` / `push` / `pull` are registered as core subcommands; ADR-013 / issue remains open and requires maintainer decision.
- **#27**: legacy `spec/v1.json` missing the `observation` entry type. v1.2 includes an observation definition; assess whether this legacy-schema issue remains relevant to the supported migration policy.
- **#28**: issue says no `validate` CLI subcommand. Current `cli/main.py` contains `cmd_validate`, registers the `validate` parser and dispatches it. Issue appears stale; reproduce/verify installed package behaviour before closing.
- **#29**: issue says `cmd_search` is defined twice. Current `cli/main.py` snapshot contains one `def cmd_search` definition. Issue appears stale; verify with a fresh search/test before closing.

## Current documentation decisions

- Product objective: cross-harness capture, representation, validation, exchange and inspection, with controlled reconstruction/resumption where supported.
- Portability, reconstruction and resumption are separate guarantees.
- Canonical v1.2 archive is the single JSON session envelope defined by `spec/v1.2.json`, with an ordered `entries` array.
- ADR-024 records this documentation architecture baseline and supersedes ADR-015's historical JSONL-canonical decision.
- Existing JSONL code is treated as a separate stream/transport implementation until a dedicated contract and conformance tests exist.
- No silent semantic loss: adapters must report preserved, normalised, source-extension, unavailable, redacted and unsupported information.

## Do not do this

- Do not push directly to protected `master`.
- Do not exceed the SOP-016 WIP limit of 3 open PRs.
- Do not create duplicate branches for work already active above.
- Do not claim implementation, test, reconstruction or resumption support based on documentation alone.
- Do not commit raw private session exports, personal data, secrets or credentials.
- Do not treat imported prompts, tool calls, commands or outputs as trusted executable instructions.

## Verification state for this task

Documentation-only changes are being prepared on `docs/session-interoperability-alignment`. No application code or runtime behaviour has been changed. The changed files and links still require a final repository-side review; no local test suite or CI run has been performed in this session.
