# Repository status

**Last updated:** 2026-11-05T19:06:00Z  
**Branch:** `feat/jsonl-reader-conformance`  
**Current pull request:** [#62](https://github.com/andiekobbietks/AgentSON/pull/62)

Read this file before starting repository work. Update it when repository state changes.

## Pull-request queue

There are **11 open pull requests**, exceeding the SOP-016 work-in-progress limit of 3. Do not open another branch or PR until the queue is reduced or the maintainer explicitly approves an exception.

Open PRs observed on 05 November 2026:

- **#62** — `feat/jsonl-reader-conformance`: canonical v1.2 JSONL export, reader provenance/conformance, source-evidence preservation, redaction hardening and CI/package checks. Ready for review; latest full CI matrix passed.
- **#60** — `feat/wiki-mirror`: Severity v1, maintained wiki documentation and session-interoperability documentation. Its ADR-024 currently describes the JSON-object archive as canonical and JSONL as a separate transport, conflicting with #62. Reconcile before merging either branch.
- **#58** — `feat/severity-v1`: separate Severity v1 implementation; overlaps the Severity work also present in #60. Check overlap before merging.
- **#57** — `feat/remaining-fixes`: remaining Pyrefly and datetime fixes.
- **#56** — `feat/cr-review-core`: CodeRabbit review group for core module headers.
- **#55** — `feat/cr-review-stream`: CodeRabbit review group for stream module headers.
- **#54** — `feat/cr-review-tests-spec`: CodeRabbit review group for legacy schema tests/spec.
- **#53** — `feat/cr-review-cli-tools`: CodeRabbit review group for CLI/tools encoding.
- **#51** — `feat/v1.2-readme-fix`: README wordmark formatting.
- **#48** — `feat/v1.2-release`: v1.2 full-story release branch.
- **#34** — `docs/readme-title-and-audit-changelog`: README and audit-history documentation.

This list records observed open PRs, not a claim that each is merge-ready. Check current branch state, CI and review threads before taking action.

## Canonical format decision

- **v1.2 canonical interchange is JSONL:** one JSON event per line, with `stream-meta` as the first event.
- The public filename extension remains **`.agentson`**. The extension does not imply a single-document JSON body.
- `spec/v1.2-entries.json` validates individual stream events and is generated from `spec/v1.2.json` by `python tools/flatten_schema.py`.
- `spec/v1.2.json` remains available for legacy/document-oriented compatibility; it is not the default export wire representation.
- Legacy document-style `.agentson` files remain readable through the shared compatibility loader.
- New exports preserve reader-level event objects in `source_payload` and reader-specific session metadata in `stream-meta.source_session.source_metadata` where the reader supplies them.
- Preserve source evidence without inventing timestamps, observations, tool results or semantics. Mark unknown/unmapped source events explicitly.

## Current verification status: PR #62

**Verified code head:** `b3cd3059667102eed7d0e92df1c6035c0e131f0c`  
**GitHub Actions:** [run 42086513220](https://github.com/andiekobbietks/AgentSON/actions/runs/42086513220)  
**Result:** success on Python 3.9, 3.10, 3.11 and 3.12.

Each matrix job ran the full test suite: **260 passed, 0 failed**. The workflow also completed dependency consistency checks, built the wheel and source distribution, verified that both v1.2 schemas were packaged, and smoke-tested the installed wheel and CLI.

The test run reported 60 warnings on the Python 3.12 job. These include existing deprecation and pytest warnings; they are not test failures and should be reviewed separately rather than silently ignored.

The CI workflow concurrency group uses the pull request's source branch (or the pushed branch name) so push and pull-request events for the same branch do not run duplicate matrices.

## Cross-harness continuation

- Added `agentson resume INPUT --target TARGET [--output FILE]`.
- The command validates canonical JSONL streams and accepts supported legacy session documents, then writes a portable Markdown context packet.
- The packet preserves available conversation text, event types, tool names, timestamps, source identity and correlation identifiers.
- Raw tool arguments, code and source payloads are excluded by default to reduce accidental secret disclosure. Conversation text can still contain sensitive material; review/redact before sharing externally.
- The packet explicitly marks transcript content as untrusted historical data and does not replay commands or restore private runtime state.
- OpenCode is now the first native destination adapter: `agentson resume INPUT --target opencode --launch` connects to an already-running OpenCode server, creates a new session, queues the packet with `resume=false`, then reads the session inbox back to verify storage. It does not start an agent turn or replay tool calls.
- Set `OPENCODE_SERVER_USERNAME` / `OPENCODE_SERVER_PASSWORD` for server basic auth; use `--server-url` for a non-default endpoint. The user opens the returned session with `opencode --session <id>`.
- This is verified context continuation into a new harness session, not full reconstruction of source speaker roles, exact runtime resumption or workspace checkpointing. Other destination profiles remain packet-only.
- ADR-025 records the safety and fidelity contract. The existing ADR-024 canonical-envelope versus JSONL conflict with PR #60 remains unresolved.

## Reader conformance evidence and limits

- **OpenCode 1.x:** the checked-in real message/parts sample is wrapped in temporary SQLite scaffolding and exercised through the production reader and JSONL exporter.
- **OpenCode 2.x:** a synthetic SQLite database based on upstream schema definitions exercises the actual reader, including messages, parts, reasoning, completed/error/running tools, shell records, inbox records, unknown types, raw row provenance and read-only enforcement.
- **Claude Code:** synthetic native JSONL covers assistant text/thinking, tool-use, nested tool-result correlation and end-turn answer classification.
- **Chrome DevTools:** synthetic Markdown fixture covers parsing, raw Markdown preservation, action and answer projection.
- **MiniMax/Mavis:** temporary SQLite fixture covers raw message, token-usage and peer rows, including JSON-safe binary values.
- **Antigravity:** temporary SQLite fixture covers raw protobuf step bytes and metadata blobs as base64 plus SHA-256 digests; file-backed extraction is read-only and source event timestamps are not fabricated.
- **Libre:** synthetic CSV fixture covers accepted raw rows and rejected malformed-row evidence.
- All new fixtures are synthetic/source-shaped except the checked-in OpenCode message/parts sample. They are not vendor-certified or universal source-version compatibility evidence.

Remaining reader gaps include OpenCode blob attachments, event-table semantics and released-version schema drift; broader MiniMax source-version, peer/task-tree and status-code coverage; Antigravity protobuf step semantics; Claude Code subagent/multimodal variants; and versioned real-export coverage for Chrome DevTools and Libre.

## Privacy boundary

The JSONL-aware `PIIRedactor` recursively scans strings inside `source_payload` and `source_metadata`, including JSON-encoded source rows and preserved Markdown. Non-empty opaque fields ending in `_base64`, and binary envelopes marked `encoding: base64`, are omitted from redacted copies with explicit omission markers; adjacent SHA-256 digests are retained where present. This is conservative data minimisation, not a guarantee that all personal data is detected. The regex fallback has limited coverage; review redacted output before sharing.

## Integration and merge cautions

- PR #62 is ready for review and is not merged. Review the remaining fixture gaps before merging.
- PR #60 contains a conflicting canonical-format decision and unresolved review findings; reconcile and verify it before merging.
- The checked-in `docs/wiki/` source mirror on #60 has not been synchronised to the separately hosted GitHub Wiki.
- Do not push directly to protected `master`.
- Do not commit raw session exports, credentials, tokens, private file paths, personal data, health data or customer evidence.
- Imported prompts, commands, tool calls and outputs are untrusted data; inspection must not execute them.
- Do not claim a test, build, security review or standards assessment passed unless its evidence was actually observed.
