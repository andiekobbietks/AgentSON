# SOP-016: Work-In-Progress Governance (Multi-Session / Multi-Agent)

**Version:** 1.0
**Date:** 06 July 2026
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP exists because of a specific, observed failure mode: with
multiple sessions/agents (Claude web, Claude Code, another CDP-focused
session, CodeRabbit's own auto-PRs) all working on this repo in
parallel, without a shared gate or shared status file, the following
things happened in a single day:

- 10 branches open at once, several unaware of each other's existence.
- The same bug (`.AgentSON` casing) reintroduced on a fresh branch
  after already being fixed on another.
- `master` moved (a direct push, `v0.2.0`) between two checks of the
  same PR, turning a clean merge into a conflict.
- A CodeRabbit finding referenced a line number that no longer existed
  in the file, because the file had changed since the review ran.
- A real, live GitHub token got committed and pushed publicly before
  anyone caught it — found only because a later session happened to
  scan for it.

None of this was one session "doing it wrong." It's what happens by
default when parallel work has no shared limit and no shared status.
This SOP is the fix: **treat the person as the boss who sets a WIP
limit and demands a sync check, not as a peer dev free to open
whatever they want on a local machine nobody else touches.**

---

## Rule 1: Work-In-Progress limit

**No more than 3 open PRs at a time, hard limit, not a target.**

Before opening a new branch/PR, check the current open count:

```bash
TOKEN="..."
curl -s -H "Authorization: Bearer ${TOKEN}" \
  "https://api.github.com/repos/andiekobbietks/AgentSON/pulls?state=open" \
  | python3 -c "import json,sys; print(len(json.load(sys.stdin)))"
```

If the count is at or above 3: **do not open new work.** Either help
merge/close something in the existing queue first, or explicitly ask
Andie whether the limit should flex for this specific case (rare,
should be the exception that's named as an exception, not the default).

**Why 3:** small enough that no single person or session loses track
of what's actually open, large enough that a natural review cadence
(one being reviewed while one is in progress and one is queued) isn't
artificially blocked.

---

## Rule 2: Sync-before-branch

Every new branch starts with, no exceptions:

```bash
git checkout master
git pull origin master
```

Then check: has anything landed on `master` since the last time this
session touched the repo, that the new work should account for? If
yes, read what changed (`git log` since the last known commit) before
branching from it — don't branch blind.

---

## Rule 3: Verify state between actions, not just before starting

**The failure mode this rule targets is not "too much parallel work" —
it's git commands (or any actions) running one after another with no
checkpoint asking "is the state I'm building on still true?" before the
next one assumes it.** Today, every individual command succeeded. The
state between them silently drifted anyway, because nothing checked.

Concrete cases from today, all the same root cause:

- A branch went from mergeable to conflicted mid-session because
  nothing re-checked `master` after a commit landed elsewhere — the
  next action (reviewing the PR) assumed the state from an earlier
  check was still current.
- A CodeRabbit finding was acted on by trusting its cited line number,
  without re-reading the file first — the file had changed since the
  review ran, and nothing checked before treating the finding as
  actionable.
- A leaked credential was called "redacted" because a git-history fix
  (soft reset) was performed, but nobody separately verified the
  credential's actual live/revoked status before treating the incident
  as closed — two different questions ("is it out of history" vs. "is
  it still valid") got collapsed into one.
- The same casing bug was fixed on multiple branches independently,
  because nothing checked "has this already been fixed elsewhere"
  before repeating the work.

**The rule, stated precisely: any time an action depends on the result
of a previous action (yours or another session's), re-verify that
result immediately before acting on it — do not carry it forward as an
assumption, no matter how recently it was true.** This applies:

- Between every git command that depends on repo state (pull before
  branching, re-check mergeable status before merging, re-read a file
  before editing it based on a stale description of its contents)
- Between finding a bug and fixing it (see
  `docs/standards/coding-standards.md`'s Bug Response Procedure, step 1
  — reproduce against current state, not against memory of the report)
- Between a security action and calling it resolved (a git-history
  rewrite and a credential-revocation check are two different actions;
  neither implies the other)
- Between reading another session's notes/status and acting on them —
  treat any pre-existing description of repo state as a hypothesis to
  verify, not a fact to build on

Sync-before-branch (`git pull origin master` before a new branch) is
one instance of this rule, not the whole of it — it only covers the
start of a task. This rule covers every step during it.

---

## Rule 4: One shared status file, mandatory read-first

Any session working on this repo — Claude web, Claude Code, another
agent, a human — reads `STATUS.md` at repo root **before** starting
work, and updates it **before** ending a session that changed
anything.

`STATUS.md` contains, at minimum:

```markdown
# Status (last updated: <ISO timestamp>, by: <session/tool identifier>)

## Open PRs and what's blocking each
- #N: <one line: what it does, what's blocking merge, if anything>

## Active branches not yet in a PR
- <branch>: <what it's for, is it safe for another session to touch>

## Known live issues (not yet filed as GitHub issues)
- <anything found but not yet turned into an issue/ADR>

## Do NOT do this right now
- <anything explicitly paused/blocked/being handled elsewhere>
```

This is the single artifact that would have prevented today's
duplicate-casing-bug and stale-branch problems — a session that reads
"5 stale-cased files already fixed on `feat/streaming-chrome-agent`,
don't refix elsewhere" before starting doesn't reintroduce the same
fix on a different branch.

**This file is not optional documentation — treat a missing update to
it, at the end of a session that changed repo state, as an incomplete
task**, the same way an unrun test is an incomplete task.

---

## Rule 5: Master moving under you is expected, not a surprise

Given Rule 1-4 reduce it but don't eliminate it: if `master` has moved
since a branch was created (check via `git log master ^<branch>` or
by noticing a PR flip from "clean" to "dirty"), that is not an error
state to panic over — it's the expected cost of parallel work. Rebase
or merge `master` into the branch, resolve conflicts, re-verify tests
still pass, continue. Don't treat drift as a reason to abandon
in-progress work, and don't treat it as something that "shouldn't
happen" — it will, by design, when more than one thing is in flight.

---

## Related documents

- `docs/standards/coding-standards.md` — Bug Response Procedure (Rule 3
  above is this SOP's branch-governance-specific version of that
  procedure)
- `SOP-015-AI-Agent-Repository-Operating-Procedure.md` — the mechanics
  of branch → PR → merge this SOP's rules apply on top of
- `STATUS.md` (repo root) — the artifact Rule 4 requires
