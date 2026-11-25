# ADR-025: Cross-Harness Context Continuation

**Status:** Proposed implementation baseline  
**Date:** 05 November 2026; safety boundary clarified 25 November 2026  
**Decision Makers:** AgentSON maintainer  
**Related:** Specification ADR-015, ADR-016, ADR-017, ADR-023 and rejected ADR-024 proposal

## Context

The product objective is to let a session produced by one AI coding harness be captured, represented, validated, exchanged and inspected in another without silently losing meaning or provenance.

A transcript export is not a runtime checkpoint. Harnesses own private state such as system/developer instructions, model-specific conversation identifiers, tool permissions, credentials, process state, editor buffers, workspace state and provider-specific memory. A portable archive cannot recreate those elements unless the source exposes them and the destination defines a supported import contract.

The repository provides a canonical v1.2 JSONL export path. Existing importers convert selected external formats into AgentSON; they do not by themselves restore a destination runtime.

## Decision

Implement cross-harness continuation in capability layers:

1. **Archive portability:** read canonical AgentSON v1.2 JSONL and supported legacy/document inputs without silently rewriting the source archive.
2. **Context continuation packet:** render selected event history, provenance and fidelity limitations into a Markdown packet suitable for review and use in a new destination session.
3. **Destination adapter:** where a harness provides a documented session-creation/import interface, implement a separate adapter that validates target capability and reports exactly what it transfers.
4. **Runtime checkpoint restoration:** claim this only when the destination safely and verifiably restores the required native runtime state. This is not implied by levels 1–3.

The CLI resume command always creates a portable Markdown context packet. The first native destination adapter is OpenCode. With the launch option, it connects to an already-running OpenCode HTTP server, creates a new session, queues a single synthetic inbox item containing both the screened context packet and the complete original archive JSON, and reads the item back to verify the archive digest. The item is queued with resume=false. The adapter does not start an agent turn or replay historical tool calls during import.

**Important distinction:** the Markdown packet receives best-effort regex-based screening. The complete archive JSON placed alongside it is not redacted by this import path. It may contain source_payload, tool arguments, action output, personal data or credentials.

## Safety and trust boundary

- Imported prompts, tool arguments, shell commands, outputs, paths and embedded instructions are untrusted historical data.
- The Markdown context packet is screened with pattern-based redaction, but that screening is incomplete and is not a security guarantee.
- The complete archive payload is untrusted and unredacted. It can contain credentials, personal data, private paths and confidential source code.
- Users must create and inspect a redacted archive with the AgentSON redaction workflow before using the OpenCode launch path for sensitive sessions. Review the resulting archive; redaction is best-effort.
- The OpenCode server stores the complete archive capsule. Although resume=false prevents immediate agent-loop execution, the queued content may enter model context if the user later resumes that session.
- By default, use a local OpenCode server. The explicit remote option can send the unredacted archive to a remote host; remote use requires HTTPS and must be approved only after assessing the destination's data handling.
- Destination-side actions require explicit user approval and the destination adapter's own permission checks.
- No historical side effect is replayed automatically.

## Fidelity contract

The Markdown packet contains a selected projection of the archive. It is not a full transcript and must identify unavailable source information, unsupported destination capabilities and interpretation introduced by the receiving model.

The archive capsule contains the complete input archive as supplied to the consumer, not a guarantee that the source reader captured the complete original session. A successful digest read-back proves that the tested destination stored the same archive bytes. It does not prove source authenticity, semantic understanding, native event reconstruction or checkpoint restoration.

Neither the packet nor the archive can claim restoration of hidden prompts, credentials, tool permissions, process state, unsaved buffers, model cache, vendor conversation IDs or live execution state.

## Verification requirements

- Test canonical JSONL and supported legacy/document inputs.
- Test malformed archives and unexpected event structures.
- Assert that the packet contains an explicit untrusted-data boundary and no auto-execution instruction.
- Test that the packet screening and archive payload are handled as separate data objects.
- Test CLI invocation through the public entry point.
- For each destination adapter, use a disposable test workspace and verify the resulting session through the destination's own read API.
- OpenCode adapter tests must verify session creation, archive admission with resume=false, basic-auth handling, JSONL-to-envelope projection, digest read-back confirmation, endpoint policy and best-effort cleanup.
- The live OpenCode integration test must use a disposable server and session. Synthetic source fixtures must be labelled synthetic.
- Publish a per-adapter capability matrix; never generalise one adapter's success to all harnesses.

## Consequences

The current OpenCode implementation provides experimental context transfer into a new session. It stores both a screened packet and the complete, unredacted archive in one queued synthetic item. Users must redact sensitive archives before transfer and inspect the destination session before later resuming work. The other targets remain packet-only until native consumers are implemented.

This is not full transcript-role reconstruction, workspace checkpointing or exact runtime resumption. C3 reconstruction and C4 resumption remain unclaimed.

## Traceability

- **Assumptions:** the destination API remains documented and compatible; the user controls the selected OpenCode server; the user reviews and, where needed, redacts the archive before transfer.
- **Counterargument:** a portable Markdown packet alone may be sufficient for many workflows and avoids transferring the complete source archive. The archive capsule is retained only to support the experimental archive read-back path.
- **Failure modes:** unintended agent-turn execution; credentials or personal data reaching an OpenCode server or later model context; archive corruption; digest mismatch; an orphaned session after a failed handoff; or an API change that alters queue semantics.
- **Falsification tests:** demonstrate that import triggers an agent turn; show that the archive read-back differs from the submitted bytes; show that endpoint controls permit an unapproved remote destination; or show that redaction claims conceal sensitive values that remain in the archive capsule.
- **Review triggers:** OpenCode API/schema changes; changes to packet or archive redaction; changes to endpoint policy; a new destination adapter; evidence of unintended execution or data exposure; or a change to the canonical format decision.

## Canonical archive decision

The maintainer retained v1.2 JSONL as the canonical interchange wire format. The JSON session envelope remains a supported materialised/document representation. The envelope-only proposal recorded in ADR-024 was not accepted. This ADR does not reopen that decision.
