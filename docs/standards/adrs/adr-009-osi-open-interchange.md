# ADR-009: AgentSON as Open Interchange Format for OSI Open Source AI

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The Open Source Initiative (OSI) has spent over a year debating the Open Source AI Definition (OSAID). The debate centers on what "open source" means for AI systems:

- **Source code** — model architecture, training scripts
- **Model weights** — trained parameters
- **Training data** — the prompts, responses, code, and observations used to train
- **Inference pipeline** — how the model produces outputs

The OSAID focuses heavily on code and weights. But the training data component has no open standard. Every AI company stores session traces in proprietary formats:

- Cursor: proprietary SQLite
- OpenAI: internal API-only format
- Anthropic: closed
- Google: closed

The format doesn't exist — until now.

## Decision

AgentSON is the Open Interchange Format (OIF) for AI agent session traces. It provides:

1. **Open schema** — JSON Schema v1.1 with trajectory semantics
2. **Cross-tool readers** — opencode, MiniMax, Antigravity, Chrome DevTools, ChatGPT
3. **Training exporters** — Unsloth (ShareGPT), Olive (chat-messages)
4. **User ownership** — no telemetry, no vendor lock-in, no cloud dependency

## The OSI Gap

| OSI OSAID Component | Status | AgentSON Coverage |
|---|---|---|
| Source code (model architecture) | Defined | Not in scope |
| Model weights | Defined | Not in scope |
| Training data format | **Undefined** | **AgentSON is this** |
| Inference pipeline | Partially defined | Not in scope |

The OSI has no standard for "what does open training data look like?" AgentSON answers that question — specifically for AI agent session traces, which are the most valuable and least portable type of training data.

## Consequences

### Why This Matters

1. **OSI has a gap, we fill it.** The OSAID defines what "open source AI" means but doesn't specify the data format. AgentSON is the missing piece — the open interchange format for session traces that power AI training.

2. **Fine-tuning is the pipeline.** `agentson finetune --format unsloth` converts AgentSON traces directly into training data. The format isn't just storage — it's the pipeline from session to training.

3. **Pioneering position.** While the OSI debates definitions, we built infrastructure. The first open format for AI agent session traces is already working, tested across 5 tools, with 2 training exporters.

4. **Real problem, real solution.** AI coding tools keep session data captive. Users lose context when switching tools. Researchers can't train on cross-tool data. AgentSON solves this — not by competing with any company's valuation, but by making individual users' data portable.

### The Market Reality

| Who | Has session traces | Exports it | Lets you train on it |
|---|---|---|---|
| Cursor | Yes (70% Fortune 1000) | No | No |
| OpenAI | Yes | Partial (API only) | No |
| Anthropic | Yes | No | No |
| Chrome DevTools | Yes | MD export (unstructured) | No |
| **AgentSON** | **You own it** | **Yes (JSON)** | **Yes (finetune.py)** |

### Risk

The risk is that a major player (OpenAI, Google, Microsoft) creates their own "open" training data format and uses distribution to make it the standard. AgentSON's defense: it's already working, already has readers for multiple tools, and isn't controlled by any single company.

## The Thesis

AI's biggest debate is about openness. The OSI is defining it. Companies are fighting over it. But nobody has built the actual infrastructure for open training data.

AgentSON is that infrastructure. Not a definition — a working format. Not a policy — a tool. The Open Interchange Format for session traces that power AI.

The value isn't competing with any company's valuation. It's solving a real problem that nobody else has solved: making your AI session data yours.

## See also
- [ADR-017](adr-017-presence-live-channel-scope.md) — keeps this ADR's "training data format" claim honest by keeping live-coordination out of scope
- [ADR-001](adr-001-agentSON-format.md), [ADR-008](adr-008-trace-data-interchange.md)
- [Full catalogue](../ADR-SOP-CATALOGUE.md)
