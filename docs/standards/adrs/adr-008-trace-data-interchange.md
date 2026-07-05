# ADR-008: AgentSON as the Open Interchange Layer for AI Workflow Traces

**Status:** Accepted
**Date:** 05 July 2026
**Author:** Andrea Enning

---

## Context

Cursor was acquired for $60B. The IDE market was worth $2.5B. The 25x multiple exists because Cursor's real asset isn't the editor — it's the proprietary dataset of developer workflow traces: prompts, edits, debugging sessions, code changes, model responses.

As Eric Paulsen noted: *"Cursor's proprietary dataset of developer workflow traces, i.e. prompts, edits debugging sessions, etc. which as you know is quite valuable for training reinforcement learning models."*

James Stephenson confirmed: *"That's the whole valuation, basically."*

Every AI coding tool is accumulating this data: OpenAI (Codex), Anthropic (Claude Code), Google (Gemini Code Assist), MiniMax, Antigravity IDE, Chrome DevTools AI. Each stores it in their own proprietary format. None of them export it. None of it is portable.

The data exists. The format doesn't — until now.

## Decision

AgentSON is the open interchange layer for AI agent workflow traces. Every `.AgentSON` file captures the same type of data that Cursor charges $60B to own: the full trace of what happened during an AI-assisted session.

## Consequences

### What This Means

1. **The format is the product.** Not the viewer, not the CLI, not the cloud service. The JSON schema is what makes traces portable.

2. **Every reader is a data pipeline.** The opencode reader, the MiniMax reader, the Chrome DevTools reader — each one is a pipeline that converts proprietary trace data into an open format.

3. **Every exporter is a training pipeline.** The `finetune.py` exporter converts AgentSON traces into Unsloth/Olive training format. The data that Cursor locks in, AgentSON makes trainable.

4. **Portability breaks lock-in.** If you capture your sessions in AgentSON, you can switch tools without losing context. If you train on AgentSON data, you're not dependent on one vendor's dataset.

### The Market Reality

| Who | Has the data | Exports it | Lets you train on it |
|---|---|---|---|
| Cursor | Yes (60B worth) | No | No |
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

AI coding assistants are the new IDE market. The data they generate is the new oil. Whoever controls the format controls the pipeline.

AgentSON makes that format open, portable, and user-owned.

The $60B question isn't whether this data is valuable. It's who gets to use it.

AgentSON's answer: everyone.
