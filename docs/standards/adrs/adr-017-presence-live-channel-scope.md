# ADR-017: `presence` / Live-Channel Semantics — Core or Strip?

**Status:** Proposed — recommendation below, decision pending
**Date:** 07 July 2026
**Author:** andiekobbietks

---

## Context

`spec/v1.2.json`'s own description states it adds "streaming (JSONL),
multi-agent handoff, presence, and live channel semantics for
**real-time inter-agent collaboration**." Applying [ADR-018](adr-018-adopt-project-brief-as-scope-charter.md)'s
spec-only litmus test (fidelity / portability / replayability /
analyzability of a *captured episode*) to each primitive individually:

- `handoff` (control transferred from agent A to B at time T) — passes.
  It's a fact about what happened in the episode.
- `capabilities` (agent self-describes available operations at capture
  time) — passes. It's a fact about the episode's context.
- `presence` (`online`/`offline`/`busy`/`idle` status) and "live channel
  semantics" — these describe *live coordination infrastructure*, not a
  property of a captured episode. This is the same distinction argued
  earlier when the question was "does AgentSON solve shared reality":
  provenance/capture (core) vs. live multi-agent consensus (downstream).

## Options

**A. Strip `presence` and live-channel semantics from v1.2 entirely**
Keep `handoff` and `capabilities`. Move any future live-coordination
concept to a downstream `agentson-bus`/`agentson-consensus` package
concept (already discussed, unbuilt) that would *consume* AgentSON
traces as its audit trail, not extend the spec.

**B. Keep `presence` as a non-normative extension field**
Allowed in a file, validated if present, but explicitly documented as
"not required for a valid AgentSON file, useful only if a downstream
live-coordination consumer wants a hint." Weaker signal than a strip,
but doesn't throw away work already done in v1.2.json if it turns out
someone's depending on it.

**C. Keep as-is, argue presence is itself a captured fact**
("the agent *was* busy at time T is a fact about the episode.")
Weakest option — a status snapshot only matters operationally to a live
consumer deciding what to do next; after the fact, "was busy" carries no
replay/analysis value a timestamp+action pair doesn't already give you.
Likely fails the litmus test on scrutiny.

## Recommendation (mine, not yet decided)

**Option A.** This is the most consistent with the litmus test as
written and with the "Agentic Internet" tagline conversation — the
honest claim is "the provenance layer a live-coordination system would
need underneath it," not the live-coordination layer itself. Stripping
now, while v1.2 has shipped in zero production files, costs nothing;
leaving it costs a spec that quietly claims more than the project's own
positioning says it does.

## Decision

*(blank — yours to make)*

## Consequences

*(fill in once decided — determines exact WP2 schema diff for v1.2)*

## See also
- [ADR-015](adr-015-canonical-schema-version.md) — determines whether this even ships as v1.2 or gets folded differently
- [ADR-016](adr-016-ontology-enum-reconciliation.md) — `presence`'s fate here also removes/keeps it from the enum question
- [ADR-018](adr-018-adopt-project-brief-as-scope-charter.md) — litmus test this ADR applies
- [ADR-009](adr-009-osi-open-interchange.md) — the "open interchange for training data" positioning this decision keeps honest
- [`spec/replay-semantics.md`](../../../spec/replay-semantics.md) — note: replay *semantics* stays core regardless of this decision; only presence/live-channel is in question
