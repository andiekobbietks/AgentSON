# Wiki SOP: Publishing the AgentSON GitHub Wiki

**Status:** Maintained procedure for publishing the checked-in wiki source.

## Important distinction

The maintained, checked-in source for wiki pages is under docs/wiki/. The root wiki/ directory contains historical redirect pages only. The GitHub-hosted wiki, when enabled, is a separate Git repository ending in .wiki.git. Keep it in sync only after the checked-in source has been reviewed and merged.

## Prerequisites

- Wiki feature enabled in the main GitHub repository.
- Git installed.
- Permission to edit the repository wiki.
- Authentication configured through Git Credential Manager, GitHub CLI or SSH.

## Clone the wiki repository

~~~bash
git clone https://github.com/andiekobbietks/AgentSON.wiki.git
cd AgentSON.wiki
~~~

If cloning fails, confirm the wiki exists and that your GitHub account has access. Do not place a token in the remote URL.

## Edit and publish

1. Edit the source page under docs/wiki/ in the main repository.
2. Check links, headings, schema versions and feature status against the source-of-truth files.
3. Review the diff for personal data, secrets and stale commands.
4. Submit the main-repository documentation change through its branch/PR workflow.
5. After review and merge, copy the approved docs/wiki pages into the separate wiki clone.
6. Check the wiki diff, commit and push using the configured Git credential helper or SSH remote.

~~~bash
git status
git diff --check
git add .
git commit -m "docs(wiki): align AgentSON wiki mirror"
git push origin master
~~~

The push above applies only to the separate wiki repository if its configured default branch is master. Do not push directly to the main AgentSON master branch; follow SOP-015 and SOP-016.

## Security rules

- Never embed access tokens or passwords in a remote URL, script, wiki page or shell history.
- Prefer SSH or Git Credential Manager / GitHub CLI authentication.
- Revoke credentials that may have been exposed.
- Do not publish raw private session exports, personal data or secrets as wiki examples.

## Source-of-truth rule

The main repository files are authoritative:

- README.md, PRD.md and STATUS.md
- docs/architecture/
- spec/v1.2-entries.json, spec/v1.2.json and spec/ontology.md
- spec/ADR-*.md
- docs/standards/

The wiki is a navigable explanation and mirror, not a competing specification. Update the source-of-truth document and its wiki mirror in the same reviewed change.
