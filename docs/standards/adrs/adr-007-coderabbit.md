# ADR-007: Why CodeRabbit for Reviews (and Why Not Required)

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

Solo projects benefit from code review, but there's no team to do it. CodeRabbit provides automated AI code review for free on open-source projects. But it has rate limits on the free tier.

## Decision

Use CodeRabbit for PR reviews, but do NOT make it a required status check.

## Consequences

### Positive
- Free code review on every PR
- Catches issues before manual review
- No cost

### Negative
- Free tier has rate limits that vary by project popularity
- If rate limited, a required check would block all merges
- Not as thorough as human review

### Neutral
- CodeRabbit reviews when it can, never blocks
- The 4 branch protection rules (PR required, no force push, no deletion, linear history) work independently
- Can upgrade to paid tier later if needed

## Why Not Required

For a solo project, making CodeRabbit required means:
- If it's rate limited → PRs stuck forever
- If it's down → PRs stuck forever
- If the service shuts down → PRs stuck forever

The owner can always review their own PRs. CodeRabbit is a helpful assistant, not a gatekeeper.
