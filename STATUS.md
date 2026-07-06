# Status (last updated: 2026-07-06T13:15:00Z, by: Claude web session)

**Read this before starting any work on this repo. Update it before ending any session that changed repo state.** See SOP-016 (Work-In-Progress Governance).

**Note: this repo currently has 10 open PRs — well over the WIP limit of 3 set in SOP-016.** No new branches/PRs should be opened until this queue is worked down, per SOP-016 Rule 1.

## Open PRs and what's blocking each

- **#12** (`focused-landing`): Focused landing page rewrite. **BLOCKED — merge conflict ("dirty")** against current `master`, caused by the direct `v0.2.0` push (#24) landing on the same file after this PR was opened. Needs manual conflict resolution before it can merge.
- **#13** (`coderabbitai/chat/385d3b2`): Case studies page + shared CSS theme extraction. Based on `focused-landing` (#12), not `master` — effectively blocked until #12's conflict is resolved.
- **#17** (`fix/claude-code-outcome-test-fixture`): Fixes a stale synthetic test fixture (not a reader bug). Clean, independent, ready to merge.
- **#18** (`docs/add-adr-viewer`): Adds a second, amber-themed ADR browsing UI (adr-viewer accordion) alongside the existing hand-built one. Clean, independent.
- **#19** (`docs/add-adr-011-012-to-index`): Adds ADR-011/012 links to the existing ADR index. Clean, independent. Note: PR #25 also adds these same two links as a side effect — if #19 merges first, that part of #25 becomes a no-op.
- **#20** (`feature/copilot-chat-reader`): New Copilot Chat reader. Had a real path-traversal vulnerability and a hardcoded-model correctness bug — both fixed and confirmed resolved by CodeRabbit. Clean, independent.
- **#22** (`coderabbitai/utg/b7d041b`): CodeRabbit-generated tests for the adr-viewer theming code. **Base commit predates PR #18** — these tests exercise files that only exist once #18 is merged. Cannot be honestly verified as passing until then.
- **#23** (`docs/sop-015-agent-operating-procedure`): SOP-015 (agent operating procedure) + Bug Response Procedure in coding-standards.md + fixes 43 stale `.AgentSON` casing instances in older SOPs. Clean, independent.
- **#25** (`docs/adr-013-014-cli-scope-and-observation-enum`): ADR-013 (finetune/push/pull core-scope violation) and ADR-014 (missing `observation` entry type in spec) — both Proposed, awaiting Andie's decision. Clean, independent.
- **#30** (`feat/streaming-chrome-agent`): Chrome CDP streaming agent, ChatGPT/Claude export, MCP adapter, PII redactor, Excel exporter, 50 dogfooded OpenCode sessions. 5 real CodeRabbit findings fixed and confirmed (Python SyntaxError, PowerShell escaping, CDP response-nesting bug, a concurrency wedge bug, a replay-security spec gap). 2 findings were stale (didn't reproduce against current file content) and were explicitly not fixed. 5 more stale-cased example files renamed. Full secret scan run — clean. CodeRabbit's own check was still "pending" as of last check, not a real blocker.

## Active branches not yet in a PR

- None known as of this update.

## Known live issues (already filed as GitHub issues, not just notes)

- **#26**: Core CLI scope violation — `finetune`/`push`/`pull` registered as core subcommands (see ADR-013, PR #25)
- **#27**: `spec/v1.json` missing `observation` entry type, used by real readers (see ADR-014, PR #25)
- **#28**: No `validate` subcommand exists despite being named in core CLI scope
- **#29**: Dead code — `cmd_search` defined twice in `cli/main.py`

## Do NOT do this right now

- Do not open new branches/PRs — WIP limit is already blown (10 open vs. limit of 3). Work the existing queue down first.
- Do not re-fix `.AgentSON` casing issues without checking `git log`/existing PRs first — this has already been fixed multiple times across different branches today because sessions weren't checking for each other's work.
- Do not assume a CodeRabbit finding is current without re-verifying against the actual file first (see SOP-016 Rule 3) — at least one finding today referenced a line number that no longer existed.
- Do not generate a new broad OAuth device-flow token without checking whether one is already live for this session first.

## Security notes (resolved, kept here for record)

- A fine-grained PAT was found committed in `examples/opencode_ses_0cbcf80cdffeBI6iMSKzP1GXoA.agentson` on `feat/chrome-devtools-mcp-integration` — **revoked**, confirmed dead (401) before continuing.
- A classic PAT (`ghp_iumvM8n4...`) was found in a pasted session-notes document — **confirmed already dead** (401) on check.
- Current working credential: broad `gho_...` OAuth device-flow token (full private repo access), per Andie's stated default preference (see Claude's memory). Revoke when no longer needed for active work.
