# ADR-011: Project name "AgentSON" kept, ".ason" file extension rejected

**Status:** Accepted
**Date:** 2026-07-04

## Context

Early in the project, ".ason" was considered as the literal file extension
(paired with the "AgentSON" project/brand name), on the assumption that a
short extension would be cleaner for tooling and file associations.

A naming-clearance search turned up two existing, unrelated projects
already using ".ason":

1. **`hemashushu/ason`** — an established general-purpose data
   serialization format, with its own binary variant and a Rust reference
   implementation, registered as MIME type `application/ason`.
2. **`ason-format/ason`** — "Aliased Serialization Object Notation," a
   JSON-compression format built specifically for reducing LLM prompt
   token costs (npm package `@ason-format/ason`, CLI `npx ason`).

The second collision is a direct hit on AgentSON's own niche (AI +
structured data tooling). Anyone with LLM-tooling experience would
reasonably expect a `.ason` file to be a token-compressed JSON blob, not
an agent session transcript. This is a real MIME-type and expectation
collision, not a cosmetic naming coincidence.

A separate check on "AgentSON" as a standalone project/brand name found
no conflicts — the only adjacent hit was the unrelated `AGENTS.md`
convention (a markdown file convention, not a serialization format).

## Decision

- Keep **"AgentSON"** as the project, brand, and package name.
- Do **not** use `.ason` as a file extension.
- Files use `.agentson` as the extension, or plain `.json` with an
  internal `"$schema": "agentson-v1"` field where a distinct extension
  isn't needed (following the precedent of formats like
  `.devcontainer.json`, which don't require their own extension to be
  identifiable).

## Consequences

- No collision risk with either existing `.ason` ecosystem.
- Slightly longer extension (`.agentson` vs `.ason`), traded deliberately
  for unambiguous identification.
- The naming/trademark check performed was a manual, point-in-time
  search (UK/EU/US trademark databases, PyPI, npm, GitHub org
  availability, UK Companies House) — not a paid legal clearance search.
  Should be re-verified before any serious commercial commitment (see
  PRD.md, Risks).
