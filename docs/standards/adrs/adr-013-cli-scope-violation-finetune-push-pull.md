# ADR-013: Scope of Fine-Tuning and Remote Sync Commands

**Status:** Proposed; no accepted implementation decision  
**Date:** 06 July 2026  
**Reviewed:** 25 November 2026

## Context

AgentSON Core is intended to define and process a portable event format. Fine-tuning exports, remote archive synchronisation and hosted publishing are downstream workflows with different dependencies, security requirements and release cycles.

The original proposal grouped finetune, push and pull together. The current CLI still exposes a finetune command, while push/pull are not present as top-level commands in the current parser. This ADR has not been accepted or actioned.

## Proposal

Keep the core interchange contract and local archive operations small. Treat fine-tuning exports, remote synchronisation, registry publishing and platform services as optional downstream capabilities, with explicit dependencies and security boundaries.

Do not remove or relocate current commands solely on the basis of this proposal. Any scope change requires a maintainer decision, compatibility plan, tests and updated documentation.

## Consequences if accepted

- Optional downstream features should be isolated from core schema and reader dependencies.
- Core file validation, local inspection and supported export paths should remain useful without a hosted service.
- Fine-tuning exports must be described as transformations of available events, not as proof that the archive is complete or suitable for training.
- Remote sync and registry operations require authentication, transport security, retention and deletion policies.

## Open questions

- Should finetune remain in the main CLI as an optional subcommand or move to an extension?
- Is a remote push/pull interface required, and if so, which protocol and threat model apply?
- What compatibility and deprecation policy would protect existing users?

No decision is implied until this ADR is explicitly accepted.
