# SOP-015: AI-Agent Repository Operating Procedure for AgentSON

**Version:** 1.0  
**Date:** 06 July 2026  
**Author:** Andrea Enning (AndieKobbieTech)

---

## Purpose

This SOP documents the exact repository workflow used by Claude (via its
bash/git tooling) to work on the AgentSON repo across a session, so that:

1. **You** can do the same steps manually from your own terminal.
2. **Any other agent with a shell/git-capable harness** (Claude Code, an
   autonomous coding agent, a fresh Claude session with the same tools)
   can pick up mid-task without re-deriving the workflow from scratch.

This is the "how we actually work" doc — the mechanics, not the design
decisions (those live in `docs/standards/adrs/`).

---

## Prerequisites

| Item | Requirement |
|------|-------------|
| **Git** | Any recent version |
| **GitHub access** | A fine-grained Personal Access Token (PAT), scoped to `andiekobbietks/AgentSON` only — see Step 1 |
| **Python** | 3.11+, with `pip install pyrefly pytest --break-system-packages` (or in a venv) |
| **Repo state** | A local clone; if starting fresh, `git clone https://github.com/andiekobbietks/AgentSON.git` |

---

## Core rule: `master` is protected

`master` has a branch protection rule: **all changes must go through a
pull request.** A direct `git push origin master` will be rejected with
`GH013: Repository rule violations found`. This is enforced, not a
suggestion — every step below assumes branch → PR → (Andie reviews and
merges) → pull latest.

---

## Step 1: Get a scoped token (per session / per agent)

Do **not** use a broad classic PAT or a full-account OAuth device-flow
token for repo work — scope tightly, every time:

1. Go to **https://github.com/settings/personal-access-tokens/new**
2. **Repository access** → "Only select repositories" → `andiekobbietks/AgentSON`
3. **Permissions** needed for the full workflow used in this SOP:
   - Contents: Read and write
   - Pull requests: Read and write
   - Issues: Read and write
   - Workflows: Read and write
   - Actions: Read and write
   - Pages: Read and write
   - Commit statuses: Read and write
4. Set an expiration (90 days is reasonable for ongoing work)
5. Generate, copy the `github_pat_...` string
6. **Revoke it when the task/session is done**, or let it expire — don't
   leave long-lived tokens active without a reason

Configure git to use it for this session:

```bash
TOKEN="github_pat_..."   # paste the real token, never commit this
echo "https://x-access-token:${TOKEN}@github.com" > ~/.git-credentials
git config --global credential.helper store
git config --global user.name "andiekobbietks"
git config --global user.email "andiekobbietks@users.noreply.github.com"
```

Setting `user.name`/`user.email` this way means commits show as authored
by Andie, not as a bot — matches the existing commit history.

---

## Step 2: Standard change workflow

For **every** change, no exceptions:

```bash
# 1. Start from a clean, up-to-date master
git checkout master
git pull origin master

# 2. Branch — name it for what it does, prefixed by type
git checkout -b fix/short-description
# or: feat/..., docs/..., chore/...

# 3. Make the change

# 4. Test it — see Step 3 before committing

# 5. Commit with a real message (what + why, not just "fix bug")
git add <files>
git commit -m "fix(scope): short summary

Longer explanation of what was wrong, why, and how this fixes it.
Reference the specific bug/behavior, not just 'improves X'."

# 6. Push the branch
git push -u origin fix/short-description
```

---

## Step 3: Test before calling anything done

Per `CONVENTIONS.md`, this isn't optional:

```bash
# Run whatever test file(s) are relevant
python3 tests/test_<relevant>.py
# or, if pytest-based:
python3 -m pytest tests/test_<relevant>.py -v

# Then, always, on every file you touched:
pyrefly check <files you changed>
```

**"Tested" means it actually ran and passed** — not "I wrote code that
should work." If there's no existing test for what you changed, write
one before claiming it's done. If you can only test against synthetic
data, say so explicitly rather than implying it's been verified against
something real.

---

## Step 4: Open the PR

Using the GitHub API directly (works from any shell with `curl`, no `gh`
CLI dependency):

```bash
TOKEN="github_pat_..."
curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/andiekobbietks/AgentSON/pulls" \
  -d '{
    "title": "fix(scope): short summary",
    "head": "fix/short-description",
    "base": "master",
    "body": "## Summary\n\nWhat changed and why.\n\n## Testing\n\nWhat was actually run, what passed, what real vs synthetic data was used."
  }'
```

The response includes `html_url` — that's the link to share. **Do not
merge it yourself unless explicitly told to.** Default is: open the PR,
report the link, wait for Andie's review.

If told to merge:

```bash
curl -s -X PUT -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/andiekobbietks/AgentSON/pulls/<NUMBER>/merge" \
  -d '{"merge_method":"squash"}'
```

---

## Step 5: CHANGELOG discipline

Every PR that fixes a bug or adds a capability gets a CHANGELOG.md entry
under `## [Unreleased]`, in the same file as the code change (same PR,
not a follow-up). Format:

```markdown
## [Unreleased]

### Fixed
- **Short bug name**: what was actually wrong, root cause, how it's
  verified fixed now (which test, real vs synthetic).

### Known issues (flagged, not yet fixed)
- Anything found but deliberately not fixed in this PR — say why it's
  being left, not just that it exists.
```

Never fold multiple unrelated fixes into one vague bullet. Never claim
something is fixed without saying how it was verified.

---

## Step 6: Cutting a release (after merge)

Decide **patch vs. minor** first:

- **Patch** (`0.1.1`, `0.1.2`, ...): bug fixes only. Nothing in
  `spec/v1.json` changed, no new CLI commands, no new capability —
  just things that were supposed to work now actually working.
- **Minor** (`0.2.0`): spec changes, new CLI commands, new reader/importer
  capability, anything that changes what a user can *do*.

Once merged:

```bash
git checkout master
git pull origin master

# Rename the Unreleased CHANGELOG section to the dated release
# (do this as its own tiny PR, same branch → PR → merge flow as above —
# master is protected, this has no exception)

# After that PR is merged and pulled:
git tag -a v0.1.X -m "v0.1.X - one-line summary"
git push origin v0.1.X

# Publish the GitHub Release using the CHANGELOG section as the body
TOKEN="github_pat_..."
curl -s -X POST -H "Authorization: Bearer ${TOKEN}" \
  -H "Accept: application/vnd.github+json" \
  "https://api.github.com/repos/andiekobbietks/AgentSON/releases" \
  -d '{
    "tag_name": "v0.1.X",
    "target_commitish": "master",
    "name": "v0.1.X — one-line summary",
    "body": "<the CHANGELOG section content, verbatim>",
    "draft": false,
    "prerelease": false
  }'
```

---

## Step 7: Scope discipline — the litmus tests

Before adding anything to the `agentson` core package, run it through:

> **"Is this defining AgentSON, or using AgentSON?"**
> Defining → core. Using → a downstream package (`agentson-train`,
> `agentson-archive`, etc.) that depends on core, not the reverse.

For changes to `spec/v1.json` specifically:

> Does this improve **fidelity, portability, replayability, or
> analyzability** of a captured episode? If not, it doesn't belong in
> the schema, however useful it might be elsewhere.

If a change fails either test, it doesn't go in `agentson` core — flag
it and suggest where it *does* belong instead of silently including it.

---

## Step 8: Housekeeping — token cleanup

At the end of a session or task:

```bash
rm -f ~/.git-credentials
```

And revoke the token on GitHub's side at
**https://github.com/settings/tokens?type=beta** if it's no longer
needed — local file deletion doesn't revoke it remotely.

---

## Quick reference: what NOT to do

- ❌ Push directly to `master` (it will be rejected)
- ❌ Merge your own PR without being told to
- ❌ Claim something is "tested" when only pyrefly/syntax was checked, not actual behavior
- ❌ Use a broad/classic PAT or a full-account OAuth token for routine work
- ❌ Add downstream-purpose code (training, archiving, analytics) to core `agentson`
- ❌ Bundle unrelated fixes into one commit/PR without saying so clearly
- ❌ Leave a long-lived token active after the task is done

---

## Related documents

- `CONVENTIONS.md` — the engineering principles this SOP operationalizes
- `docs/standards/adrs/` — architecture decisions (the *why*, not the *how*)
- `CHANGELOG.md` — historical record this SOP requires you to maintain
- `PRD.md` — product scope and status
