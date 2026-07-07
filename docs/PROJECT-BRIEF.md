# The Project Brief

*If you found this file, you were curious enough. This is the standing
brief the project was steered by during its first week — preserved
verbatim below as a lineage document, with a correction layer on top,
because the project's own conventions forbid letting stale confidence
claims stand as current ones.*

---

## Current status (maintained, audit-honest)

As of 2026-07-07 (structured audit, findings reproduced not assumed —
see CHANGELOG `[Unreleased]` and PR #34):

- **v0.1 pre-launch, in remediation.** Built; *partially* tested.
- Known defects catalogued: `spec/v1.2.json` enforces nothing
  (`required: []`); `spec/ontology.md` contradicts the v1 entry enum
  (seven types divergent); no `agentson validate` CLI command exists;
  dependencies inverted (`requests` declared, `jsonschema` absent);
  `cmd_search` defined twice; no canonical-schema statement; the v1.2
  layer landed without ADRs.
- Repair path: **WP1** (ADR-015/016/017: canonical schema, ontology
  reconciliation, presence/live-channel strip) → **WP2** (schema repair)
  ∥ **WP3** (`validate` command, dependency fix, ADR-013 extraction) →
  **WP4** (Gherkin suite: 71 scenarios written, 1 of 13 families
  executed, 4 pass / 6 fail, failures traced to the schema-version
  issue) → **WP5** (docs sync).
- Definition-of-done for spec changes (pending CONVENTIONS.md): a spec
  change doesn't exist until it has (1) an ADR applying the litmus test,
  (2) a schema that actually enforces it, (3) one scenario validating a
  real example against it.

The scope rules and litmus tests below survived the audit unchanged —
the failures happened where they weren't applied, not where they were.

---

## The original brief (verbatim, 2026-07-06, pre-audit)

> Project: AgentSON — a vendor-neutral, append-only log format + Python
> CLI for capturing/validating/replaying AI agent session transcripts,
> plus a PWA viewer.
>
> Scope discipline (enforce this in every answer):
> - Core `agentson` package = spec + CLI only (import/export/validate/
>   search/render). It stays narrow, minimal deps (just jsonschema).
> - Anything that *uses* the format for a downstream purpose
>   (fine-tuning, archiving, replay tooling, analytics) belongs in a
>   separate package (agentson-train, agentson-archive, etc.) that
>   depends on core, not the reverse.
> - Litmus test for "does X belong in core": "Is this defining AgentSON,
>   or using AgentSON?" Defining → core. Using → downstream package.
> - Spec-only litmus test (for spec/v1.json itself): does it improve
>   fidelity, portability, replayability, or analyzability of a captured
>   episode? If not, it doesn't belong in the schema, however useful.
>
> Engineering conventions (antirez/DwarfStar-derived, in CONVENTIONS.md):
> - Say what's actually tested vs just written — never imply confidence
>   levels that aren't earned.
> - Test against real reference exports, not just synthetic examples.
> - Run pyrefly before treating anything as done.
> - AI-assisted, human-directed: I make the calls on design/correctness,
>   don't just accept "this works" claims.
>
> About me: Andie Kobbie, Cardiff, Wales, GitHub handle andiekobbietks.
> Also running AFJ Cardiff, AKCloud, LAMPForge PDE, and a Cognitive
> Taxonomy Protocol project — mention only if directly relevant to a
> question, don't assume overlap.
>
> Current status: v0.1 pre-launch. Core package + CLI + PRD + CONVENTIONS
> + PWA built and tested this session. Naming cleared UK/EU/US/PyPI/npm
> manually (not a paid legal search — flag if commercial stakes rise).

---

## The correction the original needed

One line of the original — "built and tested this session" — did not
survive contact with its own conventions. The audit found the tested
claim unearned: the CLI was missing a definitional command, the newest
schema could not fail validation, and zero behavioral scenarios had
executed. The fix wasn't abandoning the brief; it was applying its own
second bullet to itself. That's the whole lesson of this file, and why
it's preserved rather than deleted: the framework was right, and the one
place it broke was the one place it wasn't applied.

*"Agentic Internet powered by JSON — sorry, I meant AgentSON: 'cause you
deserve for your private sessions to be portable, in a format no vendor
controls."*
