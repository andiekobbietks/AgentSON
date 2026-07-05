# ADR-006: Why GitHub Pages Over Vercel/Netlify

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The project needs a way to host the landing page, viewer, SOPs, and documentation. Vercel and Netlify are popular choices, but they add another account, another billing surface, another dependency.

## Decision

Use GitHub Pages (free, built into the repo).

## Consequences

### Positive
- Free — no additional cost
- No additional account setup
- Deploys automatically on push to master
- Custom domain support if needed later

### Negative
- No server-side rendering (static files only)
- Limited build minutes
- `.nojekyll` workaround needed for Google Fonts URLs

### Neutral
- All pages are static HTML/CSS/JS — no SSR needed
- The SOP renderer uses client-side markdown parsing
- If the project outgrows GitHub Pages, migration to Cloudflare Pages is straightforward
