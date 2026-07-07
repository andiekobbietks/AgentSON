# ADR-018: Adopt the Project Brief as the Governing Scope Charter

**Status:** Proposed
**Date:** 07 July 2026
**Author:** andiekobbietks

---

## Context

The brief that has been steering this project since 2026-07-06 — scope
discipline, the two litmus tests, the engineering conventions, the
"say what's tested" rule — was never itself an ADR. It lived as a
standing instruction (see [`docs/PROJECT-BRIEF.md`](../../PROJECT-BRIEF.md)),
which meant its rules could be *applied* inconsistently without any
single record forcing a check against them. That's exactly how the
v1.2 layer landed without triggering the litmus test in the first
place — the rule existed, but nothing pointed back to it as the
authority to consult.

This ADR doesn't introduce anything new. It promotes the brief's rules
from "instruction Andie happens to paste" to "recorded project law,"
the same status every other scope decision in this project already has.

## Decision

Adopt the scope-discipline section of the original brief verbatim as
binding project policy:

1. Core = spec + CLI only (import/export/validate/search/render)
2. Core litmus test: "defining AgentSON, or using AgentSON?"
3. Spec-only litmus test: fidelity / portability / replayability /
   analyzability of a captured episode, or it doesn't belong
4. Engineering conventions (tested-vs-written, real reference exports,
   Pyrefly-before-done, human-directed) apply project-wide, not just to
   code

And add the definition-of-done rule surfaced during the 2026-07-07
audit as a formal amendment (not present in the original brief, earned
by finding what its absence cost):

5. A spec change doesn't exist until it has an ADR applying the litmus
   test, a schema that enforces it, and one scenario validating a real
   example against it.

## Consequences

### Positive
- Every future ADR can now cite ADR-018 as "why this litmus test
  applies" instead of re-deriving it from an informal brief
- CONVENTIONS.md gets a canonical source to point to for rule #5
- The brief itself stays discoverable as history in
  `docs/PROJECT-BRIEF.md`, unchanged; this ADR is what makes its rules
  enforceable rather than merely stated

### Negative
- None identified — this formalizes existing practice, it doesn't
  change it

### Neutral
- This ADR is retroactive; it does not itself fix anything. See
  ADR-015/016/017 for the substantive decisions it exists to enable.

## See also
- [`docs/PROJECT-BRIEF.md`](../../PROJECT-BRIEF.md) — the brief this ADR formalizes
- [ADR-015](adr-015-canonical-schema-version.md) — first decision made under this charter
- [ADR-016](adr-016-ontology-enum-reconciliation.md)
- [ADR-017](adr-017-presence-live-channel-scope.md)
- [ADR-013](adr-013-cli-scope-violation-finetune-push-pull.md) — the litmus test already in action, pre-dating this ADR
- [ADR-014](adr-014-observation-entry-type-missing-from-spec.md)
- [`SOP-INDEX.md`](../../../SOPs/SOP-INDEX.md) — cross-linked catalogue of every SOP referenced across these ADRs
