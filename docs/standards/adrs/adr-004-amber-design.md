# ADR-004: Why Amber Phosphor Design Tokens

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The original `.ailog` page used a cyan/blue theme (`#58a6ff`). When rebranding to AgentSON, the design tokens needed to change to differentiate the new identity while maintaining readability.

## Decision

Use amber phosphor design tokens:
- Accent: `#ffb000` (amber)
- Background: `#0a0a08` (warm dark)
- Text: `#e8e0c8` (warm ivory)
- Success: `#a0d060`
- Error: `#e05040`
- Fonts: Space Mono (headings/code) + IBM Plex Sans (body)

## Consequences

### Positive
- Warm, distinctive look that stands out from GitHub's default blue
- High contrast for readability
- Consistent across all pages (landing, viewer, SOPs, 404)

### Negative
- Not a standard palette — harder to find matching UI components
- Amber on dark can be fatiguing in large blocks

### Neutral
- The design is ours — not borrowed from any framework
- Easy to change via CSS variables if needed later
