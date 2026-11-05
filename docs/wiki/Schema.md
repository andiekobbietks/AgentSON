# Schema Reference

AgentSON uses JSON Schema for validation. Two versions exist:

- **v1.0** — Original format (8 entry types)
- **v1.1** — Trajectory semantics (adds task, outcome, observation, correlation)

All v1.0 files validate against v1.1 (backward compatible).

---

## Schema URLs

```
https://agentson.dev/schema/v1.json
https://agentson.dev/schema/v1.1.json
```

---

## Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `$schema` | string | Yes | Schema URL |
| `id` | string | Yes | Unique session identifier |
| `task` | string | No | High-level task description |
| `outcome` | string | No | `success`, `failure`, `partial`, `abandoned` |
| `tool` | object | No | Tool metadata (`name`, `session_id`) |
| `agent` | object | No | Agent metadata (`name`, `provider`) |
| `entries` | array | Yes | Array of entry objects |
| `metadata` | object | No | Arbitrary key-value pairs |

---

## Entry Types (v1.1)

| Type | Description | Key Fields |
|------|-------------|------------|
| `user-query` | User's input or question | `text` |
| `context` | Additional context (data used, DOM info) | `text`, `source` |
| `querying` | Agent is processing | `text` |
| `title` | Section or step title | `text` |
| `thought` | Agent's reasoning/thinking | `text` |
| `action` | Tool execution (code + output) | `tool`, `code`, `output`, `tool_call_id` |
| `answer` | Agent's response | `text` |
| `side-effect` | File changes, state mutations | `tool`, `code`, `tool_call_id` |
| `observation` | Async observation from tool/user/system | `text`, `correlation_id` |

---

## v1.1 Additions

### Task & Outcome

```json
{
  "task": "Fix the authentication bug in the login flow",
  "outcome": "success"
}
```

- `task` — Human-readable description of what the session was trying to accomplish
- `outcome` — One of: `success`, `failure`, `partial`, `abandoned`

### Correlation ID

Links actions to their observations:

```json
{"type": "action", "tool": "bash", "code": "grep -r 'auth' src/", "tool_call_id": "tc_001"}
{"type": "observation", "text": "Found 3 files", "correlation_id": "tc_001"}
```

### Duration & Error

```json
{"type": "action", "tool": "bash", "code": "pytest", "duration_ms": 1234, "error": "2 tests failed"}
```

---

## Example: Complete Session

```json
{
  "$schema": "https://agentson.dev/schema/v1.1.json",
  "id": "session-2026-07-04-001",
  "task": "Fix the authentication bug in the login flow",
  "outcome": "success",
  "tool": {"name": "opencode", "session_id": "ses_xxx"},
  "agent": {"name": "mimo-v2.5-free", "provider": "opencode"},
  "metadata": {
    "project": "agentson",
    "branch": "feat/auth-fix",
    "duration_ms": 45000
  },
  "entries": [
    {"type": "user-query", "text": "Fix the auth bug", "timestamp": "2026-07-04T10:00:00Z"},
    {"type": "thought", "text": "Looking at the auth module, I see the null check is missing in auth.py line 42"},
    {"type": "action", "tool": "bash", "code": "grep -r 'auth' src/", "tool_call_id": "tc_001", "timestamp": "2026-07-04T10:00:05Z"},
    {"type": "observation", "text": "Found 3 files: src/auth.py, src/auth_test.py, src/middleware.py", "correlation_id": "tc_001"},
    {"type": "action", "tool": "edit", "code": "if user is not None and user.is_active:", "tool_call_id": "tc_002"},
    {"type": "observation", "text": "Edit applied to src/auth.py:42", "correlation_id": "tc_002"},
    {"type": "action", "tool": "bash", "code": "pytest src/auth_test.py", "tool_call_id": "tc_003"},
    {"type": "observation", "text": "All tests passed", "correlation_id": "tc_003"},
    {"type": "answer", "text": "Fixed the null check in auth.py:42. All tests pass."}
  ]
}
```

---

## Validation

```bash
# Validate a file
python -c "import json; d=json.load(open('session.AgentSON')); assert d.get('\$schema')"

# Full schema validation
pip install jsonschema
python -c "
import json, jsonschema
schema = json.load(open('spec/v1.1.json'))
instance = json.load(open('session.AgentSON'))
jsonschema.validate(instance, schema)
print('Valid')
"
```
