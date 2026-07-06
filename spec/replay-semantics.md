# AgentSON Replay Semantics

**Status:** Draft v1.0
**Date:** 06 July 2026

---

## Overview

Replay is the process of executing an .agentson stream to reproduce agent behavior. This specification defines how to interpret and execute the stream.

---

## Core Principles

### 1. Deterministic Ordering

Events are processed in **file order** (line-by-line JSONL). The stream is append-only and immutable.

```
Line 1: stream-meta
Line 2: user-query
Line 3: handoff (user → agent-a)
Line 4: thought
Line 5: action
Line 6: observation
Line 7: handoff (agent-a → agent-b)
Line 8: answer
```

### 2. Causal Ordering

Events have causal relationships:

```
user-query → handoff → thought → action → observation → handoff → answer
     ↑                                                              ↑
     └──────────────────── causes ──────────────────────────────────┘
```

### 3. Control Transfer

`handoff` events define who acts next:

```json
{"type": "handoff", "from": "user", "to": "agent-a", "conch": "agent-a"}
```

After this handoff, only `agent-a` can emit events until another handoff.

---

## Replay Rules

### Rule 1: Stream Initialization

1. Parse first line as `stream-meta`
2. Load agent capabilities from `stream-meta.agents[]`
3. Initialize agent states (all start as `offline`)

### Rule 2: Handoff Processing

When a `handoff` event is encountered:

1. Verify `from` agent exists
2. Verify `to` agent exists
3. Transfer control token (`conch`) to `to` agent
4. Update agent states:
   - `from` agent → `idle`
   - `to` agent → `busy`

### Rule 3: Action Processing

When an `action` event is encountered:

1. Verify the acting agent holds the `conch`
2. Look up the `tool` in agent capabilities
3. Execute the tool with provided `args`
4. Wait for completion or timeout (default: 30s)
5. Emit corresponding `observation`

### Rule 4: Observation Processing

When an `observation` event is encountered:

1. Verify `source` field exists
2. If `correlation_id` exists, link to preceding action
3. Store observation for downstream consumption

### Rule 5: Thought Processing

When a `thought` event is encountered:

1. Log the thought
2. No execution required (planning only)

### Rule 6: Side-Effect Processing

**⚠️ Security note:** `side-effect` entries can carry arbitrary `path`
and `diff` values. A `.agentson` file may originate from an untrusted
or unverified source (a shared session, a downloaded example, a
compromised export). Applying `path`/`diff` verbatim during replay
means replay becomes an untrusted filesystem-mutation path — a replay
engine that blindly does this on arbitrary input files creates a real
data-loss and security risk, not just a correctness one.

A conformant replay implementation MUST NOT apply `side-effect` diffs
directly to the filesystem unless at least one of the following holds:
- replay is running inside a sandboxed/isolated environment with no
  access to files outside an explicitly scoped working directory, or
- the user has explicitly opted into non-dry-run replay for this
  specific file (not a global "always allow" setting), or
- replay is running in an explicit dry-run/preview mode that reports
  what *would* change without writing anything.

The specific sandboxing/isolation mechanism is implementation-defined
and is not specified further here — this section defines the
requirement, not the mechanism.

When a `side-effect` event is encountered:

1. If `path` exists, verify file exists
2. If `diff` exists, apply diff to file **only under the conditions
   above** — never unconditionally
3. Log the change

### Rule 7: Answer Processing

When an `answer` event is encountered:

1. Output the answer to user
2. Mark session as complete

---

## Correlation IDs

Actions and observations can be linked via `correlation_id`:

```json
{"type": "action", "correlation_id": "abc-123", "tool": "browser.navigate", ...}
{"type": "observation", "correlation_id": "abc-123", "text": "Page loaded", ...}
```

### Correlation Rules

1. Each `action` SHOULD have a unique `correlation_id`
2. The corresponding `observation` MUST reference the same `correlation_id`
3. Multiple `observation` events can reference one `action`
4. Orphaned observations (no matching action) are logged as warnings

---

## Branching (Future)

Streams can branch when agents explore alternatives:

```json
{"type": "handoff", "branch_id": "explore-a", "from": "agent", "to": "chrome"}
{"type": "action", "branch_id": "explore-a", "tool": "browser.navigate", ...}
{"type": "observation", "branch_id": "explore-a", "text": "Page loaded", ...}

{"type": "handoff", "branch_id": "explore-b", "from": "agent", "to": "mcp"}
{"type": "action", "branch_id": "explore-b", "tool": "mcp.tools.call", ...}
{"type": "observation", "branch_id": "explore-b", "text": "Result", ...}
```

### Branch Rules

1. Branches are independent execution paths
2. Each branch has its own `conch` chain
3. Branches can merge at a later handoff
4. Only one branch is "active" at a time

---

## Error Handling

### Action Failures

If an action fails:

```json
{"type": "observation", "text": "Error: timeout", "status": "error", "correlation_id": "abc-123"}
```

The replay engine should:
1. Log the error
2. Continue to next event
3. Allow agent to handle error in next thought/handoff

### Invalid Handoffs

If a handoff references a non-existent agent:
1. Log warning
2. Skip the handoff
3. Continue to next event

### Missing Observations

If an action has no corresponding observation:
1. Log warning
2. Generate synthetic observation: `{text: "No observation recorded", source: "system"}`
3. Continue to next event

---

## Provenance Levels

Each event can include provenance metadata:

```json
{
  "provenance": {
    "confidence": "confirmed|inferred|estimated|ml_generated|unknown",
    "source": "cdp|mcp|extension|user|system",
    "timestamp_ms": 1234567890
  }
}
```

### Confidence Levels

| Level | Meaning | Use Case |
|-------|---------|----------|
| `confirmed` | Directly observed from execution | CDP responses, user input |
| `inferred` | Derived from confirmed events | Derived state changes |
| `estimated` | Approximate or calculated | Performance metrics |
| `ml_generated` | Generated by ML model | AI-generated text |
| `unknown` | Source unclear | Fallback |

---

## Replay Engine Interface

```javascript
class ReplayEngine {
  // Load an .agentson stream
  load(streamPath: string): void;
  
  // Execute the stream
  execute(): Promise<ReplayResult>;
  
  // Execute up to a specific line
  executeUntil(lineNumber: number): Promise<ReplayResult>;
  
  // Get execution state
  getState(): {
    currentAgent: string;
    completedActions: number;
    observations: Observation[];
    errors: Error[];
  };
}

interface ReplayResult {
  success: boolean;
  duration_ms: number;
  actionsExecuted: number;
  observationsCollected: number;
  errors: Error[];
  output: string;
}
```

---

## Validation Rules

Before replay, validate:

1. Stream starts with `stream-meta`
2. All referenced agents exist in `stream-meta.agents[]`
3. No circular handoffs without completion
4. Every `action` has a valid `tool` in agent capabilities
5. `user-query` appears before first `handoff` from user

---

## Example Replay

Input stream:
```
{"type": "stream-meta", "stream_id": "demo", "agents": [{"id": "user"}, {"id": "chrome"}]}
{"type": "user-query", "agent": "user", "text": "Navigate to example.com"}
{"type": "handoff", "from": "user", "to": "chrome", "conch": "chrome"}
{"type": "thought", "agent": "chrome", "text": "Will navigate to URL"}
{"type": "action", "agent": "chrome", "tool": "browser.navigate", "args": {"url": "https://example.com"}}
{"type": "observation", "agent": "chrome", "source": "tool", "text": "Page loaded: Example Domain"}
{"type": "handoff", "from": "chrome", "to": "user", "conch": "user"}
{"type": "answer", "agent": "chrome", "text": "Navigated to example.com"}
```

Replay execution:
1. Load stream-meta, initialize agents
2. Process user-query
3. Handoff to chrome (chrome → busy)
4. Thought logged
5. Execute `browser.navigate` → wait for CDP response
6. Observation recorded
7. Handoff to user (chrome → idle, user → busy)
8. Answer output

---

## Implementation Checklist

- [ ] Replay engine class
- [ ] Stream parser (JSONL)
- [ ] Action executor (tool dispatch)
- [ ] Correlation tracker
- [ ] Error handler
- [ ] Branch manager (future)
- [ ] Provenance validator
