# Readers

Readers convert tool-specific session data into AgentSON format.

---

## Working Readers (v0.1.0)

| Tool | Reader | Tests | Notes |
|------|--------|-------|-------|
| opencode | `readers/opencode.py` | ✅ | SQLite → AgentSON |
| MiniMax | `readers/minimax.py` | ✅ | SQLite → AgentSON |
| Antigravity IDE | `readers/antigravity.py` | ✅ | Protobuf → AgentSON |
| FreeStyle Libre 2 | `readers/libre.py` | ✅ | CSV → AgentSON (health data) |
| Chrome DevTools AI | `readers/chrome_devtools.py` | ✅ 9 tests | MD export → AgentSON |
| Claude Code | `readers/claude_code.py` | ✅ | JSONL → AgentSON |

---

## Usage

```python
from readers.opencode import read_opencode_session

session = read_opencode_session("ses_xxx", db_path="~/.local/share/opencode/opencode.json")
```

```python
from readers.libre import read_libre_csv

session = read_libre_csv("libre_data.csv")
```

---

## RICE-Scored Roadmap

| Priority | Tool | RICE Score | Status |
|----------|------|------------|--------|
| 1 | Cursor | 2700 | Planned |
| 2 | GitHub Copilot | 4000 | Planned |
| 3 | Claude Code | ∞ | Working |
| 4 | Codex CLI | 1920 | Planned |
| 5 | Gemini CLI | 1400 | Planned |
| 6 | Cline | 1350 | Planned |
| 7 | Aider | 1350 | Planned |
| 8 | Kiro | 1120 | Planned |
| 9 | opencode | ∞ | Working |
| 10 | Replit | 150 | Planned |

---

## Adding a New Reader

1. Create `readers/<tool_name>.py`
2. Implement `read_<tool>_session(session_id, **kwargs) -> dict`
3. Return AgentSON-compatible dict with `entries` array
4. Add test fixtures in `tests/`
5. Update this wiki page
6. Submit PR

### Reader Template

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
    
    # TODO: Implement reader
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

---

## Tool Landscape

AgentSON covers 33 tools across 7 tiers:

| Tier | Tools | Status |
|------|-------|--------|
| Core Market | Cursor, Claude Code, Kiro, Codex CLI, Gemini CLI, Windsurf | Partial |
| Open Source | opencode, Cline, Aider, Zed, Goose, OpenHands | Partial |
| Extensions | Copilot, Amazon Q, JetBrains, Cody, Qodo, Augment, Continue, Tabnine | Planned |
| Builders | Bolt.new, v0, Lovable, Replit | Planned |
| Orchestrators | amux, Claude Squad, Kilo Code, dmux | Planned |
| Autonomous | Devin, Blitzy | Planned |
| China Plans | GLM Coding, Kimi, Qwen Code | Deferred |

See [ROADMAP.md](../ROADMAP.md) for full RICE scoring.
