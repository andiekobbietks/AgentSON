# ADR-013: `finetune`, `push`, and `pull` violate the core/downstream scope rule

**Status:** Proposed
**Date:** 2026-07-06

## Context

The project's own scope rule states:

> Core `agentson` package = spec + CLI only (import/export/validate/
> search/render). Anything that *uses* the format for a downstream
> purpose (fine-tuning, archiving, replay tooling, analytics) belongs
> in a separate package (`agentson-train`, `agentson-archive`, etc.)
> that depends on core, not the reverse.
>
> Litmus test: "Is this defining AgentSON, or using AgentSON?"
> Defining → core. Using → downstream package.

A code review of `cli/main.py` (prompted by building a manual `.agentson`
reconstruction of an agent session and checking what the actual CLI
surface supports) found three registered subcommands that fail this
test:

- `finetune` (`cmd_finetune`) — exports an `.agentson` file to
  Unsloth/Olive fine-tuning format. This is explicitly the
  `agentson-train` use case named in the scope rule itself.
- `push` (`cmd_push`) — pushes a session to Supabase.
- `pull` (`cmd_pull`) — pulls sessions from Supabase, with search/filter
  options.

`push`/`pull` are archiving/sync functionality — the `agentson-archive`
use case, also named explicitly in the scope rule.

All three are *using* AgentSON (consuming an already-captured episode
for a downstream purpose), not *defining* it. None of the three touch
`spec/v1.json`, and none are things a user needs merely to capture,
validate, or inspect a session — the stated core verbs.

This is not a hypothetical scope question — it is the exact violation
the litmus test was written to catch, discovered by applying the test
to the shipped code rather than only to new proposals.

## Decision

**Proposed, not yet actioned** (this ADR documents the finding and the
options; the actual code change is a separate PR after a decision is
made):

- Remove `finetune`, `push`, and `pull` from `cli/main.py`'s core
  subcommand registration.
- Move `cmd_finetune` (and its Unsloth/Olive export logic) into a new
  `agentson-train` package, depending on `agentson` core for reading
  `.agentson` files.
- Move `cmd_push`/`cmd_pull` (and the Supabase client code) into a new
  `agentson-archive` package, same dependency direction.
- Core's registered subcommands become exactly the five named in the
  scope rule: `export`, `import`, `validate` (see ADR-014's companion
  finding — this doesn't exist yet either), `search`, `render`.

## Consequences

- **Positive:** Core stays narrow and matches its own documented scope.
  A user who only wants to capture and inspect sessions doesn't need
  Supabase client dependencies or fine-tuning format logic pulled in.
- **Negative:** Existing users of `agentson finetune`/`push`/`pull` (if
  any, given v0.1 pre-launch status) would need to install a second
  package. Given the project is pre-launch, this is the cheapest point
  to make this change — the cost only grows with adoption.
- **Neutral:** No spec change required. This is purely a CLI/package
  boundary decision.

## Open question for Andie

Should this be actioned before or after v0.1 launch? Pre-launch, this
is a clean cut with no migration cost to real users. Post-launch, it
becomes a breaking change requiring a deprecation path.
