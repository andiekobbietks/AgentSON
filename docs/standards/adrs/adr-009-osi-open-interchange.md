# ADR-009: AgentSON as Open Interchange Format for OSI Open Source AI

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

The Open Source Initiative (OSI) has spent over a year debating the Open Source AI Definition (OSAID). The争论 centers on what "open source" means for AI systems:

- **Source code** — model architecture, training scripts
- **Model weights** — trained parameters
- **Training data** — the prompts, responses, code, and observations used to train
- **Inference pipeline** — how the model produces outputs

The OSAID focuses heavily on code and weights. But the most valuable component — the training data — has no open standard. Every AI company stores session traces in proprietary formats:

- Cursor: proprietary SQLite (valued at $60B)
- OpenAI: internal API-only format
- Anthropic: closed
- Google: closed

The data is the bottleneck. The format doesn't exist — until now.

## Decision

AgentSON is the Open Interchange Format (OIF) for AI training data. It provides:

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

The OSI has no standard for "what does open training data look like?" AgentSON answers that question.

## Consequences

### Why This Matters

1. **The $60B problem.** Cursor's value is proprietary training data. AgentSON makes the same data portable and open. If AgentSON becomes the standard, no single company can lock in the data moat.

2. **OSI has a gap, we fill it.** The OSAID defines what "open source AI" means but doesn't specify the data format. AgentSON is the missing piece — the open interchange format for the training data that powers AI systems.

3. **Fine-tuning is the pipeline.** `agentson finetune --format unsloth` converts AgentSON traces directly into training data. The format isn't just storage — it's the pipeline from session to training.

4. **Pioneering position.** While the OSI debates, we built. The first open format for AI training data is already working, tested across 5 tools, with 2 training exporters.

### The Market Reality

| Who | Has training data | Exports it | Lets you train on it |
|---|---|---|---|
| Cursor | Yes ($60B) | No | No |
| OpenAI | Yes | Partial (API only) | No |
| Anthropic | Yes | No | No |
| **AgentSON** | **You own it** | **Yes (JSON)** | **Yes (finetune.py)** |

### Risk

The risk is that a major player (OpenAI, Google, Microsoft) creates their own "open" training data format and uses distribution to make it the standard. AgentSON's defense: it's already working, already has readers for multiple tools, and isn't controlled by any single company.

## The Thesis

AI's biggest debate is about openness. The OSI is defining it. Companies are fighting over it. But nobody has built the actual infrastructure for open training data.

AgentSON is that infrastructure. Not a definition — a working format. Not a policy — a tool. The Open Interchange Format for the data that powers AI.

The $60B question isn't whether this data is valuable. It's who gets to use it.

AgentSON's answer: everyone.
