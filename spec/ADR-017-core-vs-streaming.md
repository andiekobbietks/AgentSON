# ADR-017: Core vs Streaming Primitive Separation

**Status:** Accepted
**Date:** 07 July 2026
**Decision Makers:** andiekobbietks

---

## Context

The 12 ontology primitives split naturally into two groups:

### Core Primitives (9) — Always Present
These exist in every .agentson stream, whether single-agent or multi-agent:

| Primitive | Layer | Purpose |
|-----------|-------|---------|
| `action` | Execution | Tool invocation |
| `observation` | Execution | Result from action |
| `thought` | Execution | Agent reasoning |
| `side-effect` | Execution | Persistent state change |
| `answer` | Execution | Final response |
| `user-query` | Input | User request |
| `user-feedback` | Input | User correction |
| `system-event` | Input | External trigger |
| `stream-meta` | Coordination | Session header |

### Streaming Primitives (3) — Multi-Agent Only
These only appear in multi-agent collaboration streams:

| Primitive | Layer | Purpose |
|-----------|-------|---------|
| `handoff` | Coordination | Transfer control |
| `presence` | Coordination | Agent status |
| `capabilities` | Coordination | Agent self-description |

### The Question

Should streaming primitives be **optional** (only in multi-agent streams) or **always required** (even in single-agent streams)?

---

## Decision

**Streaming primitives are OPTIONAL in single-agent streams, REQUIRED in multi-agent streams.**

### Rationale

1. **Single-agent streams don't need handoff.** If there's only one agent, there's nobody to hand off to. Requiring `handoff` entries in a single-agent export would be noise.

2. **Presence is meaningless without multiple agents.** "Agent X is online" is only useful when you need to know which agent is active. In a single-agent stream, the agent is always active.

3. **Capabilities are useful but not required.** A single-agent stream from OpenCode doesn't need to advertise "I can use bash" — the consumer already knows what OpenCode can do.

4. **stream-meta is always required.** Even single-agent streams need a header declaring the tool, agent, and session ID.

### Validation Rules

| Scenario | Required Primitives |
|----------|-------------------|
| Single-agent stream | `stream-meta` + 9 core primitives |
| Multi-agent stream | `stream-meta` + 9 core + 3 streaming |
| Collaboration stream | All 12, with `handoff` chain |

### Detection Rule

A stream is "multi-agent" if `stream-meta.agents` has more than 1 agent (excluding `user`). If `agents.length <= 1`, streaming primitives are optional.

---

## Consequences

### Positive
- (+) Single-agent exports stay simple (no meaningless handoff/presence entries)
- (+) Multi-agent streams get full coordination primitives
- (+) Validation can auto-detect stream type from `stream-meta`
- (+) Backward compatible with existing single-agent exports

### Negative
- (-) Two validation modes (single vs multi-agent) adds complexity
- (-) Consumers must check `stream-meta.agents.length` to know which primitives to expect
- (-) Edge case: stream starts single-agent, becomes multi-agent mid-stream

### Mitigations
- Define a `mode` field in `stream-meta`: `"single" | "multi" | "collab"`
- Validation uses `mode` to determine required primitives
- Edge case handled by: if a `handoff` appears, stream is implicitly multi-agent

---

## Schema Impact

### v1.2 Schema Update

Add `mode` to `stream-meta`:

```json
"streamMeta": {
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["single", "multi", "collab"],
      "description": "Stream mode. Determines which primitives are required."
    }
  },
  "required": ["stream_id", "agents", "mode"]
}
```

### Validation Logic

```python
def validate_stream(stream):
    entries = parse_jsonl(stream)
    meta = entries[0]
    
    if meta["type"] != "stream-meta":
        return Error("Stream must start with stream-meta")
    
    mode = meta.get("mode", "single")
    agent_count = len(meta.get("agents", []))
    
    # Auto-detect mode if not specified
    if mode == "single" and agent_count > 1:
        mode = "multi"
    
    for entry in entries[1:]:
        if mode == "single":
            if entry["type"] in ("handoff", "presence", "capabilities"):
                return Error(f"{entry['type']} not allowed in single-agent stream")
        
        # Validate required fields per primitive
        validate_entry(entry)
```

---

## Litmus Test

> "Does this improve fidelity/portability/replayability/analyzability of a captured episode?"

**Yes.** Separating core from streaming primitives means:
- Higher fidelity (no noise entries in single-agent streams)
- Better analyzability (consumers know what to expect based on mode)
- Same replayability (replay engine handles all 12 types)
- Same portability (JSONL format unchanged)

### ISO Litmus Test

> "Is this the only format solving this problem at the international level?"

**Yes.** No other format distinguishes single-agent vs multi-agent session traces. The `mode` field in `stream-meta` is a unique capability that makes AgentSON adaptable to any agent architecture.

---

## References

- `spec/ontology.md` lines 12-37 — 12 primitives grouped by layer
- `spec/v1.2.json` lines 59-101 — `streamMeta` definition
- `spec/replay-semantics.md` lines 56-70 — Handoff processing rules
