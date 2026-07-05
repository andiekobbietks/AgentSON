# AndieKobbieTech — Operating Manual

**Version:** 1.0
**Date:** 05 July 2026
**Author:** Andrea Enning (AndieKobbieTech)

---

## What This Is

This is the full operating manual for how I build, think, and work. It covers:

- **Mental Models** — how I approach problems
- **Coding Standards** — how I write code
- **ADRs** — why I made specific decisions
- **SOPs** — step-by-step procedures for recurring tasks
- **Workflow Rules** — how I manage work

---

## Mental Models

How I think about problems before I write code.

| Model | What It Means |
|---|---|
| [Simplicity First](mental-models.md#simplicity-first) | The simplest solution that works is the best solution |
| [Own Your Data](mental-models.md#own-your-data) | Never depend on a vendor for something you can store yourself |
| [Build to Learn](mental-models.md#build-to-learn) | Build things to understand them, not just to use them |
| [Constraint-Driven](mental-models.md#constraint-driven) | Limitations are features, not bugs |
| [One File, One Truth](mental-models.md#one-file-one-truth) | A single file should contain everything needed |

→ [Read Mental Models](mental-models.md)

---

## Coding Standards

How I write code. Non-negotiable.

| Standard | Rule |
|---|---|
| [No PII in Repo](coding-standards.md#no-pii-in-repo) | Never commit personal file paths, names, or identifiers |
| [No Telemetry](coding-standards.md#no-telemetry) | No phone-home, no analytics, no tracking |
| [Vendor Neutral](coding-standards.md#vendor-neutral) | Never depend on one company's API or format |
| [Single File Output](coding-standards.md#single-file-output) | One .AgentSON file = one complete session |
| [Minimal Dependencies](coding-standards.md#minimal-dependencies) | If you can do it in 20 lines, don't import a library |
| [Test Against Real Data](coding-standards.md#test-against-real-data) | Synthetic test data lies. Real data tells the truth |

→ [Read Coding Standards](coding-standards.md)

---

## Architecture Decision Records (ADRs)

Why I made specific decisions. Each ADR captures context, decision, and consequences.

| ADR | Decision |
|---|---|
| [ADR-001](adrs/adr-001-agentSON-format.md) | Why AgentSON exists as a format |
| [ADR-002](adrs/adr-002-json-over-sqlite.md) | Why JSON files over SQLite databases |
| [ADR-003](adrs/adr-003-vendor-neutral.md) | Why vendor neutrality matters |
| [ADR-004](adrs/adr-004-amber-design.md) | Why amber phosphor design tokens |
| [ADR-005](adrs/adr-005-nightscout.md) | Why Nightscout over proprietary CGM systems |
| [ADR-006](adrs/adr-006-github-pages.md) | Why GitHub Pages over Vercel/Netlify |
| [ADR-007](adrs/adr-007-coderabbit.md) | Why CodeRabbit for reviews (and why not required) |
| [ADR-008](adrs/adr-008-trace-data-interchange.md) | AgentSON as the open interchange layer for AI workflow traces ($60B insight) |
| [ADR-009](adrs/adr-009-osi-open-interchange.md) | AgentSON as Open Interchange Format for OSI Open Source AI definition |

→ [Read ADRs](adrs/)

---

## Workflow Rules

How I manage work day-to-day.

| Rule | What |
|---|---|
| [Git Workflow](workflow.md#git-workflow) | Branch naming, commit messages, PR process |
| [PR Process](workflow.md#pr-process) | What goes in a PR, what gets reviewed |
| [Deployment](workflow.md#deployment) | How things get shipped |
| [Incident Response](workflow.md#incident-response) | What to do when something breaks |

→ [Read Workflow Rules](workflow.md)

---

## The Stack (Quick Reference)

```
DATA COLLECTION:
├── Juggluco (mother's phone)
├── FreeStyle Libre 2 (sensor)
└── Manual entry (CHWs in West Africa)

DATA STORAGE:
├── Nightscout (self-hosted)
├── AgentSON (.AgentSON files)
└── Supabase (optional cloud)

AI/ML:
├── MedGemma (Google HAI-DEF)
├── Fine-tuned glucose model
└── MedASR (speech-to-text)

ALERTS:
├── WhatsApp (whatsapp-web.js)
├── SMS (Africa's Talking)
├── Voice (Coqui TTS)
└── TV Dashboard

CLINICAL:
├── NHS FHIR (intu)
├── EMIS/SystmOne (when available)
└── GP reports (HTML/PDF)

DEVELOPER TOOLS:
├── Backstage (documentation portal)
├── AgentSON (session portability)
└── GitHub (version control)
```

---

## Principles

1. **User owns their data.** No cloud required. No account required.
2. **Free or self-funded.** No VC money. No paywalls for essential features.
3. **Transparent.** Open source, open format, open process.
4. **Practical.** Built for real people with real constraints (limited money, limited time, limited hardware).
5. **Honest.** If something doesn't work, say so. If something is experimental, label it.

---

*Built with love for carers, clinicians, and communities.*
