# ADR-003: Why Vendor Neutrality Matters

**Status:** Accepted
**Date:** 04 July 2026
**Author:** Andrea Enning

---

## Context

Every AI platform wants you to stay in their ecosystem. OpenAI wants you to use their API. GitHub wants you to use Copilot. Google wants you to use Gemini. Each provides session history in their own format, with their own export tools, with their own limitations.

This creates lock-in. If you build workflows around one vendor's format, switching costs become prohibitive.

## Decision

AgentSON must be vendor-neutral. Every external service is optional. Every core feature works offline.

## Consequences

### Positive
- Users can switch tools without losing context
- The format survives vendor shutdowns
- No single company controls the standard

### Negative
- Must maintain readers for every tool
- Some vendor-specific features won't map cleanly
- No integration partnerships (yet)

### Neutral
- The format starts with Chrome DevTools, opencode, MiniMax, Antigravity
- More readers = more value, but each reader is optional
- The spec can be extended without breaking old files
