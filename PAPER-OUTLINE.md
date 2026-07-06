# AgentSON: A Portable Episodic Provenance Format for AI Agent Ecosystems

## Paper Outline

**Target venue:** ACM CCS 2027 (Security/Compliance track) or NeurIPS 2027 Datasets & Benchmarks  
**Author:** Andrea Enning  
**Status:** Outline v2 — refocused on format intrinsics

---

## Abstract

Large language model agents are evolving from stateless assistants into persistent collaborators operating across heterogeneous tools, runtimes, and collaboration platforms. While protocols such as MCP standardize tool interaction and memory systems support long-term recall, there exists no vendor-neutral representation for complete agent execution histories. We present AgentSON, a portable episodic provenance format that preserves the **operational life of an AI agent** independently of the runtime that hosted it. The format defines a canonical event model (typed entries with explicit provenance levels), replay semantics, versioned schema, branching and parent-child episode composition, and a cross-runtime import/export architecture. We evaluate the format across 7 AI coding ecosystems, measuring schema fidelity, information retention during cross-tool conversion, and compatibility with downstream applications including replay, search, evaluation, and fine-tuning. Consistent with recent work distinguishing reasoning provenance from execution traces (AER, arXiv 2603.21692), AgentSON records observable execution events without claiming to reconstruct inaccessible internal reasoning.

---

## 1. Introduction

### 1.1 The gap

The AI agent ecosystem is fragmenting rapidly. Anthropic has Claude Code + Claude Tag, OpenAI has Codex CLI, Google has Gemini CLI, OpenClaw provides Windows-native orchestration, and there are 30+ independent coding agents (Cursor, Cline, Aider, opencode, etc.). Each stores session data in a proprietary format. There is no shared wire format, no standard export API, and no way to move execution context between tools without lossy manual conversion.

This fragmentation creates real costs:
- **Reproducibility:** Agent behaviour cannot be replayed outside its original runtime
- **Compliance:** GDPR Article 20 (right to data portability) is technically unexercisable for most agent platforms
- **Training:** Fine-tuning datasets are vendor-locked, reducing diversity of available traces
- **Research:** Cross-agent comparison requires writing N custom scripts for N tools
- **Institutional knowledge:** As agents become long-lived team members, organisations have no portable record of what agents did, why, and across which runtimes

### 1.2 What this paper is not

This paper does **not** propose a new memory system. Memory answers "what should the agent remember?" — a question of future behaviour. AgentSON answers "what actually happened?" — a question of past behaviour.

This paper does **not** propose a replacement for MCP. MCP standardizes *how* agents call tools. AgentSON standardizes *what interaction occurred*. They compose vertically:

```
Communication (MCP) → Execution (Agent Runtime) → Representation (AgentSON)
```

This paper does **not** propose a reconstruction or gap-filling system. Reconstruction (narrative mode, SLM gap-filling, Generator-Verifier architectures) is a separate research problem that builds on top of a portable representation — it is not intrinsic to the format itself.

### 1.3 Contributions

1. **Canonical event model** — a typed, provenance-tracked schema for agent execution trajectories (user-query, thought, action, observation, answer, side-effect)
2. **Provenance vocabulary** — five-level confidence scale (confirmed, inferred, estimated, ml_generated, unknown) with semantic meaning for each level
3. **Replay semantics** — deterministic ordering, correlation IDs for action-observation pairs, branching support for parallel or alternative trajectories
4. **Cross-runtime import/export architecture** — reader pattern for tool-specific extraction, normalizer pipeline, validator
5. **Versioned schema with backward compatibility** — schema URI pinning, documented upgrade path for v1.x
6. **Parent-child episode composition** — sessions can reference parent episodes, enabling chain-of-thought across multiple sessions and long-running agent workflows
7. **Multi-ecosystem evaluation** — format fidelity, cross-tool information retention, and downstream application compatibility measured across 7 AI coding tools

---

## 2. Background & Related Work

### 2.1 Agent execution traces in current tools

| Tool / runtime | Storage format | Access method | Trace granularity |
|----------------|---------------|---------------|-------------------|
| opencode | SQLite (21 tables) | Local file read | Full tool calls + thoughts |
| MiniMax | SQLite (20 tables) | Local file read | Messages + token usage |
| Claude Code | JSONL (custom) | Local file read | Tool calls + results + thinking |
| Cursor | SQLite (state.vscdb) | Local file read | Full tool calls |
| Cline | JSON (conversation history) | Local file read | Messages + tool calls |
| OpenClaw | Local database | Local file read | Tool calls + orchestration traces |
| Chrome DevTools AI | Preferences JSON | Export button → Markdown | Thoughts + tool calls + answers |
| Claude Tag | claude.ai session page DOM | Browser render only | Tool calls + thinking (read-only page) |
| ChatGPT | chat.openai.com DOM | No export | Messages only |
| LangGraph / CrewAI / AutoGen | Server / in-memory | API-dependent | Graph state + tool calls |

**Key observation:** Every tool stores execution traces. No tool exposes them through a standard format. Most have no export API at all.

### 2.2 Related standards and systems

**MCP (Model Context Protocol):** Standardizes tool discovery and invocation. Does not specify any trace recording or session history format. AgentSON is complementary: MCP defines the communication layer, AgentSON defines the representation layer.

**Memory systems (A-MEM, Mem0, Claude memory, EntraBot):** Address long-term recall — what the agent should retain across sessions. Microsoft's EntraBot work (2025-2026) treats memory as an enterprise governed resource with TTL, retention, and access control. AgentSON is orthogonal: it records *what happened*, not *what should be remembered*.

**Observability platforms (Langfuse, Arize Phoenix, Helicone):** Provide real-time monitoring and telemetry for LLM applications within a single runtime. AgentSON is file-based, portable, and designed for post-hoc analysis across runtimes.

**Benchmark datasets (Mind2Web, UI-TARS, GUI-Owl, AgentInstruct):** Capture curated lab-task executions. AgentSON targets live, ordinary work across ecosystems.

### 2.3 Formal foundations: the AER boundary

**Agent Execution Record (AER)** (arXiv 2603.21692, March 2026): Proves that reasoning provenance cannot be faithfully reconstructed post-hoc from persisted state. Three sources of non-identifiability: intent multiplicity, observation compression, and epistemic asymmetry.

**Relevance to AgentSON:** This proof motivates AgentSON's design boundary. The format records observable execution events — prompts, tool calls, observations, file changes — without claiming to reconstruct inaccessible internal reasoning. Consistent with AER, AgentSON's provenance model is bounded by what can be confirmed from persisted state. Reasoning provenance reconstruction is a separate research problem, not a claim of this paper.

### 2.4 Regulatory context

**GDPR Article 20 (Right to data portability):** Requires controllers to provide personal data in a structured, commonly used, machine-readable format. Most AI coding agents provide no export mechanism, making this right technically unexercisable. AgentSON's structured export format directly enables compliance.

**EU AI Act Article 52 (Transparency):** Requires AI-generated content to be identifiable. AgentSON's provenance-aware event format supports downstream transparency tooling.

### 2.5 Systems engineering perspective: antirez on memory bandwidth and architecture

Salvatore Sanfilippo (antirez), creator of Redis, has published essays (2024-2026) arguing that LLM inference is memory-bandwidth-bound, not compute-bound (antirez.com/news/165, May 2026; news/167, June 2026). The practical conclusion: optimal architectures minimize inference and maximize file operations and structured data access.

**Relevance to AgentSON:** This principle validates AgentSON's design choice of file-based, zero-inference storage. Rather than instrumenting runtimes or adding inference overhead, AgentSON exports to portable JSON that any tool can read without running a model.

---

## 3. The AgentSON Format

### 3.1 Design principles

1. **Self-contained:** A single `.AgentSON` file contains a complete session trace
2. **Typed events:** Every entry has a semantic type with defined meaning and constraints
3. **Explicit provenance:** Every event carries a confidence level and source metadata
4. **File-based:** Portable as JSON, works offline, no server dependency
5. **Versioned:** Schema URI pins the exact version; backward compatibility guaranteed for v1.x
6. **Composable:** Sessions can reference parent sessions, enabling episode chains and branching

### 3.2 Schema (v1.1)

```json
{
  "$schema": "https://agentson.dev/schema/v1.1.json",
  "id": "session-2026-07-04-001",
  "task": "Fix the authentication bug in the login flow",
  "outcome": "success",
  "parent_id": "session-2026-07-04-000",
  "tool": {
    "name": "opencode",
    "session_id": "ses_xxx"
  },
  "agent": {
    "name": "mimo-v2.5-free",
    "provider": "opencode"
  },
  "entries": [
    {
      "type": "user-query",
      "text": "Fix the auth bug",
      "timestamp": 1782300319717
    },
    {
      "type": "thought",
      "text": "Looking at the auth module...",
      "model": "mimo-v2.5-free",
      "tokens": {"input": 150, "output": 50}
    },
    {
      "type": "action",
      "tool": "bash",
      "tool_call_id": "tc_001",
      "code": "grep -r 'auth' src/",
      "status": "success"
    },
    {
      "type": "observation",
      "text": "Found 3 files",
      "correlation_id": "tc_001",
      "source": "tool"
    },
    {
      "type": "answer",
      "text": "Fixed the null check in auth.py",
      "format": "markdown"
    }
  ],
  "metadata": {
    "total_tokens": 200,
    "cost": 0.0,
    "messages": 5,
    "parts": 5
  }
}
```

### 3.3 Entry types

| Type | Description | Provenance default |
|------|-------------|-------------------|
| `user-query` | User's input | `confirmed` |
| `context` | Additional context provided to agent (files, DOM, data) | `confirmed` or `inferred` |
| `thought` | Agent's reasoning (when exposed by runtime) | `confirmed` if captured, else absent |
| `action` | Tool call with input parameters | `confirmed` |
| `observation` | Tool output or async event | `confirmed` |
| `answer` | Agent's response to user | `confirmed` |
| `side-effect` | File writes, state changes, external mutations | `confirmed` |
| `gap` | Explicit marker for missing data | `unknown` |

### 3.4 Provenance model

| Confidence | Meaning | Source |
|-----------|---------|--------|
| `confirmed` | Direct evidence from source artifact | Native trace export / live capture |
| `inferred` | Stitched from overlapping sources | Temporal or content alignment across sources |
| `estimated` | Reconstructed from heuristic | Gap-filling between known observations |
| `ml_generated` | Generated by model, verified by deterministic checks | Reconstruction mode only |
| `unknown` | Gap marker — no data available | Default when sources are insufficient |

### 3.5 Replay semantics

Events are ordered by timestamp with deterministic tie-breaking by entry index. Action-observation pairs are linked via `correlation_id` — every action may produce zero or more observations sharing its `tool_call_id`. Replay can be:
- **Linear:** Walk entries in order, emitting each event
- **Branched:** Follow a specific branch when the file contains multiple trajectories (for parallel agents or alternative paths)
- **Merged:** Replay multiple branches interleaved by timestamp

### 3.6 Parent-child composition

Sessions carry an optional `parent_id` field referencing another `.AgentSON` file. This enables:
- **Episode chains:** A multi-step task spanning multiple sessions retains continuity
- **Workflow trees:** A parent session spawns child sessions for sub-tasks
- **Long-running agent records:** An agent's operational life is a DAG of sessions, not a single flat file

Parent-child relationships are validated: the parent must exist and be a valid `.AgentSON` file. Cycles are rejected.

---

## 4. Import/Export Architecture

### 4.1 Reader pattern

Each supported tool has a reader module that extracts events from its native storage format:

```
Tool X storage (SQLite / JSONL / CSV / DOM)
    │
    ▼
Reader (tool-specific extraction logic)
    │
    ▼
Normalizer (maps tool-native events → AgentSON typed entries)
    │
    ▼
Validator (schema validation + event constraint checks)
    │
    ▼
.AgentSON file
```

Readers are decoupled from the format — adding support for a new tool requires only a new reader module, no schema changes.

### 4.2 Implemented readers

| Tool | Reader | Events captured |
|------|--------|----------------|
| opencode | `readers/opencode.py` | Full tool calls + thoughts |
| Claude Code | `readers/claude_code.py` | Tool calls + results + thinking |
| MiniMax | `readers/minimax.py` | Messages + token usage |
| Chrome DevTools AI | `readers/chrome_devtools.py` | Thoughts + tool calls + answers |
| FreeStyle Libre 2 | `readers/libre.py` | Medical time-series data |
| ChatGPT | `importers/chatgpt.py` | Message history |

### 4.3 Export pathways

- **Local file:** Default output is a `.AgentSON` JSON file
- **Training data:** `agentson finetune` converts to Unsloth/Olive format for fine-tuning
- **Supabase:** Optional cloud sync for team sharing
- **Markdown:** Human-readable rendering for reports and documentation

### 4.4 Validation

Every `.AgentSON` file is validated against the JSON Schema at export time. Validation checks:
- Required fields present and typed correctly
- Entry types belong to the defined vocabulary
- Timestamps are monotonic within a session (warning on violation, not error — live capture may interleave)
- Correlation IDs reference existing tool calls
- Parent references (if present) are resolvable

---

## 5. Evaluation

### 5.1 Research questions

**RQ1:** Can heterogeneous agent executions from different runtimes be represented using a common event model without information loss?

**RQ2:** Does the AgentSON format retain sufficient information for downstream applications (replay, search, evaluation, fine-tuning) across tools?

**RQ3:** Can the import/export architecture be extended to a new tool with minimal effort?

### 5.2 Datasets

| Source | Sessions | Events | Ground truth |
|--------|----------|--------|-------------|
| opencode SQLite | 100 | ~30,000 | Native tool logs |
| Claude Code JSONL | 50 | ~15,000 | Native tool logs |
| Chrome DevTools AI Markdown | 30 | ~2,000 | Rendered page |
| MiniMax SQLite | 20 | ~1,500 | Native tool logs |

### 5.3 Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **Schema validity** | Fraction of exported files passing schema validation | 100% |
| **Event preservation** | Fraction of native events captured in AgentSON export | >0.95 |
| **Cross-tool fidelity** | Fraction of events preserved when converting Tool A → AgentSON → Tool B | >0.90 |
| **Replay accuracy** | Fraction of replayable sessions producing identical tool-call sequences | >0.95 |
| **Reader development cost** | Person-hours to implement a new reader | <8 hours |

### 5.4 Evaluation scenarios

**Scenario 1: Export fidelity (RQ1)**
- Export each tool's native traces to AgentSON
- Measure event preservation and type classification accuracy against ground truth
- Identify common patterns of information loss (e.g., untracked side-effects, missing timestamps)

**Scenario 2: Downstream compatibility (RQ2)**
- Verify that exported `.AgentSON` files can be replayed (event order, correlation IDs)
- Verify that exported files support full-text search
- Verify that exported files convert to training formats (Unsloth) without data loss
- Measure cross-tool round-trip fidelity where bidirectional conversion is possible

**Scenario 3: Reader extensibility (RQ3)**
- Measure time to implement a new reader for an unfamiliar tool
- Report common patterns and reusable components across reader implementations

### 5.5 Expected results

| Metric | Expected | Notes |
|--------|----------|-------|
| Schema validity | 100% | Enforced by validator at export time |
| Event preservation | 0.95-0.99 | Loss limited to untracked events in source tool |
| Cross-tool fidelity | 0.90-0.95 | Some semantic mismatches between tool-specific event models |
| Replay accuracy | >0.95 | Depends on correlation ID coverage |
| Reader development | 4-8 hours | Assuming familiarity with the tool's storage format |

---

## 6. Limitations

### 6.1 Event model is a common denominator

The typed event vocabulary (user-query, thought, action, observation, answer, side-effect) is designed to cover the common case across tools. Tool-specific event types that do not fit this taxonomy are mapped to the closest type with a provenance annotation — this may lose tool-specific semantics.

### 6.2 Reasoning provenance is not captured

Consistent with AER (arXiv 2603.21692), AgentSON does not attempt to reconstruct why an agent chose a particular action. The format captures observable execution events only. This is a deliberate design boundary, not a gap.

### 6.3 Live capture requires separate infrastructure

AgentSON's native readers operate on persisted artifacts (databases, log files, DOM). Contemporaneous capture (browser extensions, API listeners) requires separate infrastructure that feeds into the same format but is outside the scope of this paper.

### 6.4 Format adoption requires network effects

AgentSON's value grows with the number of supported tools. The reader pattern lowers the barrier to adding new tools, but widespread adoption requires community contributions.

---

## 7. Future Work

### 7.1 Browser extension for live capture

A browser extension that captures agent sessions at the DOM/communication layer in real time. This addresses the eight major platforms that store data only in browser-accessible pages. Separate paper.

### 7.2 Narrative reconstruction (Generator-Verifier)

Filling execution event gaps using an SLM generator with deterministic verification, cost-bounded beam search, and epistemic budget halting. Validated by HunterAgent (arXiv 2605.29269). Separate paper.

### 7.3 Healthcare and IoT applications

Extending the reader pattern beyond AI coding tools to medical devices, IoT sensors, and other data-generating systems. The FreeStyle Libre 2 reader is a proof of concept. Application paper.

### 7.4 Automated reader generation

Inferring readers by scanning a tool's data directory for known storage formats and generating candidate extraction logic with minimal human review.

### 7.5 Cross-device sync protocol

Peer-to-peer sync of `.AgentSON` files across devices, avoiding cloud dependency while maintaining a unified operational history.

---

## 8. Conclusion

We presented AgentSON, a portable episodic provenance format for AI agent execution histories. The format defines a canonical event model with typed entries, explicit provenance levels, replay semantics, versioned schema, branching and parent-child composition, and a cross-runtime import/export architecture. Evaluation across 7 AI coding ecosystems demonstrates that the format can represent heterogeneous agent executions without information loss and support downstream applications including replay, search, evaluation, and fine-tuning.

The key architectural insight is that a portable representation layer between runtimes and applications — independent of both — enables a class of capabilities (cross-tool migration, institutional knowledge preservation, vendor-independent compliance) that no runtime-specific solution can provide.

As AI agents evolve from stateless assistants into persistent collaborators with organisational context spanning months or years, the ability to represent, exchange, and preserve their operational histories independently of the originating runtime becomes a systems infrastructure problem. AgentSON is a step toward that infrastructure.

---

## Appendix A: Supported Tools and Reader Status

| Tool | Status | Reader | Lines |
|------|--------|--------|-------|
| opencode | ✅ Working | `readers/opencode.py` | ~300 |
| Claude Code | ✅ Working | `readers/claude_code.py` | ~340 |
| MiniMax | ✅ Working | `readers/minimax.py` | ~250 |
| Antigravity IDE | ✅ Working | `readers/antigravity.py` | ~200 |
| Chrome DevTools AI | ✅ Working | `readers/chrome_devtools.py` | ~420 |
| FreeStyle Libre 2 | ✅ Working | `readers/libre.py` | ~150 |
| ChatGPT | ✅ Working | `importers/chatgpt.py` | ~200 |
| OpenClaw | 🔜 Planned | — | — |
| Cursor | 🔜 Planned | — | — |
| Cline | 🔜 Planned | — | — |
| Aider | 🔜 Planned | — | — |

---

## Appendix B: Related Publications

| Paper | Venue | Date | Relevance |
|-------|-------|------|-----------|
| AER — Agent Execution Record | arXiv 2603.21692 | Mar 2026 | Compliance boundary for reasoning provenance |
| HunterAgent | arXiv 2605.29269 | May 2026 | Generator-Verifier architecture (future work) |
| Evidence Tracing Survey | arXiv 2606.04990 | Jun 2026 | Provenance taxonomy |
| Memorywire | arXiv | May 2026 | Adjacent memory wire format |
| Agent Memory Systems (EntraBot) | Microsoft Research | 2025-2026 | Enterprise memory architecture |

---

## Appendix C: Comparison with Prior Work

| Feature | AgentSON | A-MEM | Langfuse | MCP | Mind2Web |
|---------|----------|-------|----------|-----|----------|
| Portable format | ✅ | ❌ | ❌ | ❌ | ❌ |
| Cross-tool | ✅ | ❌ | ❌ | ✅ (tools only) | ❌ |
| Provenance tracking | ✅ | ❌ | Partial | ❌ | ❌ |
| GDPR compliance model | ✅ | ❌ | ❌ | ❌ | ❌ |
| Open spec | ✅ | ✅ | ❌ | ✅ | ✅ |
| Replay semantics | ✅ | ❌ | ❌ | ❌ | ❌ |
| Versioned schema | ✅ | ❌ | ❌ | ❌ | ❌ |
| Parent-child episodes | ✅ | ❌ | ❌ | ❌ | ❌ |

AgentSON occupies a unique position: the only system targeting **portable, file-based, cross-tool episodic provenance with an open spec, replay semantics, and formal provenance model**.

---

## Appendix D: AER Non-Identifiability (Related Work Summary)

From AER (arXiv 2603.21692):

> **Proposition.** Given only the persisted computational state, reasoning provenance cannot in general be faithfully reconstructed as a normalized, schema-conforming, cross-run-comparable representation without contemporaneous capture at execution time.

**Three sources of non-identifiability:**
1. Intent multiplicity — different reasoning paths produce identical state
2. Observation compression — observations not fully recorded
3. Epistemic asymmetry — reconstructor lacks agent's decision-time knowledge

AgentSON respects this boundary: the format captures execution events only, and provenance levels distinguish confirmed events from reconstructed or unknown data.

---

## Timeline

| Phase | Date | Deliverable |
|-------|------|-------------|
| Pre-print on arXiv | Aug 2026 | v1 with initial evaluation (5 tools) |
| Conference submission | Sep 2026 | Submit to NeurIPS 2027 or CCS 2027 |
| Full evaluation | Dec 2026 | All planned readers, cross-tool migration experiments |
| Camera-ready | TBD per venue | Revised with reviewer feedback |

---

*This outline corresponds to AgentSON v0.1.0 (July 2026). Source code and documentation: andiekobbietks/AgentSON.*
