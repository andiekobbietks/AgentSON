# Contributing to AgentSON

## Before changing code or documentation

1. Read STATUS.md and the repository instructions in AGENTS.md.
2. Check the live pull-request queue and follow SOP-016. Do not create another PR when the queue is at or above the three-PR limit unless the maintainer explicitly approves an exception.
3. Confirm the current canonical contract: v1.2 JSONL, one event per line, stream-meta first. Individual events use spec/v1.2-entries.json. The materialised document envelope in spec/v1.2.json is a compatibility representation, not the JSONL stream schema.
4. Read the relevant ADR, reader conformance notes and tests before editing an adapter.

## Adding a reader

1. Identify the source application and version/schema generation.
2. Use documented exports or read-only access where possible.
3. Implement the production reader path and preserve source identifiers, event order and raw source data where safe.
4. Map into the v1.2 event vocabulary without inventing missing timestamps, observations, results or actor identities.
5. Retain unknown source fields where safe and document normalisation, inference, unavailable data, redaction and unsupported semantics.
6. Add sanitised source fixtures. Label synthetic fixtures explicitly; never commit raw private sessions or credentials.
7. Test malformed, truncated, unknown and version-skewed records.
8. Update docs/standards/reader-conformance-v1.2.md and docs/wiki/Readers.md with the tested source version and limitations.

## Adding a destination consumer

A reader is not a consumer. A consumer imports an AgentSON stream into another harness. It must validate the declared version, preserve source identity and ordering, treat imported content as untrusted, and avoid executing historical commands or tool calls.

A C2 claim requires a live producer-to-consumer test and semantic comparison. Archive read-back or digest equality alone is not C2 evidence. Reconstruction and resumption require separate C3/C4 tests.

## Documentation

- State whether a capability is implemented, tested, experimental, designed, planned or unsupported.
- Date inventories and identify the branch/commit they describe.
- Avoid legal compliance, trademark clearance, market-share or lossless-compatibility claims without evidence.
- Keep docs/wiki as the checked-in wiki source. Root wiki files are historical redirects.
- Update README, PRD, STATUS and CHANGELOG when a contract or capability changes.

## Pull request checklist

- [ ] Reproduced the issue or stated the requirement.
- [ ] Added or updated focused tests and sanitised fixtures.
- [ ] Ran the focused tests and, where feasible, the complete suite.
- [ ] Checked schema/package resources and installed-wheel behaviour when relevant.
- [ ] Updated relevant documentation and ADRs.
- [ ] Checked internal links and capability claims.
- [ ] Recorded exact test commands, commit and results.
- [ ] Confirmed the PR queue and current base/head state before merge.
