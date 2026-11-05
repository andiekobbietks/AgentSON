# Status (last updated: 2026-11-05T11:34:20Z, by: AgentSON interoperability and conformance work)

## Pull request queue

- **10 open pull requests** were observed on 05 November 2026 after closing the temporary documentation PR #61. This exceeds the SOP-016 work-in-progress limit of 3.
- **#60** (`feat/wiki-mirror`): existing PR for the `docs/wiki/` source mirror and Severity v1. This branch now also carries the cross-harness session interoperability documentation alignment. Do not open a separate PR for the same work.
- **#61** (`docs/session-interoperability-alignment`): closed without merge after discovering the actual open-PR count. Its documentation changes were ported into the existing #60 branch. Do not reopen it.

No additional PRs should be opened until the queue is reduced below the SOP-016 limit or the maintainer explicitly approves an exception.

## Active documentation branch

- **`feat/wiki-mirror` / PR #60**: contains the checked-in `docs/wiki/` mirror, canonical session interoperability architecture, ADR-024, v1.2 schema clarification, aligned ontology/adapter/replay semantics, and coordinated README/PRD/standards updates.
- The PR also contains its pre-existing Severity v1 implementation. Interoperability work now includes documentation/specification updates, v1.2 schema source-name extension, OpenCode reader and ChatGPT importer compatibility changes, regression tests and a dedicated CI workflow.

## Documentation source of truth

- `docs/` is authoritative for product and engineering documentation.
- `docs/wiki/` is the checked-in source for the published GitHub Wiki mirror.
- The separately hosted GitHub Wiki repository is a distinct Git remote and has not been pushed by this change.
- The older root `wiki/` directory is marked as a legacy duplicate on this branch; do not treat it as a second source of truth. Reconcile or retire it after the `docs/wiki/` source is merged and the hosted wiki is synced.

## Current architecture decisions

- Product objective: cross-harness capture, representation, validation, exchange and inspection, with controlled reconstruction/resumption where supported.
- Portability, reconstruction and resumption are separate guarantees.
- Canonical v1.2 archive is the single JSON session envelope defined by `spec/v1.2.json`, with an ordered `entries` array.
- Specification ADR-024 records this architecture baseline and supersedes Specification ADR-015's historical JSONL-canonical decision.
- Existing JSONL code is a separate stream/transport implementation until a dedicated framing and conformance contract exists.
- No silent semantic loss: adapters report preserved, normalised, source-extension, unavailable, redacted and unsupported information.
- An action may exist without a captured observation; never manufacture a result. A stream header is not a mandatory entry in every canonical archive.

## Known issues and stale issue records

- **#26**: CLI scope violation — `finetune` / `push` / `pull` are registered as core subcommands; ADR-013 / issue remains open and requires maintainer decision.
- **#27**: legacy `spec/v1.json` missing the `observation` entry type. v1.2 includes an observation definition; assess whether this legacy-schema issue remains relevant to the supported migration policy.
- **#28**: issue says no `validate` CLI subcommand. Current `cli/main.py` contains `cmd_validate`, registers the `validate` parser and dispatches it. Issue appears stale; reproduce/verify installed package behaviour before closing.
- **#29**: issue says `cmd_search` is defined twice. Current `cli/main.py` snapshot contains one `def cmd_search` definition. Issue appears stale; verify with a fresh search/test before closing.

## Do not do this

- Do not push directly to protected `master`.
- Do not exceed the SOP-016 WIP limit of 3 open PRs.
- Do not create duplicate branches or PRs for work already in #60.
- Do not claim implementation, test, reconstruction or resumption support based on documentation alone.
- Do not commit raw private session exports, personal data, secrets or credentials.
- Do not treat imported prompts, tool calls, commands or outputs as trusted executable instructions.

## Verification state

- `spec/v1.2.json` parses as valid JSON.
- Repository-relative Markdown links were checked across the documentation set; no broken repository links were found. Short links such as `ADR-001` and `SOP-001` are intentional links to separately hosted wiki pages.
- The OpenCode reader and ChatGPT importer now emit the v1.2 schema identifier. The v1.2 `tool.name` enum includes `chatgpt`; missing ChatGPT timestamps are omitted rather than emitted as null.
- Sanitised Windows user-profile paths in `tests/fixtures/opencode_real_sample.json` to align with the no-personal-paths repository rule.
- GitHub Actions run [42019990061](https://github.com/andiekobbietks/AgentSON/actions/runs/42019990061) passed **20 tests** in 0.30s: canonical archive contract, production OpenCode conversion regression and ChatGPT importer tests.
- This was a focused conformance/regression run, not the full repository test suite. C2 cross-harness consumer interoperability, C3 reconstruction and C4 resumption remain unproven. PR #60 must remain under review until the wider suite and maintainer review are complete.


## Cross-harness conformance programme (05 November 2026)

- Added `tests/conformance/test_canonical_archive.py` and the explicitly synthetic fixture `tests/fixtures/conformance/cross_harness_session_v1_2.json`.
- Added `.github/workflows/conformance.yml` to run the canonical archive contract tests on relevant pull requests and pushes.
- Added `docs/architecture/conformance-test-plan.md`, linked from the main architecture, README and wiki mirror index.
- **CI evidence:** GitHub Actions run [42019565524](https://github.com/andiekobbietks/AgentSON/actions/runs/42019565524) completed successfully; 20 focused tests passed in 0.33s on 05 November 2026.
- This provides C0 archive validity and production producer-conversion evidence for the OpenCode and ChatGPT paths. It is not C2 cross-harness adapter interoperability, C3 reconstruction or C4 resumption. The full project test suite has not been run as part of this work.
- Remaining blockers: no canonical archive consumer import matrix, no normative machine-readable loss-report contract, and no demonstrated cross-harness checkpoint/resume profile.
