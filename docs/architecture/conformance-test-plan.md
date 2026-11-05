# Cross-Harness Conformance Test Plan

**Status:** Initial executable baseline implemented; producer/consumer adapter conformance not yet implemented  
**Target contract:** AgentSON v1.2 canonical JSON session envelope  
**Related decisions:** Specification ADR-024; `docs/architecture/session-interoperability.md`

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

## 3. Executable baseline currently added

Run locally:

```bash
python -m pip install pytest jsonschema
python -m pytest -q tests/conformance/test_canonical_archive.py
```

The initial suite and fixture are:

- `tests/fixtures/conformance/cross_harness_session_v1_2.json`
- `tests/conformance/test_canonical_archive.py`
- `.github/workflows/conformance.yml`

The fixture is deliberately synthetic and labelled as such. It exercises the v1.2 envelope, the 12-primitive entry validator, source identifiers, source sequence, correlation, source-specific extensions, action-without-observation semantics and the absence of a mandatory `stream-meta` event.

The initial JSON parse/serialise test is a neutral consumer preservation check. It is **not** a harness-to-harness test.

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

## 5. Cross-harness pairwise matrix

The following matrix is a test programme, not a claim that these pairs currently work. Select pairs only when both the source producer and receiving consumer have implemented adapters.

| Producer | Consumer | Current evidence | Next requirement |
|---|---|---|---|
| OpenCode | ChatGPT / other independent consumer | OpenCode reader tests exist; ChatGPT importer tests exist, but this does not demonstrate an AgentSON v1.2 import path. | Add canonical export, independent import and semantic diff. |
| ChatGPT export | OpenCode / other independent consumer | ChatGPT export importer exists; its current output identifies itself with the legacy v1 schema URI and uses `tool.name=chatgpt`, which is not in the v1.2 tool-name enum. | Define and test explicit v1-to-v1.2 migration and source identity mapping before claiming C0/C2. |
| Claude Code | OpenCode | Dedicated reader tests exist for both sources. | Add one shared task fixture and a real producer-to-consumer pair test. |
| Aider | Cline | Dedicated reader tests exist for both sources. | Add one shared task fixture and a real producer-to-consumer pair test. |
| Cursor | Copilot Chat | Dedicated reader tests exist for both sources. | Add one shared task fixture and a real producer-to-consumer pair test. |

A reader test proves only the reader behaviour it exercises. The existence of two reader modules does not prove that either module imports a canonical archive produced by the other.

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

1. **Legacy importer/schema mismatch:** the current ChatGPT importer emits a v1 schema URI and a `chatgpt` tool name not accepted by the v1.2 `tool.name` enum. Decide whether to add a versioned source identity model, use the existing `other` value with explicit source metadata, or introduce a migration profile. Do not silently widen the enum without an ADR/schema review.
2. **Reader test fidelity:** `tests/test_opencode_real_sample.py` contains a minimal reimplementation of the mapping logic rather than invoking `OpencodeReader`. It is useful as a mapping example/regression description but is not an end-to-end regression test of the production reader.
3. **No canonical archive consumer matrix:** current reader tests do not establish a common consumer import interface or producer-to-consumer round-trip.
4. **Loss-report representation:** ADR-024 requires semantic-loss accounting, but the v1.2 schema does not yet define a normative, machine-readable loss-report structure. Design and version this before claiming complete loss-report conformance.
5. **Resume profile:** there is no demonstrated cross-harness checkpoint/resume contract in this test baseline. Keep C4 unclaimed.

## 9. Release gate

Do not label an adapter pair interoperable until its C2 test is checked in and passes in CI against identified source fixtures. Do not label reconstruction or resumption supported until C3/C4 evidence exists. Publish the exact tested producer, consumer, schema versions, adapter versions, fixture provenance and known losses with every conformance result.
