# Contributing

How to add a reader, write tests, or submit a PR.

---

## Adding a New Reader

### 1. Create the Reader

Create `readers/<tool_name>.py`:

```python
"""
<Tool Name> reader for AgentSON.

Converts <Tool Name> session data to AgentSON format.
"""

import json
from typing import Dict, List, Optional


def read_<tool>_session(session_id: str, db_path: Optional[str] = None) -> Dict:
    """
    Read a <Tool Name> session and convert to AgentSON format.
    
    Args:
        session_id: The session identifier
        db_path: Path to the database file (optional)
    
    Returns:
        AgentSON session dict
    """
    entries = []
    
    # 1. Connect to database
    # 2. Query session data
    # 3. Convert to AgentSON entry format
    # 4. Return complete session dict
    
    return {
        "$schema": "https://agentson.dev/schema/v1.1.json",
        "id": f"session-{session_id}",
        "tool": {"name": "<tool_name>", "session_id": session_id},
        "entries": entries
    }
```

### 2. Add Test Fixtures

Create `tests/fixtures/<tool_name>/` with real session data (anonymized).

### 3. Write Tests

Create `tests/test_<tool_name>.py`:

```python
import pytest
from readers.<tool_name> import read_<tool>_session


def test_read_session():
    session = read_<tool>_session("test_session", db_path="tests/fixtures/<tool_name>/test.db")
    assert session["tool"]["name"] == "<tool_name>"
    assert len(session["entries"]) > 0


def test_entry_types():
    session = read_<tool>_session("test_session", db_path="tests/fixtures/<tool_name>/test.db")
    valid_types = {"user-query", "context", "querying", "title", "thought", "action", "answer", "side-effect", "observation"}
    for entry in session["entries"]:
        assert entry["type"] in valid_types
```

### 4. Update Documentation

- Add to `wiki/Readers.md`
- Add to `README.md` if working
- Update `CHANGELOG.md`

### 5. Submit PR

- Branch: `feat/<tool-name>-reader`
- Title: `feat(readers): add <Tool Name> reader`
- Tests must pass

---

## Writing Tests

### Test Fixtures

- Use real session data (anonymized)
- Never use synthetic/hand-crafted data
- Store in `tests/fixtures/<tool_name>/`

### Running Tests

```bash
# All tests
pytest

# Specific reader
pytest tests/test_opencode.py

# With coverage
pytest --cov=readers
```

---

## Code Style

- Follow [Coding Standards](Coding-Standards)
- Type hints on all public functions
- Docstrings on all public functions
- No `*` imports
- f-strings over `.format()`

---

## Commit Messages

Format: `type(scope): description`

```
feat(readers): add Claude Code JSONL session reader
fix(adr): correct Cursor valuation reasoning
docs: update landing page with v1.1 trajectory
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

---

## PR Process

1. Fork the repo
2. Create branch: `git checkout -b feat/my-feature`
3. Make changes
4. Run tests: `pytest`
5. Commit: `git commit -m "feat(readers): add My Tool reader"`
6. Push: `git push origin feat/my-feature`
7. Open PR

### PR Checklist

- [ ] Tests pass
- [ ] No PII in code or fixtures
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Status labels honest (working/planned/tested)
