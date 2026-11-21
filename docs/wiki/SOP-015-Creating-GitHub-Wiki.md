# Wiki SOP: Publishing the AgentSON GitHub Wiki

**Status:** Maintained procedure for the checked-in wiki mirror. Follow the repository root SOP-015 and SOP-016 for all repository governance.

## Important distinction

The repository's checked-in documentation mirror is under `wiki/`. The GitHub-hosted wiki, when enabled, is a separate Git repository ending in `.wiki.git`. Keep the two in sync only through an intentional, reviewed documentation change.

## Prerequisites

- Wiki feature enabled in the main GitHub repository.
- Git installed.
- Permission to edit the repository wiki.
- Authentication configured through Git Credential Manager, GitHub CLI or SSH.

## Clone the wiki repository

```bash
git clone https://github.com/andiekobbietks/AgentSON.wiki.git
cd AgentSON.wiki
```

If cloning fails, confirm the wiki exists and that your GitHub account has access. Do not place a token in the remote URL.

## Edit and publish

1. Copy or edit the relevant Markdown pages.
2. Check links, headings, schema versions and feature status against the source-of-truth files in the main repository.
3. Review the diff for personal data, secrets and stale commands.
4. Commit with a descriptive message.
5. Push using the configured Git credential helper or SSH remote.

```bash
git status
git diff --check
git add .
git commit -m "docs(wiki): align session interoperability guidance"
git push origin master
```

For the main repository, do not push directly to `master`: use the branch/PR workflow required by SOP-015 and SOP-016. The command above applies only to the separate wiki repository if its configured default branch is `master`.

## Security rules

- Never embed access tokens or passwords in a remote URL, script, wiki page or shell history.
- Never request or paste a broad account token for routine wiki updates.
- Prefer SSH or Git Credential Manager / GitHub CLI authentication.
- Revoke credentials that may have been exposed.
- Do not publish raw private session exports, personal data or secrets as wiki examples.

## Source-of-truth rule

The main repository files are authoritative for product and engineering claims:

- `PRD.md`
- `docs/architecture/session-interoperability.md`
- `spec/v1.2.json` and `spec/v1.2-entries.json`
- `spec/ontology.md`
- `spec/ADR-*.md`
- `docs/standards/coding-standards.md`

The wiki is a navigable explanation and mirror, not a competing specification. Update the source-of-truth document and its wiki mirror in the same reviewed change.
