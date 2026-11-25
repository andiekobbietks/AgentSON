# SOP-015: AI-Agent Repository Operating Procedure

**Status:** Current repository procedure  
**Version:** 2.0  
**Last reviewed:** 25 November 2026

## Purpose

Define the safe, repeatable workflow for human and agent-assisted changes to the AgentSON repository.

## Non-negotiable rules

1. The protected default branch is changed through reviewed pull requests, never by direct push.
2. Follow SOP-016's hard limit of three open pull requests unless the maintainer explicitly approves a named exception.
3. Re-check repository state, branch head, PR mergeability, review threads and required checks immediately before an action that depends on them.
4. Treat automated review as advisory. A green status is not approval and does not prove all findings are resolved.
5. Never claim a feature is complete without tests and evidence appropriate to its capability level.
6. Do not commit credentials, private session exports, raw health data or unredacted user data.

## Authentication

Preferred options:

- GitHub CLI: authenticate with the browser-based flow using gh auth login, then verify with gh auth status.
- Git Credential Manager on supported systems.
- SSH keys with an appropriately scoped GitHub account.

Do not:

- Store a personal access token in plaintext ~/.git-credentials.
- Put a token in a Git remote URL, source file, script, issue, PR comment or chat.
- Use a broad classic token or full-account OAuth token for routine repository work.
- Paste a token into a command that will be saved in shell history.

If a fine-grained token is genuinely required for an automated task, restrict it to this repository and the minimum permissions needed, use an approved secret store or short-lived environment injection, set an expiry, and revoke it when the task ends. Never enable the plaintext credential.helper store for this workflow.

## Standard change workflow

~~~bash
gh auth status
gh auth setup-git
git checkout master
git pull --ff-only origin master
git status --short
git checkout -b docs/short-description
~~~

Make the smallest coherent change. Before committing:

~~~bash
git diff --check
python -m pytest -q
~~~

Run focused tests first, then the relevant complete test suite and package checks. Use the repository's current instructions for the exact matrix. Do not claim tests passed unless they ran against the exact commit being reported.

Commit and push the branch:

~~~bash
git add <reviewed-paths>
git commit -m "docs(scope): describe the change"
git push -u origin docs/short-description
gh pr create --fill
~~~

Use the actual branch prefix and commit type appropriate to the work.

## Bug response and review

1. Reproduce the reported failure against the current branch.
2. Check whether it exists on the current default branch.
3. Read the current file and review thread; do not trust stale line numbers.
4. Fix the smallest confirmed cause.
5. Add a regression test or a clear reason why a test cannot be added.
6. Re-run the reproduction and relevant suite.
7. Reply to the review finding with the fix and evidence. Resolve a thread only when the underlying issue is actually fixed.

## Merge gate

Before merge, verify all of the following against the current PR head:

- The base and head are current and mergeable.
- Required CI checks passed on that exact head.
- Required human approvals are present.
- No unresolved blocking security, correctness or data-loss finding remains.
- The diff contains only intended files.
- The PR queue remains within SOP-016's limit or has an explicit exception.
- The maintainer has approved the merge.

Use the GitHub UI or GitHub CLI only after these conditions are satisfied. Never force-push, bypass branch protection, or use an API merge request to evade required checks or approvals.

## Security and data handling

- Use synthetic fixtures by default. A C1 reader claim requires a sanitised, permissioned, version-identified real source export.
- Pattern-based redaction is best-effort; inspect output before sharing.
- Keep session archives, logs, health data and credentials out of public fixtures.
- If a credential is exposed, revoke it with the issuing provider. Removing it from Git history does not revoke it.
- Report security incidents through the repository's documented process.

## Related procedures

- SOP-016: Work-In-Progress Governance
- docs/standards/coding-standards.md
- AGENTS.md
- STATUS.md
