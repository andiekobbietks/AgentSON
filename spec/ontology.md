# AgentSON Formal Ontology

**Status:** Draft v1.0
**Date:** 06 July 2026

---

## Core Primitives (12 max)

AgentSON defines exactly 12 event types. All agent execution traces normalize to these primitives.

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
| `side-effect` | Persistent state change (file, DB, etc.) | `path`, `agent` |
| `answer` | Final response to user | `text`, `agent` |

### Input Layer (3 primitives)

| Primitive | Purpose | Required Fields |
|-----------|---------|-----------------|
| `user-query` | User input or request | `text`, `agent` |
| `user-feedback` | User correction or clarification | `text`, `agent` |
| `system-event` | External trigger (cron, webhook, etc.) | `text`, `source` |

---

## Normalization Rules

### Rule 1: Every execution event maps to exactly one primitive

```
CDP Runtime.evaluate → action (tool: "browser.evaluate")
MCP tools/call → action (tool: "{server}/{tool}")
browser-use click → action (tool: "browser.click")
Extension message → observation (source: "extension")
```

### Rule 2: Observations always follow actions

```
action (browser.navigate) → observation (page loaded)
action (browser.extract) → observation (content extracted)
action (browser.evaluate) → observation (result)
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
    "source": "cdp|mcp|extension|user|system",
    "timestamp_ms": 1234567890
  }
}
```

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

1. Events are processed in file order (line-by-line JSONL)
2. `handoff` events define control transfer
3. `action` events must complete before next `handoff`
4. `observation` events are causally linked to preceding `action`

### Correlation IDs

Every `action` can include `correlation_id`. The corresponding `observation` MUST reference the same `correlation_id`.

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

1. Every stream MUST start with `stream-meta`
2. Every `handoff` MUST reference valid agent IDs
3. Every `action` SHOULD have a corresponding `observation`
4. No circular handoffs (A→B→A without completion)
5. `user-query` MUST appear before first `handoff` from user

---

## Next Steps

1. [ ] Implement replay engine that executes .agentson streams
2. [ ] Build MCP adapter using this mapping
3. [ ] Build browser-use adapter using this mapping
4. [ ] Add validation CLI tool
5. [ ] Test with captured ChatGPT sessions
