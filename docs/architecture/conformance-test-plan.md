# AgentSON Cross-Harness Conformance Test Plan

**Status:** Test programme; levels are evidence claims, not product badges.  
**Canonical wire format:** v1.2 JSONL.

## 1. Purpose

This plan defines what must be tested before AgentSON can claim that a source adapter captures a session, that an archive is portable, or that a destination reconstructs or resumes work. A reader test, schema test or archive digest comparison proves only the behaviour it actually exercises.

## 2. Evidence levels

| Level | Claim | Required proof |
|---|---|---|
| C0 | Archive validity | Correct JSONL framing, first stream-meta event, event-schema validation and negative cases |
| C1 | Source capture | Production reader tested against a versioned source fixture with provenance and known-loss assertions |
| C2 | Cross-harness portability | Live producer and independent destination consumer, plus semantic comparison of source and imported records |
| C3 | Reconstruction | Destination rebuilds a useful representation of recorded work and reports unavailable state |
| C4 | Resumption | Destination resumes from a validated checkpoint with explicit capability negotiation, authorisation and isolation |

C0 and C1 do not imply C2. C2 does not imply C3 or C4.

## 3. Canonical contract

- One JSON event per line.
- The first event is stream-meta.
- Retain the .agentson extension.
- Validate each event against spec/v1.2-entries.json.
- Treat spec/v1.2.json as the materialised session-envelope/document contract, not the JSONL stream schema.
- Preserve source identifiers and sequence where available.
- Do not manufacture missing timestamps, tool results, observations or actor identity.
- Preserve unknown source data where safe and report transformation loss.

## 4. Producer requirements

Every producer adapter must provide:
1. A sanitised, version-identified source fixture, or an explicitly synthetic fixture.
2. The production reader entry point, not duplicated test-only mapping code.
3. Canonical v1.2 JSONL output.
4. Validation of stream framing and every event.
5. Assertions for source identity, event order, actor/tool attribution, timestamps and action/result correlation.
6. A mapping/loss report for preserved, normalised, inferred, unavailable, redacted and unsupported fields.
7. Negative cases for truncated, malformed, unknown and version-skewed source records.

## 5. Consumer requirements

Every consumer adapter must additionally prove:
1. It accepts the declared v1.2 stream contract.
2. It rejects or explicitly migrates unsupported versions.
3. It preserves ordering and source identity.
4. It retains unknown extensions or reports why it cannot.
5. It never executes imported commands or tool calls during inspection/import.
6. It provides a deterministic semantic comparison result.
7. It has a live destination-harness test before any C2 claim.

## 6. Current evidence and limits

The PR #62 branch records a pinned OpenCode CLI 2.2.5 live handoff/read-back test using a synthetic ChatGPT-shaped source fixture. This demonstrates the tested archive-capsule storage path, not semantic equivalence for a real export. A permissioned, sanitised real source export and semantic comparison are still required before claiming C2 for that pair.

Native event reconstruction and checkpoint resumption remain unclaimed. See the [reader conformance matrix](../standards/reader-conformance-v1.2.md), [OpenCode consumer profile](opencode-consumer-profile.md) and [ADR-025](../../spec/ADR-025-cross-harness-context-continuation.md).

## 7. Security and privacy gates

- Never commit raw private sessions, credentials, private keys or unnecessary personal data.
- Imported prompts, tool arguments, commands and outputs are untrusted and inert.
- Review redacted outputs; regex or model-based screening is not a complete detector.
- Resumption tests require a disposable workspace, explicit approval, capability allow-list, resource limits and auditable cleanup.
- Hashes establish integrity relative to covered bytes, not source authenticity or truth.
- Record missing evidence and test failures; do not convert them into success claims.
