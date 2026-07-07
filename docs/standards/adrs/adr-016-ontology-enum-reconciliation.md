# ADR-016: Ontology ↔ Entry-Type Enum Reconciliation

**Status:** Proposed — recommendation below, decision pending
**Date:** 07 July 2026
**Author:** andiekobbietks

---

## Context

`spec/ontology.md` declares "exactly 12 primitives." The v1/v1.1 entry
enum disagrees with it in both directions:

- In the v1 enum, **not** in the ontology's 12: `context`, `querying`, `title`
- In the ontology's 12, **not** in the v1 enum: `handoff`, `presence`,
  `capabilities`, `user-feedback`, `system-event`, `stream-meta`,
  `observation`

ADR-014 (Proposed) covers only the `observation` case in isolation.
This ADR supersedes/subsumes ADR-014 by handling the full reconciliation
at once, since fixing `observation` alone and leaving the other six
mismatches would just relocate the same class of bug.

## Options

**A. v1 enum is legacy, ontology's 12 is the v2 target**
`context`/`querying`/`title` get deprecated with a migration note
(old files keep validating per ADR-001; new captures stop emitting
them). The ontology's 12 become the actual v2 enum, gated behind
ADR-015's schema-version decision.

**B. Merge into one enum — union of both sets**
Simpler to implement, but abandons the ontology's own "exactly 12" claim
on day one, which is a credibility problem the ontology doc would need
to be rewritten to acknowledge.

**C. Two enums, one per schema version, no shared "primitive" claim**
v1/v1.1 keep their existing 8 types (including `context`/`querying`/
`title`); v1.2 gets its own independent 12. Drop "exactly 12 primitives"
from the ontology doc as a v2-only description, not a universal claim.

## Recommendation (mine, not yet decided)

**Option C**, contingent on ADR-015 choosing "both versions coexist"
(Option A there). If v1.1 and v1.2 are genuinely different shapes for
different purposes, forcing one shared enum across both is the thing
that keeps causing contradictions. Rewrite the ontology's opening line
from "AgentSON defines exactly 12 event types" to "AgentSON v1.2's
streaming mode defines exactly 12 primitives" — a small wording fix
that makes the claim true again without touching either schema.

This also resolves ADR-014 as a side effect: `observation` is real and
required in v1.2, absent in v1.1, and that's fine once the two aren't
claiming to share one enum.

## Decision

*(blank — yours to make; also formally closes ADR-014 once decided)*

## Consequences

*(fill in once decided)*

## See also
- [ADR-014](adr-014-observation-entry-type-missing-from-spec.md) — the narrower case this ADR subsumes
- [ADR-015](adr-015-canonical-schema-version.md) — the version-coexistence decision this ADR depends on
- [ADR-017](adr-017-presence-live-channel-scope.md) — whether `presence`/`capabilities` survive at all, independent of enum placement
- [ADR-018](adr-018-adopt-project-brief-as-scope-charter.md)
- [`spec/ontology.md`](../../../spec/ontology.md)
- [`tests/features/spec_validation/10-spec-validation.feature`](../../../tests/features/spec_validation/10-spec-validation.feature) — scenario pinning this exact mismatch
