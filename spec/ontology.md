# AgentSON Formal Ontology

**Status:** Draft v1.0
**Date:** 06 July 2026

---

## Core Primitives (12 max)

AgentSON defines exactly 12 event types. All agent execution traces canonicalise to these primitives.

### Coordination Layer (4 primitives)

| Primitive | Purpose | Required Fields |
|-----------|---------|-----------------|
| `stream-meta` | Session header, capabilities, agents | `stream_id`, `agents[]` |
| `handoff` | Transfer control between agents | `from`, `to`, `conch` |
| `presence` | Agent status (online/offline/busy/idle) | `status`, `agent` |
| `capabilities` | Agent self-describes available operations | `agent`, `capabilities` |

### Execution Layer (5 primitives)

| Primitive | Purpose | Required Fields |
|-----------|---------|-----------------|
| `action` | Tool invocation or operation | `tool`, `agent` |
| `observation` | Result from action or external input | `text`, `source` |
| `thought` | Agent reasoning or planning | `text`, `agent` |
| `side-effect` | Persistent state change (file, DB, todo, etc.) | `agent`, plus `path` **or** `action` |
| `answer` | Final response to user | `text`, `agent` |

### Input Layer (3 primitives)

| Primitive | Purpose | Required Fields |
|-----------|---------|-----------------|
| `user-query` | User input or request | `text`, `agent` |
| `user-feedback` | User correction or clarification | `text`, `agent` |
| `system-event` | External trigger (cron, webhook, etc.) | `text`, `source` |

---

## Canonicalisation Rules

### Rule 1: Every execution event maps to exactly one primitive

```
CDP Runtime.evaluate → action (tool: "browser.evaluate")
MCP tools/call → action (tool: "{server}/{tool}")
browser-use click → action (tool: "browser.click")
Extension message → observation (source: "extension")
```

### Rule 2: Record observations when the source provides them

An action may produce an observation, but a result is not guaranteed: the source may omit it, the action may time out, or capture may stop before a result is available. Preserve the action and report the missing/unavailable result; do not manufacture an observation to complete a pair.

When a result is available, represent it as an observation and correlate it with the action where the source provides a correlation identifier.

```text
action (browser.navigate) → observation (page loaded, when returned)
action (browser.extract) → observation (content extracted, when returned)
action (browser.evaluate) → observation (result, when returned)
```

### Rule 3: Handoffs define the execution graph

```
handoff (user → agent-a) → thought → action → observation → handoff (agent-a → agent-b)
```

### Rule 4: Provenance is optional but recommended

Each event can include:
```json
{
  "provenance": {
    "confidence": "confirmed|inferred|estimated|ml_generated|unknown",
    "source": "cdp|mcp|extension|user|system|other|export|reconstructor",
    "timestamp_ms": 1234567890
  }
}
```

The `source` values mean:
- `cdp` — captured from a Chrome DevTools Protocol session
- `mcp` — captured from a Model Context Protocol server
- `extension` — captured from a browser extension
- `user` — supplied by the human directly
- `system` — supplied by the harness or platform
- `other` — a source this version does not name
- `export` — imported from a vendor's own export, not captured live
- `reconstructor` — inferred by the reconstructor rather than observed

**Note:** `provenance.source` is not the same field as the `source` on
`observation` and `system-event`. Those name *what* was observed; this names
*how the entry was obtained*. `observation.source` is
`agent|user|system|tool|sensor|extension|other`, and `system-event.source` is
`cron|webhook|timer|healthcheck|manual|other|reconstructor`. The three enums
overlap only partly, and a value valid in one is not valid in the others.

---

## Adapter Mapping Table

### CDP Adapter

| CDP Method | AgentSON Primitive | Semantic Operation |
|------------|-------------------|-------------------|
| `Page.navigate` | `action` | `browser.navigate` |
| `Runtime.evaluate` | `action` | `browser.evaluate` |
| `Page.captureScreenshot` | `action` | `browser.screenshot` |
| `DOM.getDocument` | `action` | `browser.extract` |
| `Performance.getMetrics` | `action` | `browser.performance` |
| `Target.getTargets` | `action` | `browser.list-tabs` |
| CDP response | `observation` | (result of above) |

### MCP Adapter

| MCP Method | AgentSON Primitive | Semantic Operation |
|------------|-------------------|-------------------|
| `tools/list` | `action` | `mcp.list-tools` |
| `tools/call` | `action` | `mcp.{tool-name}` |
| MCP response | `observation` | (result of call) |
| `resources/read` | `action` | `mcp.read-resource` |
| Resource content | `observation` | (resource data) |

### browser-use Adapter

| browser-use | AgentSON Primitive | Semantic Operation |
|-------------|-------------------|-------------------|
| `navigate(url)` | `action` | `browser.navigate` |
| `click(index)` | `action` | `browser.click` |
| `type(index, text)` | `action` | `browser.type` |
| `state()` | `action` | `browser.snapshot` |
| State response | `observation` | (page state) |

### Extension Adapter

| Extension Event | AgentSON Primitive | Source |
|-----------------|-------------------|--------|
| `chrome.runtime.sendMessage` | `observation` | `extension` |
| `chrome.tabs.executeScript` | `action` | `extension` |
| DOM mutation | `observation` | `extension` |

---

## Replay Semantics

### Deterministic Ordering

1. In the canonical v1.2 archive, events are processed in the order of the `entries` array.
2. In a separately defined line-oriented stream profile, record order follows the stream framing contract; JSONL is not the canonical archive container.
3. `handoff` events define control transfer where collaboration is recorded.
4. An `observation` is causally linked to a preceding `action` when the source establishes that relationship; absence of an observation is not proof of success.

### Correlation IDs

An `action` can include `correlation_id`. If a corresponding `observation` exists and the source provides the correlation identifier, the observation MUST reference the same identifier. An action without a captured observation is valid when the source did not provide a result or capture was incomplete; the adapter must report that limitation rather than inventing a result.

```json
{"type": "action", "correlation_id": "abc-123", "tool": "browser.navigate", ...}
{"type": "observation", "correlation_id": "abc-123", "text": "Page loaded", ...}
```

### Branching (Future)

Streams can branch when agents explore alternatives:
```json
{"type": "handoff", "branch_id": "explore-a", "from": "agent", "to": "chrome"}
{"type": "handoff", "branch_id": "explore-b", "from": "agent", "to": "mcp"}
```

---

## Minimal Event Ontology (12 Primitives)

```
┌─────────────────────────────────────────────────────┐
│                    AgentSON                         │
│              12-Primitive Ontology                  │
├─────────────────────────────────────────────────────┤
│  COORDINATION          │  EXECUTION                 │
│  ────────────          │  ─────────                 │
│  stream-meta           │  action                    │
│  handoff               │  observation               │
│  presence              │  thought                   │
│  capabilities          │  side-effect               │
│                        │  answer                    │
├─────────────────────────────────────────────────────┤
│  INPUT                 │                            │
│  ─────                 │                            │
│  user-query            │                            │
│  user-feedback         │                            │
│  system-event          │                            │
└─────────────────────────────────────────────────────┘
```

---

## Validation Rules

1. The canonical v1.2 archive is validated as a JSON session envelope; its session metadata is carried at the envelope level. A future line-oriented stream profile may require `stream-meta` as its first record, but that is not a v1.2 archive framing rule.
2. Every recorded `handoff` MUST reference valid agent IDs.
3. An `action` SHOULD have a corresponding `observation` when the source provides a result; missing results must remain explicit and must not be fabricated.
4. No circular handoffs (A→B→A without completion) in a stream profile that defines control-transfer semantics.
5. For user-initiated collaboration, a captured `user-query` precedes the corresponding user-to-agent handoff. System-initiated sessions may begin with a `system-event`.

---

## ISO Litmus Test

> "Is this the only format solving this problem at the international level?"

AgentSON is the **only** format doing agent session provenance. No other standard — MCP, A2A, AGNTCY, OpenClaw — records what agents actually did in a portable, vendor-neutral file format.

### Five questions for ISO readiness

| # | Question | AgentSON |
|---|----------|----------|
| 1 | **Does any ISO standard already cover this?** | ❌ No. ISO has SQL, PDF, Unicode. No agent provenance format. |
| 2 | **Does any non-ISO standard cover this?** | ❌ No. MCP/A2A/AGNTCY are execution protocols, not provenance formats. |
| 3 | **Is this royalty-free and open?** | ✅ Apache 2.0. No patents. |
| 4 | **Is this stable enough?** | v1.2 JSON session envelope with 12 event primitives; stream framing remains a separate contract. |
| 5 | **Does this have broad industry potential?** | ✅ Every AI agent produces session traces. Every enterprise needs audit trails. |

### Why AgentSON and not MCP/A2A/AGNTCY

| Layer | What it does | ISO candidate? |
|-------|-------------|----------------|
| **Execution** | How agents talk (MCP, A2A, AGNTCY) | Maybe — but LF handles it |
| **Framework** | How agents run (OpenClaw, NemoClaw) | No — vendor-specific |
| **Provenance** | What agents did (AgentSON) | **Yes — only format in this category** |

MCP, A2A, and AGNTCY are execution protocols. They define how agents communicate. They have the Linux Foundation.

AgentSON is a provenance format. It defines what agents actually did. **No other format does this.** That's not competition — it's a gap in the standardization landscape.

### The PDF analogy

PDF got ISO 32000 because it was the only format canonicalising document layout across vendors. AgentSON canonicalises agent session traces across vendors. Same pattern. Same gap. Same opportunity.

---

## Next Steps

1. [ ] Implement replay engine that executes .agentson streams
2. [ ] Build MCP adapter using this mapping
3. [ ] Build browser-use adapter using this mapping
4. [ ] Add validation CLI tool
5. [ ] Test with captured ChatGPT sessions
