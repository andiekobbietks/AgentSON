# ADR-022: Reconciling the Readers with the Ontology

**Status:** Accepted
**Date:** 20 October 2026
**Decision Makers:** andiekobbietks

---

## Context

A conformance suite run against the committed examples found that **17 of 68
of them do not validate against the format's own schema**. That is a
failure of the *examples*, not of the schema: every one of the 68 was
committed as a demonstration of a working reader, and 17 of them describe
something the schema does not allow.

The causes are three, and each is a question the code and the schema answer
differently. This ADR decides all three.

| # | The disagreement | Where the code is right | Where the schema is right |
|---|---|---|---|
| 1 | `side-effect` requires `path`; readers emit `action`/`text`/`status` | ✅ | |
| 2 | `stream-meta.mode` is `"jsonl"`; the enum is `single\|multi\|collab` | | ✅ |
| 3 | One example carries a `context` entry; ADR-016 demoted `context` to metadata | | ✅ |
| 4 | `timestamp: null` on 53 entries; the schema says integer | | ✅ (omit, don't null) |
| 5 | `action.status` is `"running"`; not in the enum | | ✅ (it is a real state) |

---

## Decision 1 — `side-effect` gains `action`, and `path` becomes optional

**The schema changes.** `side-effect` becomes:

```json
{
  "type": "side-effect",
  "agent": "a1",
  "action": "todo_update",
  "text": "Check system temperature",
  "status": "pending",
  "path": "/repo/file.txt",
  "diff": "+1 -0"
}
```

with `required: []` at the primitive level, plus:

```json
"anyOf": [{ "required": ["path"] }, { "required": ["action"] }]
```

### Why the schema is wrong here, not the readers

**The ontology's own wording admits the case.** `side-effect` is defined as
"Persistent state change (file, DB, etc.)" — the "(file, DB, etc.)" is not
decoration. A todo list is a persistent state change. A database row is a
persistent state change. Neither has a filesystem path.

**A `path` is a locator, and a locator is not always available.** The
readers that emit `action`/`text` are not making a mistake — they are
reporting a state change to something that has no path:

- `readers/opencode.py` emits a `todo_update` side-effect for every todo
  the agent touched. **A todo item has no path.** It has a content string
  and a status.
- `readers/claude_code.py` emits a `todo_update` for the same reason.

Requiring `path` on those forces the reader to invent one — and inventing
a path is *worse* than omitting it, because a fabricated locator is a false
statement in a provenance record. **A format whose required field forces a
fabrication is a format that will be fabricated.**

**`action` is the missing discriminator, and it is already in the data.**
`side-effect` was the only primitive with no way to say *what* changed. It
has `path` (where) and `diff` (how), but not *what*. The readers were
already writing `action` because there was nowhere else to put it. The
schema was missing a field its own data needed.

**`text` and `status` are not redundant with other primitives.**
`observation` means "result from action or external input" — something came
back. `side-effect` means the world changed. A todo going from `pending` to
`completed` is the second, not the first.

### The rule this establishes

> A primitive's required fields are the minimum for it to be *that*
> primitive, and a required field that a real occurrence cannot supply is a
> field that will be fabricated.

`action` requires `tool`. `observation` requires `text` and `source`.
`handoff` requires `from`, `to`, `conch`. All of those are always
available. `side-effect` was the outlier.

**Note on `agent`.** `agent` is a `baseEntry` field and is *optional*
there — an entry does not always name the agent that produced it. It was
NOT made required for `side-effect`, even though the ontology's table
lists it, because the readers do not always know it: `readers/opencode.py`
emits a todo side-effect with `timestamp: None` and no agent, because the
todo list is a property of the session rather than of a particular agent.
**Making it required would have been a second fabrication** — this time of
an agent identity.

### Consequence

`side-effect` with no `path` and no `action` is not a valid side-effect.
The schema does not require a field it cannot guarantee, but it does
require **one** of the two that identify the change. The validator
enforces: `anyOf: [{required: ["path"]}, {required: ["action"]}]`.

---

## Decision 2 — the schema is right; `mode` is a *stream* mode, not a *file* format

**The code changes.** `stream/lib/mcp_adapter.py` writes
`"mode": "jsonl"`. That is a bug, and a naming one.

`mode` was introduced by ADR-017 to answer a specific question: **"is this
stream single-agent or multi-agent?"** The enum is `single | multi |
collab` and it determines which primitives are required:

| Scenario | Required primitives |
|---|---|
| Single-agent stream | `stream-meta` + 9 core primitives |
| Multi-agent stream | `stream-meta` + 9 core + 3 streaming |
| Collaboration stream | All 12, with `handoff` chain |

`"jsonl"` answers none of that. It is the name of the *file format* — and
the file format is not a choice, because ADR-015 made JSONL the only
format. **Every stream in this format is JSONL.** So `mode: "jsonl"` is a
constant that carries no information.

**Why it matters beyond this one field.** ADR-017's detection rule is
"a stream is multi-agent if `stream-meta.agents` has more than 1 agent
(excluding `user`)". A consumer that reads `mode` to decide which
primitives to expect gets `"jsonl"`, matches nothing, and falls back to
requiring or ignoring the wrong set. **A field whose value is not in its
own enum is not a harmless extra — it is a broken branch.**

The fix is to compute the mode the way ADR-017 says: from the roster.

```python
agents = [a for a in roster if a.get("id") != "user"]
mode = "multi" if len(agents) > 1 else "single"
```

which is what `readers/minimax.py` already does correctly
(`"mode": "single" if not peer_rows else "collab"`). **The MCP adapter is
the outlier, and the fix already exists elsewhere in the codebase.**

### Consequence

`mode` becomes what it was defined to be, and a consumer can rely on it.
No schema change.

---

## Decision 3 — the schema is right; `context` is metadata, and the reader was wrong

**The code changes.** `readers/chrome_devtools.py` emits
`{"type": "context", "details": [...]}` for a "**Data used:**" block inside
an AI block.

ADR-016 is explicit:

> **`context`** → Remove from entry types. Context is session-level metadata
> (already in `context` field of v1.json top-level). If context changes
> during a session, use `observation` with `source: "system"`.

**And ADR-016's own reasoning is right.** Context is not an *event*. It has
no timestamp of its own, no agent, and no place in the causal chain. A
primitive that describes state rather than an occurrence cannot be replayed,
and the format has a replay contract (`spec/replay-semantics.md`).

**But ADR-016 says exactly what to do instead**, and the reader does not
do it: *"`observation` with `source: "system`"*. The block being parsed is
"**Data used:**" — a list of things the agent read. That is an
observation, from the system, about data that was used. The fix is
one line:

```python
return {"type": "observation", "source": "system", "text": ...}
```

**The `details` structure does not survive the change**, and it should not:
`observation` carries `text`, and `attachments` for structured extras. The
parsed details become the observation's text, and the individual
title/text pairs become attachments.

### Consequence

`context` is not an entry type. The 12 primitives are exactly 12. The
reader emits a primitive that can be replayed.

---

## Two more causes, found while fixing the first three

The first three were visible from the schema. Validating each example against
each primitive *separately* — rather than against the `oneOf`, which only
says "not valid under any of the given schemas" — surfaced two more.

### Decision 4 — a missing timestamp is OMITTED, not null

`readers/opencode.py` wrote `"timestamp": None` on todo side-effects, and
53 entries across 10 committed examples carried it. The schema said
`timestamp` was an integer.

**The first instinct was to allow null.** That was wrong. A null value and
an absent value are **different facts**: one says "there is a timestamp and
it is unknown", the other says "there is no timestamp". A format whose
whole argument is provenance cannot afford to blur that.

**And the fix belongs in the reader, not the schema.** A todo update is a
property of the session, not of an instant — there is no moment of its own.
So the reader now **omits the key**:

```python
entry = {
    "type": "side-effect",
    "action": "todo_update",
    "text": todo["content"],
    "status": todo["status"],
}
```

The schema is unchanged, and `timestamp` stays a clean integer-or-absent.
This is the same rule as decision 1, applied to a null instead of a
missing field: **do not loosen the schema to accommodate a value the
producer should not have emitted.**

### Decision 5 — `action.status` gains `running`

Two committed examples carried `"status": "running"`, which is not in the
enum `success | error | partial | pending`.

**`running` is a real state**, and it is the one the readers are most
likely to produce: a tool call that was still in flight when the session
was exported. Every other status describes a *finished* call. A session
exported mid-call is normal, and the format had no way to record it — so
the reader either dropped the status or wrote a value the schema rejected.

**The schema changes.** `running` joins the enum.

**And the flattener was silently dropping constraints.** `tools/flatten_schema.py`
merged only `properties` and `required` from each `allOf` part, so when
decision 1 added `anyOf` to `side-effect`, the generated entry schema
would have quietly lost it — and the two schemas would have disagreed
about what is valid, which is the same three-way drift this project
already closed once. The flattener now carries every keyword a primitive
declares, and the consistency test checks the committed file against the
generator byte for byte.

---

## The principle these decisions share

> **The schema is a contract about what happened. When a reader cannot
> satisfy it, the question is whether the contract is wrong or the reader
> is — and the answer differs per case.**

Two of the three were the reader's fault and one was the schema's. Deciding
them by which was "more convenient" would have got all three wrong, and
would have left a schema that quietly contradicted the data it was
supposed to describe.

The test applied in each case was the same: **would a conformant
implementation of this schema be able to record what the reader is trying
to record?**

- A side-effect with no path? **No** — the schema was wrong.
- A stream whose mode is its file format? **Yes, and the reader was
  wrong** — the schema was right.
- A "data used" block recorded as a context entry? **No** — the reader was
  wrong, and ADR-016 already said what to do instead.

---

## Consequences

### Positive
- (+) **All 68 committed examples validate.** The format's own reference
  corpus is schema-valid, which it was not before.
- (+) `side-effect` can express every persistent state change, not only
  the ones with a filesystem path.
- (+) `mode` becomes meaningful, so a consumer can rely on ADR-017's
  detection rule.
- (+) `context` is gone as an entry type, so the 12 primitives are 12 and
  every one of them is replayable.
- (+) `running` is expressible, so a session exported mid-tool-call can say
  so.
- (+) A missing timestamp is omitted rather than nulled, so "no timestamp"
  and "unknown timestamp" stay different facts.
- (+) The flattener carries every keyword, so the generated schema cannot
  quietly disagree with the canonical one again.

### Negative
- (-) `side-effect` is looser: an entry with only `agent` and `action` is
  valid. That is the cost of not forcing a fabricated path.
- (-) The chrome-devtools reader's `details` structure becomes `text` plus
  attachments, so anything that read `details` directly must be updated.
  Nothing in the repository does — it was never in the schema.
- (-) Two existing example files change shape.

### Neutral
- The 12 primitives are unchanged. `context` was already not one of them.

---

## References

- `spec/ontology.md` — the 12 primitives, and `side-effect`'s definition
- `spec/ADR-015-canonical-schema.md` — JSONL is the only format
- `spec/ADR-016-ontology-enum-reconciliation.md` — `context` demoted to
  metadata, with the replacement specified
- `spec/ADR-017-core-vs-streaming.md` — what `mode` is for
- `spec/replay-semantics.md` — why a non-event cannot be a primitive
- `internal/security/docs/reference/the-drift-audit.md` — the audit that
  found the 17
