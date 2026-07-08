# Normalization: Why 12 Primitives?

*How and why AgentSON normalizes provenance from six agent protocols into a single 12-primitive format.*

## The Problem

Every agent framework and protocol records provenance differently:

- **MCP** has resources, tools, prompts, and sampling — but no concept of "thought" or "handoff"
- **A2A** has tasks, artifacts, and messages — but conflates user input with system events
- **AGNTCY** has action traces and knowledge artifacts — but lacks structured user feedback
- **capi** has performance tokens and capability manifests — but no session-level coordination
- **TOAST** has hierarchical test oracles and assertions — but prioritizes pass/fail over process
- **T3 Code** has code execution traces — but no awareness of side-effects outside the sandbox

Without normalization, provenance is locked into each protocol's ontology. Cross-protocol analysis, composability, and auditing require a **universal intermediate format** — AgentSON.

## The 12-Primitive Ontology

AgentSON defines exactly 12 primitive types, organized into three categories:

### Coordination (4)

These primitives handle how agents interact, coordinate, and share presence:

| Primitive | Description | Source Protocols |
|-----------|-------------|------------------|
| `stream-meta` | Metadata about a streaming connection (model, provider, status) | MCP, A2A |
| `handoff` | Transfer of control between agents or tools | A2A, AGNTCY |
| `presence` | Agent availability, capability announcement, heartbeat | capi, MCP |
| `capabilities` | Declared capabilities, tools, or resources an agent exposes | MCP, capi, T3 Code |

### Execution (5)

These primitives capture what happened during a session:

| Primitive | Description | Source Protocols |
|-----------|-------------|------------------|
| `action` | An agent took an action (called a tool, executed code, made an API call) | MCP, A2A, AGNTCY, T3 Code |
| `observation` | The result or output of an action | AGNTCY, MCP, T3 Code |
| `thought` | Internal reasoning, planning, or chain-of-thought | A2A, AGNTCY |
| `side-effect` | An external impact that wasn't directly requested (state change, notification, resource creation) | capi, TOAST |
| `answer` | A final response delivered to the user | A2A, MCP |

### Input (3)

These primitives capture the human-in-the-loop signals:

| Primitive | Description | Source Protocols |
|-----------|-------------|------------------|
| `user-query` | An initial or follow-up question from the user | MCP, A2A, ChatGPT |
| `user-feedback` | Explicit feedback (thumbs up/down, rating, correction) | ChatGPT, A2A |
| `system-event` | A system-generated event (timeout, error, config change, interruption) | MCP, A2A, AGNTCY |

## Why Not Use Protocol-Specific Schemas Directly?

Because each protocol was designed for a different use case:

- **MCP** is focused on tool execution and resource access — provenance is a side effect, not a goal
- **A2A** is about agent-to-agent task delegation — it assumes bilateral trust and doesn't record system-level events
- **AGNTCY** captures agent execution traces for debugging — but doesn't handle user intent or feedback
- **capi** is a capability advertising protocol — it has no session model at all
- **TOAST** is about verifiable assertions — it treats everything as a test case
- **T3 Code** is about code execution isolation — it has no concept of agent coordination

Using any single protocol's ontology would lose information from the other five protocols. AgentSON's 12 primitives are the **intersection of all six, with explicit loss recording**.

## What About Other Formats?

| Format | Why Not |
|--------|---------|
| OpenTelemetry | Good for observability but lacks user intent, handoff, and capabilities concepts |
| W3C Provenance (PROV-O) | Too abstract — no primitives for agent thought, side-effect, or feedback |
| JSON-LD / ActivityPub | Activity Streams are pub-sub, not provenance — no execution model |
| TensorBoard / MLflow | Designed for model training metrics, not interactive agent sessions |
| (your protocol here) | AgentSON's adapter pattern makes it trivial to add — see ADR-016 |

## Loss Recording

No adapter is lossless. Every adapter records what it couldn't map in a `_loss` array on each entry:

```json
{
  "type": "action",
  "from": "mcp",
  "_loss": [
    {
      "field": "sampling.temperature",
      "reason": "No AgentSON primitive for sampling parameters",
      "original": { "temperature": 0.7 }
    }
  ]
}
```

This ensures **no silent data loss**. Any information that doesn't fit the 12 primitives is preserved in `_loss` and can be recovered by downstream processes.

## Session-to-Session Normalization

AgentSON normalizes across sessions — not just within a session. The `session` block tracks:

- `id` — globally unique session identifier
- `parentId` — for branching/forking sessions
- `model` — the model/provider used
- `startedAt` / `endedAt` — temporal bounds
- `metadata` — arbitrary key-value context

This enables:
- **Session trees** — one user query can spawn multiple agent sub-sessions
- **Cross-session aggregation** — collect all sessions that used a specific tool
- **Auditability** — replay any session from its normalized trace

## ADR References

- **ADR-012**: Initial 12-primitive ontology definition and the decision to use three categories (Coordination, Execution, Input)
- **ADR-013**: Session tree model — parent/child session relationships for branching
- **ADR-014**: Loss recording mechanism — why `_loss` arrays and what they preserve
- **ADR-015**: Selection of format primitives — why 12 and how they map to MCP, A2A, AGNTCY
- **ADR-016**: Adapter architecture — each protocol gets its own adapter, importers and exporters are symmetric
- **ADR-017**: Design token and design system standardization — shared CSS across all viewers

For full ADR content, see `docs/adr/`.
