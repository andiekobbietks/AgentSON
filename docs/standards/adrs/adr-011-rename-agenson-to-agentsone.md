# ADR-011: Rename from agenson → AgentSON

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The original project name was **agenson** — a concatenation of "agent" + "json". The file extension was `.ason`.

When registering the project on npm, PyPI, and GitHub, `.ason` collided with existing projects:
- An npm package `ason` already existed
- GitHub URL `github.com/agenson` was taken
- The name was too generic to differentiate

Additionally, the original design used cyan/blue tokens (`#58a6ff`). When rebranding to AgentSON, the design tokens changed to amber phosphor (ADR-004).

## Decision

Rename from `agenson` → `AgentSON`, where:
- **Agent** = the AI agent
- **SON** = Session Object Notation (a play on JSON)

The file extension changed from `.ason` → `.AgentSON` (capital letters to prevent collisions and make it visually distinctive).

The schema evolved through:
1. `.ailog` (original prototype)
2. AgentSON v1 (`spec/v1.json`)
3. AgentSON v1.1 (`spec/v1.1.json` — trajectory semantics)

## Consequences

### Positive
- Distinctive name, no collisions on package registries
- `.AgentSON` extension is unique and self-documenting
- Capital letters make it visually distinct from other file formats
- Amber phosphor design differentiates from predecessor

### Negative
- Breaking change for anyone who used the original name
- Must update all documentation, URLs, and package metadata

### Neutral
- The rename happened before public release — no downstream users affected
- The format name "AgentSON" (Agent + Session Object Notation) is more descriptive than "agenson" (agent + json)
