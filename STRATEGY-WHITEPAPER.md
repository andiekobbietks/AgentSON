# AgentSON: Preserving the Operational Life of AI Agents

**Strategy Whitepaper** — July 2026  
**License:** Apache 2.0 — free to share, adapt, and distribute  
**Repository:** https://github.com/andiekobbietks/AgentSON  

---

## What AgentSON Is

AgentSON asks: **what survives when the runtime disappears?** It preserves the **operational life of an AI agent** independently of the runtime that hosted it — every prompt, thought, tool call, observation, file change, and answer in one self-contained JSON file.

It is **not** a memory system (those answer "what should the agent remember?"). It is **not** a replacement for MCP (which answers "how does an agent call a tool?"). It is **not** a workflow provenance system like PROV-AGENT (which captures agent traces within an MCP-enabled runtime). It is **not** an observability platform (which answers "what happened inside this runtime?").

AgentSON answers a question none of those address: **how can one agent execution be represented, exchanged, replayed, and analysed independently of the runtime that produced it?**

```
          MCP                    Memory                Observability
     (communication)         (future recall)          (monitoring)
            │                       │                       │
            ▼                       ▼                       ▼
              Agent Runtime Layer
    ┌────────────┬───────────┬──────────────┬──────────┐
    │OpenClaw    │Claude Code│Cursor        │LangGraph  │
    │OpenAI SDK  │CrewAI     │AutoGen       │opencode   │
    │Cline       │Aider      │Gemini CLI    │Codex CLI  │
    └────────────┴───────────┴──────────────┴──────────┘
                            │
                            ▼
                     AgentSON file
              (portable episodic provenance)
                            │
            ┌───────────────┼───────────────┐
            ▼               ▼               ▼
        Replay        Evaluation         Compliance
        Training      Migration          Research
        
```

---

## The Problem

Every AI coding agent stores session data in a proprietary format. There is no shared wire format, no standard export API, and no way to move execution context between tools without lossy manual conversion.

| Tool / Runtime | Storage | Access | Granularity |
|----------------|---------|--------|-------------|
| opencode | SQLite (21 tables) | Local file | Full tool calls + thoughts |
| Claude Code | JSONL | Local file | Tool calls + results |
| Cursor | SQLite (state.vscdb) | Local file | Full tool calls |
| OpenClaw | Local database | Local file | Tool calls + orchestration traces |
| Chrome DevTools AI | Preferences JSON | Export → Markdown | Thoughts + actions |
| Claude Tag | claude.ai session page | Browser render only | Tool calls + thinking |
| ChatGPT | chat.openai.com DOM | No export | Messages only |
| LangGraph | Server-side storage | API-dependent | Graph state + tool calls |
| CrewAI / AutoGen | In-memory / files | Varies | Task + agent traces |

**Key observation:** Every tool stores traces. No tool exposes them through a standard format. Four of the eight above have no export API at all.

This fragmentation creates real costs:
- **Reproducibility:** Agent behaviour cannot be replayed outside its original runtime
- **Compliance:** GDPR Article 20 (right to data portability) is technically unexercisable
- **Training:** Fine-tuning datasets are vendor-locked
- **Research:** Cross-agent comparison requires N custom scripts for N tools

---

## The Format

A single `.AgentSON` file contains a complete session trace with typed events, explicit provenance tracking, and tool metadata.

```json
{
  "$schema": "https://agentson.dev/schema/v1.1.json",
  "id": "session-2026-07-04-001",
  "task": "Fix the authentication bug in the login flow",
  "outcome": "success",
  "tool": {
    "name": "opencode",
    "session_id": "ses_xxx"
  },
  "agent": {
    "name": "mimo-v2.5-free",
    "provider": "opencode"
  },
  "entries": [
    {"type": "user-query", "text": "Fix the auth bug", "timestamp": 1782300319717},
    {"type": "thought", "text": "Looking at the auth module...", "model": "mimo-v2.5-free"},
    {"type": "action", "tool": "bash", "code": "grep -r 'auth' src/", "status": "success"},
    {"type": "observation", "text": "Found 3 files", "correlation_id": "tc_001"},
    {"type": "answer", "text": "Fixed the null check in auth.py", "format": "markdown"}
  ]
}
```

Every event carries a **provenance confidence level**:

| Confidence | Meaning | Source |
|-----------|---------|--------|
| `confirmed` | Direct evidence | Native export / live capture |
| `inferred` | Stitched from overlapping sources | Temporal / content alignment |
| `estimated` | Reconstructed from heuristic | Gap-filling |
| `ml_generated` | SLM-generated, deterministically verified | Narrative mode |
| `unknown` | Gap marker — no data | Insufficient sources |

---

## The Pipeline

AgentSON reconstructs execution traces through three modes, depending on data availability:

**Forensic mode** (default): Post-hoc stitching of available exports. Gaps are marked explicitly. Nothing is fabricated. This satisfies GDPR compliance requirements.

**Narrative mode** (opt-in): Extends forensic mode by filling execution event gaps using a Generator-Verifier architecture — a small SLM proposes candidate events, a deterministic verifier hard-prunes violations, and a cost-bounded beam search selects optimal paths.

**Live mode** (browser extension): Contemporaneous capture at the communication layer. Sidesteps post-hoc reconstruction limits entirely. Full tool-call detail from claude.ai session pages, Slack message streams, and general page metadata.

A formal result governs what each mode can claim — the **Agent Execution Record (AER)** non-identifiability proof (arXiv 2603.21692):

> **Reasoning provenance cannot be faithfully reconstructed post-hoc from persisted state.**

AgentSON respects this: execution events are tractable, reasoning is not. All three modes respect this boundary. Live mode sidesteps it because capture is contemporaneous, not post-hoc.

---

# Part I: 7 Powers Moat Analysis

Strategic framework: Hamilton Helmer's *7 Powers* (2016).

## Power 1: Network Economies — PRIMARY MOAT

AgentSON becomes more valuable as more users join, across multiple dimensions:

| Dimension | Node → Edge | Value per new node |
|-----------|-------------|-------------------|
| **Tool coverage** | New reader → all `.AgentSON` files become more portable | Every new reader compounds |
| **Training corpus** | New `.AgentSON` file → better gap-filling SLM | Every session improves accuracy |
| **User adoption** | New user → more exports → more contributions | Community growth |
| **Hydration network** | N tools → N² cross-tool hydration pairs | Quadratic |

**The virtuous cycle:**

```
More readers → More exports → More .AgentSON files
                                         ↓
More training data → Better SLM gap-filling → Higher quality reconstruction
                                         ↓
More users → More reader contributions → More readers (loop)
```

**Threat:** Network Economies only exist after critical mass (~500 stars, ~20 tools). At zero users, the moat is zero. Adoption velocity is the binding constraint.

## Power 2: Switching Costs — SECONDARY MOAT

| Level | Cost to leave | Durability |
|-------|---------------|------------|
| Personal `.AgentSON` library | User's entire searchable AI history in the format | High |
| Cross-tool hydration | Workflow depends on AgentSON bridge | Medium |
| Custom readers | Organization writes readers for internal tools | High |
| Training pipeline | Fine-tuning pipeline consumes `.AgentSON` | Medium |

**The real lock-in:** it's not the format (JSON is trivial to copy). It's the **reconstruction pipeline** — 20+ reader implementations, the Generator-Verifier architecture, the AER-bounded compliance model, the cross-source stitching methodology. Estimated replication cost: 6-9 person-months for a determined competitor.

## Power 3: Counter-Positioning — DEFENSIVE MOAT

AgentSON's "business model" is **not owning the data** — it's standardising what everyone already has. Incumbents cannot replicate this because their business model depends on owning the trace.

```
Vendor strategy:   Capture trace → Lock user in → Monetize
AgentSON strategy: Export trace → Free user → Standardize
```

This is structurally identical to what **OpenAPI did to enterprise middleware** and **TCP/IP did to proprietary networks**.

| Vendor | Why they can't adopt AgentSON |
|--------|-------------------------------|
| Anthropic (Claude) | Exporting traces undermines switching costs |
| OpenAI (Codex CLI) | Full trace export exposes prompt structure |
| Cursor | Portable export reduces lock-in |
| Copilot | Trace data is valuable training signal |

**Risk:** A vendor could adopt the format as a feature — this would be good for adoption but dilute the counter-positioning. Mitigation: community-governed spec, not vendor-controlled.

## Power 4: Cornered Resource — EVOLVING MOAT

AgentSON's most defensible resource is the **multi-tool trace corpus** — the largest collection of cross-tool, real-world session traces. No single vendor can replicate this because their corpus is tool-specific. AgentSON's is cross-tool by design.

1. Every export contributes to the corpus
2. The corpus trains better gap-filling SLMs
3. Better SLMs make narrative mode more valuable
4. More value drives more adoption → more corpus contributions

Secondary resources: the reader implementation knowledge (33 tools reverse-engineered), the AgentSON format as reference standard, the GDPR compliance positioning (legally defensible via AER proof).

## Power 5: Process Power — OPERATIONAL MOAT

The three-mode reconstruction pipeline is a **superior process**, validated by converging academic research:

- **Generator-Verifier architecture** with hard-pruning constraints (HunterAgent, arXiv 2605.29269): 86.1% F1, 6.4% hallucination vs. 61.5% for unconstrained LLM
- **Cost-bounded beam search** with epistemic budget: halt on uncertainty rather than fabricating
- **AER-bounded provenance tracking**: legally defensible confidence levels

The verifier is the critical component. Hallucination reduction comes from deterministic hard-pruning (schema violations, temporal impossibilities, physical constraints), not from a better generator model. This is structurally identical to the **Ralph Loop** pattern — a small, fast generator with a strict external verifier achieves capabilities far beyond either component alone.

**Why this is hard to replicate:** Estimated 6-9 person-months to build an equivalent pipeline, plus ongoing maintenance of tool-specific readers as vendor schemas evolve.

## Power 6: Scale Economies — LIMITED MOAT

| Cost center | Fixed | Variable per user |
|------------|-------|-------------------|
| Reader development | ~1 week per tool | $0 |
| CLI tooling | ~2 person-months | $0 per install |
| Supabase cloud | ~$10-50/mo | Storage costs only |
| SLM training | ~$100-500 per model | ~$0.001 per prediction |

**Zero marginal cost structure.** Standard for open-source tooling.

## Power 7: Brand — ASPIRATIONAL MOAT

| Message | Audience |
|---------|----------|
| "The format that AI companies spend billions to own, AgentSON gives away for free" | Developers |
| "GDPR Art. 20 right to data portability, made exercisable" | Enterprise legal |
| "What OpenAPI did for REST APIs" | Technical decision-makers |
| "Apache 2.0 — open forever" | OSS community |
| "Provenance tracking: every event labeled confirmed/inferred/estimated/ml_generated" | Security/audit |

**Brand risk:** Pre-revenue, pre-community. Brand is aspirational until adoption creates authority. Publishing this strategy whitepaper publicly is itself a brand-building move — transparency that vendors cannot match.

---

# Part II: Technical Foundation — The antirez Lineage

Salvatore Sanfilippo (antirez), creator of Redis, has published a series of technical essays between 2024-2026 that independently validate AgentSON's architectural choices. His perspective comes from systems engineering — memory management, data structures, performance under physical constraints — not AI research, and converges on the same conclusions.

## The Lineage

### Pre-2023: The Redis Foundation

15+ years building an in-memory data store that lives or dies by memory bandwidth, cache locality, and latency predictability. This is the lens he brings to AI: **LLM inference is a memory management problem before it is a compute problem**.

### Jan 2024: Pragmatic Engagement (news/140)

LLMs are useful for coding but limited by context window size. The human's ability to communicate problems clearly is the binding constraint — not the model's architecture.

### Feb 2025: The Architectural Break (news/146)

**"Reasoning models are just LLMs."** DeepSeek R1, o1, and similar models are architecturally identical to standard LLMs — pure decoder-only autoregressive with next-token prediction. RL over chain-of-thought saturates latent capabilities from pre-training; it does not create new capabilities.

> "DeepSeek R1 is a pure decoder only autoregressive model. There isn't, in any place of the model, any explicit symbolic reasoning or representation."

**Relevance to AgentSON:** If there is no distinct "reasoning module," the AER distinction between reasoning provenance (intractable) and execution events (tractable) is not just legally convenient — it reflects the actual architecture. AgentSON correctly captures *what the agent did*.

### Jul-Aug 2025: Experience + Economics (news/154, news/155)

Human+LLM collaboration beats either alone. Autonomous agents still fail on complex tasks. The economic impact of AI may be deflationary — structurally different from previous technological revolutions.

### Feb 2026: Synthesis (news/157)

> "LLMs are differentiable machine trained on a space able to approximate discrete reasoning steps."

Chain-of-thought is "sampling in the model representations" — a form of internal search, not a separate reasoning process. RL with verifiable rewards is the next frontier. The ARC test transitioned from anti-LLM test to validation of LLMs.

### May 2026: Applied Systems (news/165, news/163)

**DwarfStar 4:** A from-scratch Metal inference engine proving local inference on consumer hardware can approximate frontier model quality. Achieved via aggressive asymmetric quantisation — trading precision for memory fit.

**AI cybersecurity is not proof of work:** The model's *intelligence level* is the cap, not sample count. Beyond a certain point, more iterations do not help. This formally states the **epistemic budget** concept that AgentSON's narrative mode implements as `B_max`.

### Jun 2026: The Memory Wall (news/167)

> "During token-by-token decoding, an LLM is almost entirely memory-bandwidth-bound, not compute-bound."

Prefill is compute-bound; decode is memory-bound. These require fundamentally different optimisations. AgentSON avoids both by being file-based — zero inference until query time.

## Convergence with AgentSON

| antirez argument | AgentSON design |
|-----------------|-----------------|
| Inference is memory-bandwidth-bound, not compute-bound (news/167) | File-based, zero-inference default. Avoid inference until query time. |
| "Reasoning models are just LLMs" (news/146) | AER reasoning-provenance boundary is architecturally valid, not just legally conservative |
| Epistemic budget: model intelligence I caps iteration M (news/163) | Narrative mode's `B_max` threshold — halt rather than fabricate |
| CoT is sampling in representations, not a separate process (news/157) | Reasoning provenance is not recoverable — execution events are the right target |
| Local inference at frontier quality is achievable (news/165) | Local-first, sovereign data architecture is viable |
| Small models + external verification beat large models alone (implicit) | Generator-Verifier architecture — the verifier, not the generator, is the hallucination barrier |
| AI centralisation is the real risk (news/158) | Open format, Apache 2.0, no telemetry, user-owned data |
| Ensemble for shared-nothing parallelism (news/167) | Cross-source stitching merges traces without shared infrastructure |

## The Unified Thesis

> **The bottleneck is memory bandwidth. The solution is small models in self-correcting loops. The application is structured trace reconstruction.**

```
Memory bandwidth bottleneck
    ↓ forces
Smaller, more efficient models
    ↓ which need
Self-correcting loops (Generator + Verifier)
    ↓ producing structured, verifiable outputs
AgentSON narrative mode (execution event reconstruction)
    ↓ applied to
The universal problem: vendor-locked session traces
```

---

# Part III: Strategic Recommendations

## Phase 1: Seed the Network (Now — Q3 2026)

| Action | 7 Powers lever |
|--------|----------------|
| Ship v0.2.0 with 10+ working readers | Network Economies |
| Make reader contribution easy (docs, templates) | Network Economies |
| Publish GDPR compliance model | Brand, Counter-Positioning |
| Target Cursor reader (RICE: 2700) | Network Economies |
| Submit to HN, Reddit, Dev.to | Brand |

**Key metric:** Weekly active users and `.AgentSON` files created.

## Phase 2: Build the Cornered Resource (Q4 2026 — Q1 2027)

| Action | 7 Powers lever |
|--------|----------------|
| Release narrative mode (SLM gap-filling) | Process Power |
| Build training corpus from user-contributed exports | Cornered Resource |
| Train a tiny AgentSON-specific gap-filling model | Process Power |
| Implement cross-tool hydration | Switching Costs |
| Publish academic paper (NeurIPS 2027 / CCS 2027) | Brand |

**Key metric:** Corpus size in `.AgentSON` files; SLM F1 score.

## Phase 3: Entrench the Moat (Q1 2027+)

| Action | 7 Powers lever |
|--------|----------------|
| Supabase managed instance (optional cloud sync) | Switching Costs |
| Pursue standards body recognition (IETF, W3C) | Cornered Resource |
| Enterprise compliance module (audit trails, RBAC) | Brand, Switching Costs |
| Integrate with fine-tuning platforms (Unsloth, Together) | Network Economies |

**Key metric:** Third-party integrations, enterprise procurement conversations.

---

# Part IV: Risk Analysis

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Vendors add structured export APIs | Medium (12-18mo) | Medium | AgentSON becomes universal format; readers become adapters |
| Open-source competitor emerges | Low-Medium | High | First-mover in network effects; Process Power moat |
| Adoption stalls at single-user | Medium | Critical | Healthcare wedge (FreeStyle Libre + NHS FHIR + GDPR Art. 20) |
| LLM architecture changes eliminate trace structure | Low | High | Format adapts; traces will always exist in some form |
| Regulatory landscape shifts | Low-Medium | Medium | Core value prop (portability) is not regulatory-dependent |

**The cold-start trap:**

```
Without enough users:
    → Few tool contributions
    → Sparse corpus
    → Weak gap-filling
    → Low value per user
    → No adoption growth
```

**Breakout scenario:** A vendor's breaking API change makes their export unavailable → users flood to AgentSON as the workaround.

**Sustainable growth path:** The diabetes monitoring use case (FreeStyle Libre 2 reader + Nightscout + NHS FHIR) provides a non-AI-tooling wedge. Health data needs portability more than coding data does — and GDPR Art. 20 is a stronger lever in healthcare than in dev tools.

---

# Part V: The Thesis

The space is moving fast. PROV-AGENT (arXiv 2508.02866, Aug 2025, IEEE e-Science 2025) extends W3C PROV for agent workflow provenance via MCP and observability — valuable for runtime-internal traceability, but assumes the runtime stays in place. MemIR focuses on typed long-term memory to prevent provenance-role confusion. Neither asks the question AgentSON answers:

> **What survives when the runtime disappears?**

AgentSON sits at the convergence of:

1. **A unique research question** — Everyone is discussing provenance, memory, governance, and MCP, but they generally assume the runtime remains in place. AgentSON asks what happens when Claude disappears, Cursor changes format, or OpenClaw evolves. Can the operational history still exist independently of any particular infrastructure?

2. **Market timing** — The AI agent runtime ecosystem is fragmenting across 30+ tools and frameworks (OpenClaw, Claude Code, Cursor, LangGraph, CrewAI, AutoGen, opencode, etc.). None share a portable representation format. Network effects are unclaimed.

3. **Regulatory tailwind** — GDPR Art. 20 and EU AI Act Art. 52 create legal demand for portable, structured, provenance-tracked agent session data.

4. **Technical defensibility** — Open event schema, provenance model, replay semantics, cross-runtime import/export architecture, and versioned spec with backward compatibility. Adjacent research (narrative reconstruction, browser capture, healthcare) is separated into follow-up papers — the core format is simpler to specify and harder to displace once adopted.

5. **Engineering validation** — An independent lineage of systems-engineering thought (antirez, 2024-2026) confirms the architecture: memory bandwidth is the bottleneck, not compute; small models in self-correcting loops with external verification achieve results far beyond their size.

6. **Existing traction** — 7 working readers across AI coding and healthcare, dogfood artifact validated against spec v1.1, examples from real tool databases, a working CLI, Supabase integration, a GDPR compliance model grounded in formal research.

**Short-term value (developer experience):** Your AI work doesn't die when you switch tools. Every `.AgentSON` file is a searchable, portable, analysable record — your personal engineering journal across every runtime you use.

**Long-term value (institutional knowledge):** As AI agents become long-lived team members (Claude Tag, persistent agents), organisations will need to answer: what did this agent do over the last six months? Why did it make this decision? Can we migrate it to another platform? Can we audit its behaviour? Can we learn from its successful workflows? Memory systems and runtime-internal provenance don't give you portable answers to those questions. AgentSON does.

**The bet:** AI agent tooling will consolidate, but the representation layer should remain open — like TCP/IP survived the protocol wars, like OpenAPI standardised middleware interfaces. AgentSON is the portable execution representation. Every runtime is a producer; AgentSON is what survives when the runtime disappears.

**The architecture:**

```
Communication (MCP)
        │
        ▼
Execution (Agent Runtime — OpenClaw, Claude Code, Cursor, etc.)
        │
        ▼
Representation (AgentSON — portable episodic provenance format)
        │
        ├── Replay
        ├── Evaluation
        ├── Compliance
        ├── Training
        ├── Migration
        └── Archival
```

AgentSON complements MCP, memory systems, and observability — it does not replace any of them. MCP standardizes how agents call tools. AgentSON standardizes what interaction occurred. They stack vertically.

---

# Call to Action

This document is public because AgentSON's moat depends on **adoption**, not secrecy. Giving away the strategy *is* the strategy.

## To developers

- **Export your sessions:** `pip install agentson && agentson export --tool opencode --all`
- **Never lose context again:** Switch runtimes, keep your history. Your `.AgentSON` files are yours — Apache 2.0, no telemetry, no vendor lock-in.
- **Search your entire AI work history:** `agentson search "django migration" --all`

## To tool builders and runtime creators

- **Add `.AgentSON` export to your platform:** One JSON schema. Instantly interoperable with 30+ other tools.
- **Your users' next question will be "can I take my history with me?"** AgentSON is the answer they want to hear.

## To contributors

- **Add a reader for your favourite runtime** — OpenClaw, Cline, Aider, Gemini CLI, Copilot. We have templates and docs.
- **Translate, improve, critique** — open issues, send PRs, join the discussion.

## To researchers

- **Cite AgentSON** in work on agent provenance, reproducibility, evaluation, and compliance.
- **We have a pre-print incoming** (arXiv, August 2026). Formal foundations (AER), empirical validation (HunterAgent), and three-mode reconstruction pipeline.

---

```
Repository:   https://github.com/andiekobbietks/AgentSON
License:      Apache 2.0
Spec:         https://agentson.dev/schema/v1.1.json
PyPI:         pip install agentson
Paper:        arXiv August 2026 — format intrinsics (schema, replay, provenance, import/export)
Sister papers: Browser extension, narrative reconstruction, healthcare (separate)
```

---

*"The operational life of an AI agent, preserved independently of the runtime that hosted it."*
