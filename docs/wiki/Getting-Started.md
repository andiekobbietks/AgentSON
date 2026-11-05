# Getting Started

## Installation

```bash
pip install agentson
```

## Export Your First Session

```bash
# List sessions from opencode
agentson list --tool opencode

# Export a specific session
agentson export --tool opencode --session ses_xxx --output ./sessions/

# Export all sessions
agentson export --tool opencode --output ./sessions/
```

## View in Browser

### PWA (Offline)

Open `pwa/index.html` in any browser. Drag and drop an `.AgentSON` file.

### Web Viewer

Visit [andiekobbietks.github.io/AgentSON/viewer/](https://andiekobbietks.github.io/AgentSON/viewer/) for full features:
- JSON Schema validation
- Download as `.AgentSON`
- Full-text search
- Sort by timestamp
- Copy per entry
- Side-by-side layout
- Role-based colors
- Collapsible JSON metadata preview

## Search Across Sessions

```bash
# Search for a keyword across all sessions
agentson search "nightscout" --tool opencode

# Search in specific tool
agentson search "auth bug" --tool claude-code
```

## Export for Fine-Tuning

```bash
# Unsloth/ShareGPT format (LLaMA, Mistral, etc.)
agentson finetune *.AgentSON --format unsloth --output train.jsonl

# Olive format (Microsoft Olive pipeline)
agentson finetune *.AgentSON --format olive --output train.jsonl
```

## Render as Markdown

```bash
agentson render session.AgentSON --format md
```

## Push to Supabase (Optional)

```bash
agentson push session.AgentSON
```

---

## Supported Tools (v0.1.0)

| Tool | Status | Reader |
|------|--------|--------|
| opencode | ✅ Working | `readers/opencode.py` |
| MiniMax | ✅ Working | `readers/minimax.py` |
| Antigravity IDE | ✅ Working | `readers/antigravity.py` |
| FreeStyle Libre 2 | ✅ Working | `readers/libre.py` |
| Chrome DevTools AI | ✅ Working | `readers/chrome_devtools.py` |
| Claude Code | ✅ Working | `readers/claude_code.py` |

See [Readers](Readers) for the full 33-tool roadmap.

---

## What's in an AgentSON File?

```json
{
  "$schema": "https://agentson.dev/schema/v1.1.json",
  "id": "session-2026-07-04-001",
  "task": "Fix the authentication bug in the login flow",
  "outcome": "success",
  "tool": {"name": "opencode", "session_id": "ses_xxx"},
  "agent": {"name": "mimo-v2.5-free", "provider": "opencode"},
  "entries": [
    {"type": "user-query", "text": "Fix the auth bug"},
    {"type": "thought", "text": "Looking at the auth module..."},
    {"type": "action", "tool": "bash", "code": "grep -r 'auth' src/", "tool_call_id": "tc_001"},
    {"type": "observation", "text": "Found 3 files", "correlation_id": "tc_001"},
    {"type": "answer", "text": "Fixed the null check in auth.py"}
  ]
}
```

See [Schema](Schema) for the full reference.
