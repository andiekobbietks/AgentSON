# Issue: Add Cursor, Cline, and Aider readers

## Summary

Ship readers for Cursor, Cline, and Aider — covering Tier 1 and Tier 2 of the RICE roadmap. This brings AgentSON from 6 readers to 9, ahead of AgentLog (2 working readers).

## Readers added

| Reader | Storage format | Tests | Status |
|--------|---------------|-------|--------|
| cursor | SQLite key-value (`state.vscdb`) | 10 | Working |
| cline | JSON files (`api_conversation_history.json`) | 9 | Working |
| aider | Markdown (`.aider.chat.history.md`) | 10 | Working |

## Files changed

- `readers/cursor.py` — Cursor IDE reader
- `readers/cline.py` — Cline VS Code extension reader
- `readers/aider.py` — Aider CLI reader
- `tests/test_cursor.py` — Cursor tests
- `tests/test_cline.py` — Cline tests
- `tests/test_aider.py` — Aider tests
- `readers/__init__.py` — Updated exports
- `cli/main.py` — Updated CLI to support cursor/cline/aider

## CLI usage

```bash
agentson export --tool cursor --all --output ./sessions/
agentson export --tool cline --all --output ./sessions/
agentson export --tool aider --all --output ./sessions/
agentson list --tool cursor
agentson list --tool cline
agentson list --tool aider
```

## Context

AgentLog (braintied/agentlog) has Cursor, Cline, and Aider as "planned" but no working implementations. This PR puts AgentSON ahead with 9 working readers vs. AgentLog's 2.

## Test results

50/51 tests pass (1 pre-existing failure in `test_claude_code.py` unrelated to this change).

## PR

Branch: `feat/cursor-cline-aider-readers`
Commit: `25b843a`
