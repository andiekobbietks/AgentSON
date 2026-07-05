# The Trajectory View (AgentSON v1.1)

AgentSON v1.1 promotes the **trajectory view** of an agent session to a first-class concept. A document qualifies as a trajectory when it has the canonical shape:

```
user-query
  ↓
(thought → action → observation → thought → action → observation → ...)*
  ↓
answer
```

This page documents what that means, when it applies, and how downstream consumers should read an AgentSON file.

## New top-level fields

| Field | Type | Required | Description |
|---|---|---|---|
| `task` | string | optional | The user goal that initiated the trajectory. For single-trajectory sessions this is the first `user-query.text`. For multi-trajectory sessions (coming in v1.2), it is the broader goal. |
| `outcome` | enum | optional | `success \| partial \| aborted \| error`. Default: `partial`. What happened from the user's perspective. |

Both fields are **optional** for backward compatibility. Existing v1.0 files validate unchanged. Tools that want to flag "this session is a completed trajectory" can set `outcome`; tools that want to feed agentic models can rely on the trajectory shape without setting anything new.

## New entry type: `observation`

Until v1.1, observations were inlined into `action.output` or `context.details`. In v1.1, `observation` is a **first-class entry type** that can appear anywhere an `action` would, but represents the *result* of an action (or an external signal) rather than the action itself.

```json
{
  "type": "observation",
  "text": "Screenshot shows modal closed, success toast visible",
  "source": "agent",
  "correlation_id": "tc_abc123",
  "attachments": [
    {"kind": "image", "ref": "obs_xyz.png", "note": "post-action screenshot"}
  ],
  "status": "success",
  "timestamp": 1783213351236,
  "duration_ms": 142
}
```

### When to use `observation` vs. `action.output`

| Scenario | Use `action.output` | Use `observation` entry |
|---|---|---|
| Console snippet returns a value | ✓ | |
| Long-running async action (web fetch, compile) | | ✓ |
| Multi-modal result (screenshot, file content, network response) | | ✓ |
| User mid-loop feedback ("actually use the other button") | | ✓ (source: user) |
| Sub-agent reports back to parent | | ✓ (source: agent) |
| External sensor reading (CGM, IoT) | | ✓ (source: sensor) |

Rule of thumb: if the observation is *synchronous and small*, inline it in `action.output`. If it's *async, large, multi-modal, or from a separate source*, emit it as its own entry.

### `correlation_id` + `tool_call_id`

For async or multi-modal observations, set `correlation_id` on the observation to the `tool_call_id` of the action that caused it. This lets consumers pair them without relying on entry order.

```json
{"type": "action", "tool": "browser.fetch", "tool_call_id": "tc_1", "code": "fetch('/api/data')", "timestamp": 1783215002000}
{"type": "observation", "correlation_id": "tc_1", "source": "tool", "text": "200 OK, 4.2 KB", "timestamp": 1783215005500}
```

## The trajectory loop, formally

For a session with `entries = [e₀, e₁, ..., eₙ]`, the trajectory view is:

```
T₀ = first e where e.type == "user-query"   # sets the trajectory
A  = first e after T₀ where e.type == "answer"   # closes the trajectory

between T₀ and A, every maximal run of (thought → action → observation)*
forms one "loop". The answer A is the trajectory's final_answer.
```

A document with **≥1 loop** and **≥1 final_answer** is a complete trajectory. Document-level `outcome` summarises all trajectories.

## Why this matters

Before v1.1, AgentSON could *contain* a trajectory but didn't *name* one. Tool authors had to infer the loop from the entry sequence. With v1.1:

- **Fine-tuning pipelines** for agentic models (Fara-7B, WebVoyager-style) can consume AgentSON directly as trajectory data — no separate "trajectory format" needed.
- **Search and indexing** over trajectories becomes possible (`grep -l "outcome:error" *.AgentSON`).
- **Evaluation tools** can score a trajectory by walking `entries` and checking `outcome` vs. the actual loop completion.
- **Observability stacks** (OpenTelemetry GenAI semantic conventions, LangSmith) can map AgentSON entries onto their span model.

## Migration from v1.0

| v1.0 | v1.1 |
|---|---|
| `outcome` field absent | Add top-level `outcome` (optional, default `partial`) |
| Observations inlined in `action.output` | Optionally extract to dedicated `observation` entries with `correlation_id` |
| No trajectory loop recognised by spec | Spec formally documents the trajectory view |
| `status` only on `action` entries | `status` available on all entry types |

All v1.0 files remain valid v1.1 files. The additions are backward-compatible.

## What's next

- **v1.2 (planned):** Hierarchical trajectories (`trajectories[]`, `parent_trajectory_id`) for sub-agent and multi-task sessions.
- **v2.0 (planned):** RLHF fields (`reward`, `preference`, `human_feedback`), `extensions` namespace for vendor-specific data.

See [`CHANGELOG.md`](../../CHANGELOG.md) for the full version history.