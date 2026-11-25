# ADR-007: CodeRabbit as an Optional Review Assistant

**Status:** Accepted  
**Date:** 05 July 2026  
**Clarified:** 25 November 2026

## Context

Automated review can identify potential bugs, security risks, documentation inconsistencies and maintainability issues. It cannot replace tests, maintainer judgement or a complete security review.

## Decision

Use CodeRabbit as an optional automated review assistant where it is enabled for the repository. Treat its findings as review input that must be checked against the current code and current branch.

CodeRabbit is not a required runtime dependency and must not be the only quality gate. Branch protection, required approvals, status checks, merge policy and repository permissions are controlled by GitHub repository settings and must be verified there; this ADR does not assert a fixed number of protection rules.

## Consequences

- A green CodeRabbit status is not equivalent to an approval or proof that all findings are resolved.
- Review comments can become stale after later commits; re-check the current head and line context.
- High-risk findings require reproduction and regression tests.
- Human review and CI remain independent quality controls.
