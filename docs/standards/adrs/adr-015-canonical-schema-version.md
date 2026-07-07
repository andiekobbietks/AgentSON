# ADR-015: Canonical Schema Version

**Status:** Proposed — recommendation below, decision pending
**Date:** 07 July 2026
**Author:** andiekobbietks

---

## Context

Three schema files exist (`spec/v1.json`, `v1.1.json`, `v1.2.json`) with
no document stating which is canonical. Found during the 2026-07-07
audit (see [CHANGELOG `[Unreleased]`](../../../CHANGELOG.md), PR #34):

- v1 and v1.1 both require `id`/`tool`/`entries` — single-document shape
- v1.2 requires nothing, describes JSONL streaming — different shape
  entirely, not a superset
- `examples/dogfood-session-2026-07-06.agentson` declares `$schema: v1.1.json`
- `spec/adapter-spec.md` calls the v1.2 JSONL stream "canonical"
- 6 of 10 shipped examples are single-document; 4 are JSONL streams
- ADR-001 commits to backward compatibility being mandatory, but this
  has never been tested

## Options

**A. v1.1 canonical, v1.2 is a separate "stream mode," both real**
Single-document (v1.1) is the default/simple case. v1.2 streaming is an
explicitly opt-in mode for tools capturing live (a `handoff`-heavy
session, e.g. the Chrome DevTools MCP work), declared via `$schema` and
`mode: "jsonl"` in `stream-meta`. Neither supersedes the other.

**B. v1.2 supersedes v1.1 entirely; all captures move to streaming**
Simpler long-term (one shape), but breaks ADR-001's backward-compat
promise for every v1/v1.1 file already shipped, and forces a migration
tool that doesn't exist.

**C. v1.2 is downstream, not core**
Treat streaming capture as an `agentson-stream` package concept, keep
core single-document only. Fails the fidelity litmus test partially —
streaming capture is a legitimate fidelity improvement (captures as it
happens vs. reconstructed after) — so this likely over-corrects.

## Recommendation (mine, not yet decided)

**Option A.** It's the only option that keeps ADR-001's backward-compat
promise true without inventing a migration tool, and it matches what
your own examples already do in practice (6 single-doc + 4 stream,
already coexisting). It requires v1.2 to actually enforce something
(ADR-blocked-work: WP2), and a documented rule for how/whether a stream
can be flattened into a v1.1-shaped document for tools that only
understand the simple case.

## Decision

*(blank — yours to make)*

## Consequences

*(fill in once decided — will determine WP2's exact schema-repair shape)*

## See also
- [ADR-001](adr-001-agentSON-format.md) — backward-compat mandate this decision must honor
- [ADR-016](adr-016-ontology-enum-reconciliation.md) — the enum reconciliation this decision unblocks
- [ADR-017](adr-017-presence-live-channel-scope.md) — the litmus-test question for what v1.2 should contain
- [ADR-018](adr-018-adopt-project-brief-as-scope-charter.md) — the litmus tests this decision is judged against
- [`spec/adapter-spec.md`](../../../spec/adapter-spec.md), [`spec/replay-semantics.md`](../../../spec/replay-semantics.md), [`spec/ontology.md`](../../../spec/ontology.md)
- [SOP-015](../../../SOPs/SOP-015-AI-Agent-Repository-Operating-Procedure.md) — branch/PR process this decision will flow through
