# ADR-008: AgentSON as the Open Interchange Layer for AI Workflow Traces

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

Cursor was acquired for $60B. The IDE market was worth $2.5B. The reporting is clear about what drives the price: $4B in annualized revenue at a ~15x multiple, 70% of the Fortune 1000 as paying customers, the fastest B2B software company to reach that ARR scale, a proprietary Composer model, and strategic fit with SpaceX/xAI's compute and chip supply chain.

Workflow-trace data is a legitimate, documented part of why AI-coding companies are valued highly. Eric Paulsen's comment that trace data is "quite valuable for training reinforcement learning models" is a genuine and reasonable claim about one input among many. But it is not the same as "that's the whole valuation." The $60B reflects revenue, customers, model, infrastructure, team, and strategic positioning — not just the dataset.

Every AI coding tool is accumulating session traces: OpenAI (Codex), Anthropic (Claude Code), Google (Gemini Code Assist), MiniMax, Antigravity IDE, Chrome DevTools AI. Each stores it in their own proprietary format. None of them export it. None of it is portable.

The data exists. The format doesn't — until now.

## Decision

AgentSON is the open interchange layer for AI agent workflow traces. Every `.AgentSON` file captures the full trace of what happened during an AI-assisted session: prompts, thoughts, actions, code, observations, and outcomes.

AgentSON does not compete with Cursor's valuation. It solves the adjacent, real problem of vendor lock-in for individual users' own session data.

## Consequences

### What This Means

1. **The format is the product.** Not the viewer, not the CLI, not the cloud service. The JSON schema is what makes traces portable.

2. **Every reader is a data pipeline.** The opencode reader, the MiniMax reader, the Chrome DevTools reader — each one is a pipeline that converts proprietary trace data into an open format.

3. **Every exporter is a training pipeline.** The `finetune.py` exporter converts AgentSON traces into Unsloth/Olive training format. The data that tools keep captive, AgentSON makes trainable.

4. **Portability breaks lock-in.** If you capture your sessions in AgentSON, you can switch tools without losing context. If you train on AgentSON data, you're not dependent on one vendor's dataset.

### The Market Reality

| Who | Has trace data | Exports it | Lets you train on it |
|---|---|---|---|
| Cursor | Yes (70% Fortune 1000) | No | No |
| OpenAI | Yes | Partial (API only) | No |
| Anthropic | Yes | No | No |
| Chrome DevTools | Yes | MD export (unstructured) | No |
| **AgentSON** | **You own it** | **Yes (JSON)** | **Yes (finetune.py)** |

### Why Open Wins

- **Network effects:** Every new reader makes the format more valuable. Every new exporter makes the format more useful.
- **Community:** Open formats attract contributors. Proprietary formats attract lawyers.
- **Trust:** Users trust an open format they can inspect. They don't trust a black box.
- **Longevity:** Open formats survive company shutdowns. Proprietary formats die with the company.

### Risk

The risk is that a major player (OpenAI, Google, Microsoft) creates their own "open" format that becomes the de facto standard through distribution. AgentSON's defense is that it's already working, already tested, already has readers for multiple tools, and isn't controlled by any single company.

## The Thesis

AI coding assistants keep session data captive. Every tool stores traces in proprietary databases with no export API. Users lose their context when they switch tools. Researchers can't train on cross-tool data.

AgentSON provides a portable, user-owned alternative to proprietary session-trace lock-in. Not because AgentSON competes with or replaces the value Cursor's acquisition reflects — but because the problem of data portability is real, unsolved, and worth building for its own sake.

The value isn't "giving away a $60B thing for free." The value is solving a real problem that nobody else has solved: making your AI session data yours.
