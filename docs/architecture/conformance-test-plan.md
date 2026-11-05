# Cross-Harness Conformance Test Plan

**Status:** C0 archive validation baseline plus an experimental OpenCode archive-capsule consumer with mocked API contract tests; no live C2 result yet  
**Target contract:** AgentSON v1.2 canonical JSON session envelope  
**Related decisions:** Specification ADR-024; `docs/architecture/session-interoperability.md`; [OpenCode Consumer Profile](opencode-consumer-profile.md)

## 1. Purpose

This plan turns the interoperability architecture into repeatable tests. The goal is not merely to prove that JSON can be parsed twice. It is to prove that a session produced by one harness can be understood by an independent consumer without silently changing event meaning, ordering, identity, provenance or the known limits of the source capture.

A green schema test is necessary but not sufficient evidence of cross-harness interoperability.

## 2. Conformance levels

| Level | Name | What it proves | Minimum evidence |
|---|---|---|---|
| C0 | Archive validity | A canonical envelope and each entry validate against the declared schema version. | Schema tests and invalid-case tests. |
| C1 | Preservation | A consumer preserves event order, source identity, correlation, provenance and source extensions. | Producer fixture, consumer round-trip and semantic comparison. |
| C2 | Adapter interoperability | A real producer adapter exports an archive that a separately implemented consumer adapter imports. | Source-backed fixture and producer A → canonical archive → consumer B test. |
| C3 | Reconstruction | The receiving harness rebuilds the recorded task/context representation and reports unavailable state. | Reconstruction result and explicit loss/unavailability report. |
| C4 | Resumption | A compatible receiver continues from a validated checkpoint under explicit authorisation. | Isolated runtime test, capability negotiation, approval and checkpoint integrity evidence. |

C0–C4 are cumulative evidence levels, not marketing labels. C0 or C1 must never be described as C2. C2 does not imply C3 or C4.

## 3. Executable baseline

Run locally:

```bash
python -m pip install pytest jsonschema
python -m pytest -q tests/conformance/test_canonical_archive.py tests/test_opencode_real_sample.py tests/test_opencode_consumer.py tests/test_chatgpt_importer.py
```

The suite and fixtures are:

- `tests/fixtures/conformance/cross_harness_session_v1_2.json`
- `tests/conformance/test_canonical_archive.py`
- `.github/workflows/conformance.yml`
- Production-reader regression: `tests/test_opencode_real_sample.py`
- OpenCode consumer contract tests: `tests/test_opencode_consumer.py`
- Live OpenCode v2 integration: `tests/integration/test_opencode_live.py`
- ChatGPT importer v1.2 conformance: `tests/test_chatgpt_importer.py`
- Receiving adapter: `consumers/opencode.py`

The canonical fixture is deliberately synthetic and labelled as such. It exercises the v1.2 envelope, the 12-primitive entry validator, source identifiers, source sequence, correlation, source-specific extensions, action-without-observation semantics and the absence of a mandatory `stream-meta` event.

The OpenCode consumer targets HTTP API v2. It creates a session and injects the full archive as one synthetic message with `resume: false`, so the agent loop is not scheduled immediately. The synthetic message can still enter model context on a later turn; this is not isolated storage. Mock tests verify validation, synthetic insertion, payload preservation, endpoint restrictions, future-context disclosure and cleanup. A live integration test starts pinned OpenCode CLI 2.2.5, imports the fixture, reads the deferred synthetic item back through the v2 session inbox API and compares the embedded archive and digest. This establishes archive-capsule storage fidelity against the tested OpenCode version, not native event reconstruction or full semantic C2 interoperability. See [OpenCode Consumer Profile](opencode-consumer-profile.md).

## 4. Required adapter test contract

Every producer adapter must provide a conformance test with:

1. A sanitised, version-identified source fixture, or an explicitly labelled synthetic fixture where real data cannot lawfully be retained.
2. The exact reader/adapter entry point used in production. Do not copy or reimplement the mapping logic inside the test.
3. The canonical v1.2 archive output.
4. Schema validation of the complete envelope and each entry.
5. Assertions for source identity, actor attribution, event order, timestamps/sequence, action-result correlation and source-specific fields.
6. A documented mapping/loss report for fields that are normalised, unavailable, redacted or unsupported.
7. Negative cases for truncated, malformed, unknown and version-skewed source records.

Every consumer adapter must additionally prove:

1. It accepts the canonical envelope version it declares.
2. It rejects or explicitly migrates unsupported versions; it must not silently reinterpret them.
3. It preserves event ordering and source identity.
4. It retains source extensions it does not understand, or reports precisely why it cannot.
5. It does not execute imported tool calls, commands, prompts or outputs during inspection/import.
6. It produces a deterministic semantic comparison result, excluding only fields explicitly declared volatile.
7. It has a live target-harness integration test before the pair is called C2-conformant.

## 5. Cross-harness pairwise matrix

The following matrix is a test programme, not a claim that these pairs currently work.

| Producer | Consumer | Current evidence | Next requirement |
|---|---|---|---|
| OpenCode | AgentSON OpenCode consumer | OpenCode reader and consumer adapter exist; consumer tests use a mocked API and store the archive as one opaque context message. | Run against a version-identified live OpenCode server, read the stored message back, compare the embedded archive, then assess semantic/native event mapping before C2. |
| ChatGPT export | OpenCode | ChatGPT importer emits schema-tested v1.2; OpenCode archive-capsule consumer exists. | Add a source-backed ChatGPT fixture through the receiving adapter and live read-back. |
| Claude Code | OpenCode | Dedicated source reader exists; no consumer pair test. | Add a sanitised source fixture and live receiving-harness test. |
| Aider | Cline | Dedicated readers exist; no canonical archive consumer import path. | Implement and test a receiving adapter; do not treat reader presence as import support. |
| Cursor | Copilot Chat | Reader evidence only; no canonical archive consumer import path. | Implement and test a receiving adapter; do not treat reader presence as import support. |

A reader test proves only the reader behaviour it exercises. A mocked consumer API test proves request construction and adapter behaviour against the mock, not that a live harness accepted or retained the archive.

## 6. Semantic comparison rules

The comparator must compare meaning, not raw byte equality. At minimum, it must report:

- Entry count and primitive-type distribution.
- Relative event order and source sequence where available.
- Source event/session identifiers.
- Actor and tool attribution, including whether attribution is source-provided or inferred.
- Action arguments and result/observation correlation.
- Timestamp values, timezone/clock uncertainty and missing timestamps.
- Provenance source, confidence and transformation lineage.
- Source-specific extensions and unknown fields.
- Redacted, unavailable and unsupported fields.
- Integrity metadata and the exact byte/canonicalisation scope it covers.

Normalisation must be declared. For example, a source timestamp converted to UTC may be semantically equivalent while not byte-identical. A missing tool result is not equivalent to an empty result. Unknown is not equivalent to null, false, zero or an empty string.

## 7. Security and privacy gates

- Test fixtures must be sanitised before commit; raw private sessions are not the default.
- Never include credentials, access tokens, private keys, live authorisation grants or unnecessary personal data in portable archives.
- Imported content is untrusted data. Inspection must be read-only and must not execute it.
- Resumption tests require a disposable workspace, explicit authorisation, capability allow-list, resource limits and an auditable approval decision.
- A signature or hash establishes integrity relative to the covered bytes; it does not establish that the source event was truthful.
- Redaction must be visible in the loss report; do not silently delete fields and claim full fidelity.

## 8. Known gaps to close

1. **Live consumer integration:** the OpenCode v2 live import/read-back is now covered against pinned CLI 2.2.5. The test proves opaque capsule storage fidelity only; it does not establish native event reconstruction or full semantic C2.
2. **Native event mapping:** the first OpenCode profile stores the complete canonical archive as one opaque context message. It does not reconstruct native message/tool events, so it is not yet a semantic C2 mapping.
3. **Source capture depth:** the OpenCode producer regression invokes the production conversion method, but its single-message fixture does not exercise complete SQLite discovery/read or multi-message ordering under source-version skew.
4. **Loss-report representation:** ADR-024 requires semantic-loss accounting, but v1.2 does not define a normative machine-readable loss-report structure.
5. **Resume profile:** there is no demonstrated cross-harness checkpoint/resume contract. Keep C4 unclaimed.

## 9. Release gate

Do not label an adapter pair interoperable until its C2 test is checked in and passes against identified source fixtures and a live receiving harness. Do not label reconstruction or resumption supported until C3/C4 evidence exists. Publish exact producer, consumer, schema versions, adapter versions, fixture provenance, test method and known losses with every conformance result.
