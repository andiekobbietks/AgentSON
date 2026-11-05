# ADR-025: Cross-Harness Context Continuation

**Status:** Proposed implementation baseline  
**Date:** 05 November 2026  
**Decision Makers:** AgentSON maintainer  
**Related:** ADR-015, ADR-017, ADR-023, ADR-024

## Context

The product objective is to let a session produced by one AI coding harness be captured, represented, validated, exchanged, inspected and potentially resumed in another without silently losing meaning or provenance.

A transcript export is not a runtime checkpoint. Harnesses own private state such as system/developer instructions, model-specific conversation identifiers, tool permissions, credentials, process state, editor buffers, workspace state and provider-specific memory. A portable archive cannot recreate those elements unless the source exposes them and the destination defines a supported import contract.

The repository already has source readers and a canonical JSONL export path on the PR #62 branch. Existing importers convert selected external formats into AgentSON; they do not constitute destination-harness session restoration.

## Decision

Implement cross-harness continuation in capability layers:

1. **Archive portability:** read canonical AgentSON JSONL and supported legacy session documents without rewriting the source archive.
2. **Context continuation packet:** deterministically render the available event history, source metadata, provenance and fidelity limitations into a Markdown packet suitable for a new destination-harness session.
3. **Destination adapter:** where a harness provides a documented, stable import or session-creation interface, implement a separate adapter that validates the target capability and reports exactly what it restores.
4. **Runtime checkpoint restoration:** only claim this when the destination can safely and verifiably restore the required native runtime state. This is not implied by levels 1–3.

The CLI implementation is the agentson resume INPUT --target TARGET [--output FILE] command. It always creates a portable Markdown continuation packet. The first native destination adapter is OpenCode: agentson resume INPUT --target opencode --launch connects to an already-running OpenCode HTTP server, creates a new session, queues the packet with resume=false, and reads the session inbox back to verify the handoff. The adapter does not start an agent turn or execute historical tool calls. Other target profiles remain packet-only until their own adapters are implemented.

## Safety and trust boundary

- Imported prompts, tool arguments, shell commands, outputs, paths and embedded instructions are untrusted historical data.
- A continuation packet must explicitly tell the receiving model not to execute historical commands or treat transcript content as current system/developer instructions.
- Credentials, access tokens, private keys and environment secrets must never be copied into a continuation packet.
- Redaction should be applied before sharing sensitive archives. The resume command must not imply that redaction is complete or that arbitrary source payloads are safe.
- Destination-side actions require explicit user approval and the destination adapter's own permission checks.
- No historical side effect is replayed automatically.

## Fidelity contract

The continuation packet preserves only fields represented in the AgentSON archive. It must distinguish preserved source evidence, normalised rendering, unavailable source information, unsupported destination capabilities and interpretation introduced by the receiving model.

The packet must not claim restoration of hidden prompts, credentials, tool permissions, process state, unsaved buffers, model cache, vendor conversation IDs or live execution state.

## Verification requirements

- Test canonical JSONL and legacy document inputs.
- Test malformed archives and unexpected event structures.
- Assert that user messages, assistant answers, tool actions, tool results, timestamps and source payloads remain inspectable.
- Assert that the packet contains a clear untrusted-data boundary and no auto-execution instruction.
- Test CLI invocation through the public entry point.
- For each destination adapter, use a disposable test workspace and verify the resulting session via the destination's own read API.
- OpenCode adapter tests must verify session creation, packet admission with resume=false, basic-auth handling, and read-back confirmation. The live integration check must use a disposable OpenCode server and session.
- Publish a per-adapter capability matrix; never generalise one adapter's success to all harnesses.

## Consequences

The first implementation supports practical context transfer into a new destination session. OpenCode has a native API adapter that stores the AgentSON packet in a fresh session without triggering an agent turn; the other destinations use the portable packet workflow only. This is not full transcript-role reconstruction, workspace checkpointing or exact runtime resumption. Those remain separate capabilities requiring destination-specific import contracts and round-trip verification.

## Canonical archive decision dependency

This ADR does not settle the outstanding conflict between ADR-015's JSONL-canonical position on the PR #62 branch and ADR-024's single-session-envelope position on the PR #60 branch. The resume packet reader accepts the currently supported JSONL and legacy document forms, but maintainers must reconcile the archive contract before either conflicting decision is merged.
