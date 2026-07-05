# ADR-012: AgentSON's relationship to academic trace-provenance literature

**Status:** Accepted
**Date:** 2026-07-05

## Context

During development, academic literature surfaced covering agent
execution traces, evidence tracing, and provenance — including taxonomies
of trace sources, trust functions, and frameworks like W3C PROV and
OpenTelemetry integration for AI agents. The overlap in subject matter
(agent traces, provenance, tool use, memory, cross-platform support)
raised the question of whether AgentSON was duplicating existing work.

## Decision

AgentSON and this academic literature are treated as **complementary, not
duplicative**, based on a clear difference in what each actually is:

| Aspect | AgentSON | Academic literature |
|---|---|---|
| Stage | Deployed, working system | Survey / conceptual analysis |
| Output | `.agentson` files, working CLI, PWA viewer | Papers, taxonomies |
| Contribution | Concrete readers/importers, export to Unsloth/Olive, search/replay | Frameworks, gap analysis, research directions |
| Audience | Developers building real tools | Researchers, academics |
| Verification | Tested against real exports, working code | Citation analysis, literature review |

AgentSON is the practical, implemented answer to "I need a working system
to capture/replay/search/fine-tune on agent sessions today." The academic
work is the theoretical answer to "how should the field think about trace
provenance." Neither substitutes for the other.

## Consequences

- No need to reposition, rename, or reframe AgentSON in response to
  adjacent academic publications in this space.
- Where useful, AgentSON's spec can reference relevant academic framing
  (e.g. W3C PROV concepts) as design input, without treating the
  literature as prior art that blocks the project.
- Future contributors/reviewers who raise "isn't this already covered by
  [paper]?" should be pointed to this ADR rather than re-litigating the
  comparison from scratch.
