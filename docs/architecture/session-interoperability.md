# AgentSON Session Interoperability Architecture

**Status:** Architecture baseline for the documentation set  
**Scope:** Cross-harness session capture, interchange, inspection and controlled continuation  
**Implementation status:** This document defines the target contract. It does not assert that every capability is implemented.

## 1. Product vision

AgentSON enables an AI-agent session produced by one harness to be captured, represented, validated, exchanged and inspected by another while preserving the meaning, structure, provenance and integrity of what happened.

Where the receiving harness has the necessary compatible capabilities and authorised state, AgentSON should also support controlled reconstruction and resumption. Importing a record must never be represented as proof that the original execution environment has been recreated.

AgentSON is an open session-interchange model and toolchain. It is not itself an AI harness, model runtime, execution sandbox, credential manager or guarantee that two different agents will behave identically.

## 2. Interoperability guarantees

The project distinguishes these guarantees because they require different evidence:

| Guarantee | Meaning | Minimum evidence |
|---|---|---|
| Capture fidelity | Source activity is extracted with its source identity and relevant ordering intact. | Source fixture, reader test and extraction limitations. |
| Portability | A conforming consumer can parse and understand the exchanged session without depending on the originating harness. | Schema validation and cross-implementation import test. |
| Reconstruction | A consumer can rebuild a useful representation of the recorded activity and context. | Reconstruction test and explicit list of unavailable state. |
| Resumption | A compatible receiving harness can continue work from an explicit, validated checkpoint. | Runtime-specific restore test, capability negotiation and authorisation checks. |

Portability does not imply reconstruction; reconstruction does not imply resumption. A session may be portable and inspectable even when the receiving harness cannot resume it.

## 3. Conceptual pipeline

1. **Capture:** A source reader or adapter extracts records from a harness, export, API or supported trace source.
2. **Preserve:** The adapter retains source identifiers, source timestamps, raw or source-specific fields where permitted, and the extraction method.
3. **Normalise:** Source records are mapped into the canonical AgentSON event vocabulary. Normalisation must not silently erase distinctions.
4. **Validate:** The session envelope, entries, ordering, references, timestamps, provenance and integrity metadata are checked against the applicable versioned contracts.
5. **Exchange:** The self-contained session representation is exported and imported without requiring the source harness or a hosted AgentSON service.
6. **Inspect:** A human or tool can inspect the timeline, actors, actions, observations, side effects, evidence and transformation history.
7. **Reconstruct / resume:** A receiving adapter may restore a supported representation or resume from a compatible checkpoint, subject to explicit capability and safety checks.

MCP, REST APIs, CLI commands, databases and hosted services may implement integration or transport surfaces. None of them replaces the canonical interchange contract.

## 4. Canonical session representation

The current v1.2 JSON Schema at `spec/v1.2.json` defines a **single JSON session envelope** with an ordered `entries` array. The envelope is the canonical archive representation for this documentation baseline. The per-entry contract is in `spec/v1.2-entries.json`; the event vocabulary is defined by `spec/ontology.md`.

This resolves a documentation conflict: ADR-015 historically declared JSONL canonical, but the v1.2 envelope schema is an object with `id`, `tool` and `entries`, not a JSONL document validator. ADR-024 supersedes that earlier decision for the canonical archive. Existing line-oriented exporters or stream implementations must be treated as stream/transport implementations until they are explicitly specified, validated and tested against a versioned stream contract. They must not be described as the canonical v1.2 archive merely because they emit JSONL.

A canonical session archive should be independently parseable and inspectable. Optional external artefacts may be referenced only when the reference is explicit and integrity-verifiable; a consumer must be able to identify that an artefact is absent. A reference to an external file, database, service or runtime must not be disguised as embedded content.

## 5. Semantic fidelity and loss accounting

**No silent semantic loss** is a core interoperability requirement.

Every adapter and transformation must be able to classify relevant source information as one of:

- **Preserved:** retained without semantic change.
- **Normalised:** mapped to a canonical equivalent, with the mapping documented.
- **Source extension:** retained in a namespaced source-specific field or payload.
- **Unavailable:** not exposed by the source or not obtainable by the adapter.
- **Redacted:** deliberately removed or masked under a documented privacy/security rule.
- **Unsupported:** recognised but not represented by the current target contract.

A transformation should record its source adapter and version, target schema version, transformation version, capture time, source time where available, and any loss or redaction report. Unknown is not the same as absent, false, empty or zero. Do not fabricate timestamps, tool results, model identifiers, actor identities or execution state to make a record appear complete.

Ordering must preserve the source's ordering semantics. Where source clocks differ or timestamps are missing, preserve source sequence information where available and declare uncertainty rather than inventing a total order.

## 6. Provenance and evidence

The model must distinguish at least:

- **Origin:** which harness, process, API, export or user supplied the record.
- **Source identity:** the source session, event, message, tool call or artefact identifier, subject to safe redaction.
- **Capture:** when and how AgentSON obtained the information.
- **Transformation:** which adapter and mapping version changed its representation.
- **Confidence:** whether a value is confirmed, inferred, estimated or unknown.
- **Integrity:** hashes or signatures where implemented, including what exact bytes or canonical representation they cover.
- **Attribution:** which user, agent, tool or system actor is associated with an event, and whether that attribution is source-provided or inferred.

Provenance metadata describes the evidence and its handling; it does not prove that the source itself was truthful. A hash proves byte-level correspondence to a known digest, not the truth of the recorded event.

## 7. Reconstruction and resumption boundary

Reconstruction is the recovery of a useful representation of recorded work. Resumption is a new execution that continues from a compatible state. They must not be conflated.

A resumable checkpoint may require more than a transcript, including a workspace snapshot or commit, pending task state, tool capability declarations, dependency/environment information, conversation context, and explicit user authorisation. The receiving harness must declare what it can restore and what it cannot.

Credentials, access tokens, private keys, personal secrets and live authorisation grants must not be embedded in portable session archives. A session may refer to an external credential provider or require the user to re-authorise. Imported tool calls and outputs are untrusted data: inspection must not execute them, and resumption must require explicit policy checks, sandboxing and approval appropriate to the action.

A receiving harness must never claim exact continuation when it has only reconstructed a prompt or transcript. It should report a resume outcome such as fully restored, partially restored, inspection-only, or rejected, together with the missing capabilities and state.

## 8. Adapter and consumer conformance

Adapters should declare capabilities independently. A reader that can capture and export a session is not automatically an importer, a reconstruction engine or a resume adapter.

The conformance profile should assess, at minimum:

1. Source capture and fixture provenance.
2. Canonical envelope and event validation.
3. Ordering and correlation preservation.
4. Provenance and transformation reporting.
5. Unknown-field and extension handling.
6. Redaction and secret handling.
7. Round-trip and cross-harness exchange behaviour.
8. Inspection completeness.
9. Reconstruction limitations.
10. Resume capability, permissions and safety controls, where claimed.

A conformance result must identify tested schema versions, adapter versions, source harness versions, fixtures, known gaps and whether evidence is synthetic or derived from a real export.

## 9. Versioning and compatibility

The canonical envelope version, event ontology version, adapter version and transformation version are distinct. A consumer must not infer one from another.

Compatibility claims should state whether a change is backward-compatible, forward-compatible, lossy, or breaking. Unknown event types and fields must be handled according to an explicit policy: preserve as extensions when safe, reject when required for interpretation, or report as unsupported. Never silently discard them.

Legacy v1 and v1.1 single-document formats remain legacy inputs as documented by the schema history. Migration into v1.2 must report any information that cannot be mapped. JSONL stream implementations require their own explicit contract and compatibility tests.

## 10. Security, privacy and trust boundaries

- Treat imported session content, prompts, tool outputs, code, URLs and file paths as untrusted input.
- Do not execute imported commands, scripts, links or tool calls during parsing or inspection.
- Do not include secrets or reusable credentials in portable archives.
- Redact personal data only under explicit, documented rules and record that redaction occurred without leaking the redacted value.
- Keep capture, interpretation, risk assessment and access/audit events distinguishable.
- Make offline inspection possible for the canonical archive; hosted services remain optional.
- Verify hashes/signatures only against a declared canonicalisation and coverage rule.
- Do not make legal compliance or certification claims solely because a field or manifest exists.

## 11. Implementation status and claims

This architecture is a target and documentation baseline, not a statement that all stages are implemented. Feature status must be recorded per reader, importer, exporter, validator, viewer and resume adapter.

Use the labels **Implemented and tested**, **Implemented, not yet verified**, **Experimental**, **Designed**, **Planned**, or **Unsupported**. Each claim should link to implementation and test evidence. Do not use a broad phrase such as "cross-harness resumption supported" when only export, parsing or replay inspection has been tested.

## 12. Decision and evidence chain

For each interoperability requirement, maintain this chain:

**Principle → Requirement → Contract → Implementation → Automated verification → Evidence → Known limitation.**

This is the basis for conformance reporting, release notes, standards mapping and future assurance work.
