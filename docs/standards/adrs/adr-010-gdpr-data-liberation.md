# ADR-010: AgentSON as GDPR/EU AI Act Data Liberation Tool

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The parallels are exact:

**Unsloth** made fine-tuning accessible to everyone. Before Unsloth, you needed a GPU cluster and a PhD. After Unsloth, you could fine-tune a 7B model on a single GPU in hours. Unsloth didn't create new capability — it democratized existing capability.

**AgentSON** makes session data export accessible to everyone. Before AgentSON, your AI coding sessions were locked in proprietary databases with no export API. After AgentSON, you can export, search, replay, and fine-tune on your own data. AgentSON doesn't create new capability — it democratizes existing capability.

The difference: Unsloth democratized model training. AgentSON democratizes data ownership.

## The Legal Right

Users already have the legal right to their data. AgentSON makes it exercisable.

### GDPR Article 20 — Right to Data Portability

> "The data subject shall have the right to receive the personal data concerning him or her, which he or she has provided to a controller, in a structured, commonly used and machine-readable format."

Every AI coding tool stores your prompts, code, and session data. Under GDPR, you have the right to receive that data in a machine-readable format. Most tools don't provide this. AgentSON does.

### EU AI Act — Transparency Requirements

> "Providers of AI systems shall ensure that the system is designed and developed in such a way that natural persons are informed that they are interacting with an AI system."

> "Users of AI systems that generate synthetic text... shall ensure that the outputs of the AI system are marked in a machine-readable format."

The EU AI Act requires transparency about AI-generated content. AgentSON captures the full trace — what the AI did, what it generated, what tools it used — in a machine-readable format that satisfies transparency requirements.

### What This Means

| Right | Legal basis | Tool status | AgentSON solution |
|-------|-------------|-------------|-------------------|
| Access your data | GDPR Art. 15 | Most tools: no export | AgentSON exports everything |
| Export your data | GDPR Art. 20 | Most tools: no portable format | AgentSON is the portable format |
| Transparency | EU AI Act Art. 52 | Most tools: opaque | AgentSON captures full trace |
| Right to explanation | GDPR Art. 22 | Most tools: no audit trail | AgentSON has every thought + action |

## The Unsloth Analogy

| Aspect | Unsloth | AgentSON |
|--------|---------|----------|
| What it democratized | Model fine-tuning | Session data export |
| Before | GPU cluster + PhD needed | No export API, vendor lock-in |
| After | Single GPU, hours | One CLI command, portable JSON |
| Who benefits | Individual developers, small teams | Individual developers, small teams |
| Legal basis | N/A | GDPR Art. 20, EU AI Act Art. 52 |
| Business model | Open source, freemium | Open source, Apache 2.0 |

## Decision

AgentSON is the Unsloth of session data. Not because it's technically similar — but because it serves the same role in the ecosystem:

1. **Democratizes access** — makes something previously only available to big players accessible to everyone
2. **Legal backing** — GDPR and EU AI Act give users the right; AgentSON makes it exercisable
3. **Open source** — Apache 2.0, no telemetry, no vendor lock-in
4. **Community-driven** — every new reader makes the format more valuable

## Consequences

### The Positioning

AgentSON isn't competing with Cursor, Claude Code, or Copilot. It's the tool that lets users exercise their legal rights over the data those tools generate.

- Cursor keeps your data captive → AgentSON exports it
- Claude Code embeds spyware → AgentSON gives you ownership
- Copilot stores traces in Microsoft servers → AgentSON makes them portable

### The Value Proposition

> "You have the legal right to your data. AgentSON is how you exercise it."

This is stronger than "open format for session traces" because:
- It's legally grounded (GDPR + EU AI Act)
- It's emotionally resonant (data ownership, privacy, sovereignty)
- It's practically useful (export, search, fine-tune)
- It's defensible (legal right, not just nice-to-have)

### The Market

Every developer using AI coding tools has this right. Most don't know how to exercise it. AgentSON teaches them.

- 5M+ Cline users (BYOK = they care about data)
- 6.5M opencode monthly devs (open source = they care about ownership)
- 147K GitHub stars on opencode (community = advocacy)
- Every Cursor user locked in (frustration = demand)

## The Thesis

Unsloth democratized model training. AgentSON democratizes data ownership.

Both serve the same constituency: individual developers and small teams who want the capabilities that were previously only available to big labs. Both are open source. Both are backed by legal rights (Unsloth by open research norms, AgentSON by GDPR and the EU AI Act).

The $60B question isn't whether this data is valuable. It's who gets to use it.

AgentSON's answer: you do. It's your legal right. Here's how to exercise it.
