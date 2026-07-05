# Workflow Rules

How I manage work day-to-day.

---

## Git Workflow

### Branch Naming

```
feat/<short-description>     — new feature
fix/<short-description>      — bug fix
docs/<short-description>     — documentation only
refactor/<short-description> — code cleanup
```

Examples:
- `feat/chrome-devtools-reader`
- `fix/libre-csv-encoding`
- `docs/sop-renderer`

### Commit Messages

Format: `type(scope): description`

Keep under 72 characters for the first line. Add body if needed.

### Main Branch

`master` is the production branch. All changes go through PRs. No direct pushes.

---

## PR Process

### What Goes in a PR

- One logical change per PR
- Tests if adding new functionality
- Updated documentation if changing behavior
- No unrelated changes mixed in

### PR Title

Same format as commit messages: `type(scope): description`

### What Gets Reviewed

For a solo project, self-review is fine. But read the diff before merging. Check:
- No PII leaked
- No secrets committed
- Tests pass
- Documentation updated

### Merging

Use squash merge for clean history. The branch name becomes the commit message context.

---

## Deployment

### GitHub Pages

- Source: `master` branch, `/docs` folder
- Deploy: automatic on push to master
- `.nojekyll` required (Google Fonts URLs have `?` characters)

### Python Package

- Build: `python -m build`
- Publish: PyPI trusted publishing (OIDC, no stored tokens)
- Version: follow semver in `pyproject.toml`

---

## Incident Response

### Something Breaks

1. Check if it's a deployment issue (GitHub Pages build log)
2. Check if it's a code issue (run tests locally)
3. Check if it's a dependency issue (check for deprecations)
4. Fix, commit, push
5. Verify the build succeeds

### PII Leaked

1. Stop everything
2. Rewrite git history (orphan branch with clean commit)
3. Force push
4. Delete any cached branches
5. Document what happened

### Downstream Service Outage

1. Note which service is down
2. Document the impact
3. Wait for recovery
4. Add fallback if it happens again

---

## Mental Health Rules

- **No coding after midnight.** Tired code is buggy code.
- **Take breaks.** If you've been staring at the same problem for an hour, walk away.
- **Ship imperfect things.** Done is better than perfect. Fix it later.
- **Ask for help.** If you're stuck, say so. The AI is always available.

---

*Work should be sustainable. If the process burns you out, change the process.*
