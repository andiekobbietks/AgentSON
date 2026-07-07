# ADR-001: Why AgentSON Exists as a Format

**Status:** Accepted
**Date:** 04 July 2026
**Author:** Andrea Enning

---

## Context

Every AI coding agent stores session data in its own proprietary SQLite database. OpenAI has one schema, MiniMax has another, Chrome DevTools has a completely different structure. There is no standard format for exporting, sharing, or analyzing AI agent sessions.

When I switched from one tool to another, I lost all my context. When I wanted to compare how different agents handled the same problem, I couldn't. When I wanted to fine-tune a model on my own sessions, I had to write a different parser for every tool.

## Decision

Create a single, vendor-neutral JSON format (.AgentSON) that captures the full structure of an AI agent session: who said what, what was thought, what actions were taken, what results were observed.

## Consequences

### Positive
- Sessions are portable between tools
- One parser works for all sessions
- Fine-tuning pipelines can target a single format
- Sessions can be searched, sorted, and analyzed uniformly

### Negative
- Every tool needs a reader/converter
- The format must accommodate the lowest common denominator
- Some tool-specific features may not map cleanly

### Neutral
- The format will evolve (v1.0 → v1.1 → ...) as new tools emerge
- Backward compatibility is mandatory — old files must always work

## See also
- [ADR-015](adr-015-canonical-schema-version.md) — where the "v1.0 → v1.1 → ..." evolution promised here is actually being decided
- [ADR-009](adr-009-osi-open-interchange.md), [ADR-018](adr-018-adopt-project-brief-as-scope-charter.md)
- [Full catalogue](../ADR-SOP-CATALOGUE.md)
