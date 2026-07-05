# AgentSON

**Agent + JSON** — Yet Another JSON, but metadata-rich and built for the agentic era.

## What's in a Name

| Component | Meaning |
|-----------|---------|
| **Agent** | AI coding agents (Cursor, Claude Code, opencode, MiniMax, etc.) |
| **SON** | JSON — the format it's built on |

Like **JSON** itself — which was "just another data format" but became universal because it was simple, readable, and worked everywhere — **AgentSON** is "just another JSON" but designed specifically for the agentic era.

**AgentSON = Agent + JSON**

It's immediately recognizable (everyone knows JSON), signals the format (it IS JSON with a schema), and differentiates from "yet another format" to "the JSON for agents."

## The Problem

Every AI coding agent stores session data in its own proprietary SQLite database:

| Tool | Database | Tables | Schema |
|------|----------|--------|--------|
| opencode | `opencode.db` | 21 | session, message, part, todo |
| MiniMax | `sqlite.db` | 20 | sessions, session_messages |
| Antigravity IDE | `*.db` | 7 | trajectory_meta, steps |
| Chrome DevTools AI | Preferences JSON | — | user-query, thought, action |

**Nobody has done for agent session logs what OpenAPI did for REST APIs.**

## The Solution

AgentSON provides:

1. **A specification** — JSON Schema for agent session data
2. **Readers** — SQLite parsers for each tool's database
3. **A normalizer** — Converts tool-specific schemas to AgentSON format
4. **A CLI** — Export, search, and render sessions
5. **A VSCode extension** — Hydrate context across tools

## File Extension

AgentSON files use the `.AgentSON` extension:

```
my-session.AgentSON
```

This makes them:
- **Immediately identifiable** — not `.json` (too generic), not `.ailog` (old name)
- **Grep-friendly** — `grep -r "nightscout" *.AgentSON`
- **Tool-associated** — can be associated with the AgentSON CLI or viewer
- **Windows-friendly** — `.agentson` (lowercase) also works on Windows

## Quick Start

```bash
# Install
pip install -e .

# Or from GitHub
pip install git+https://github.com/andiekobbietks/AgentSON.git

# List opencode sessions
agentson list --tool opencode

# Export a session
agentson export --tool opencode --session ses_xxx --output ./sessions/

# Export all sessions
agentson export --tool opencode --all --output ./sessions/

# Render as Markdown
agentson render session.AgentSON --format md

# Export training data (Unsloth/ShareGPT format)
agentson finetune *.AgentSON --format unsloth --output train.jsonl

# Export training data (Olive format)
agentson finetune *.AgentSON --format olive --output train.jsonl

# Push to Supabase (optional)
agentson push session.AgentSON

# Pull from Supabase
agentson pull --search "nightscout"
```

> **Note:** On Windows, if `agentson` command isn't found after install, use `python -m cli.main` instead.

## Schema

```json
{
  "$schema": "https://agentson.dev/schema/v1.json",
  "id": "session-2026-07-04-001",
  "tool": {"name": "opencode", "session_id": "ses_xxx"},
  "agent": {"name": "mimo-v2.5-free", "provider": "opencode"},
  "entries": [
    {"type": "user-query", "text": "..."},
    {"type": "thought", "text": "..."},
    {"type": "action", "tool": "bash", "code": "...", "output": "..."},
    {"type": "answer", "text": "..."},
    {"type": "side-effect", "action": "file_write", "path": "..."}
  ]
}
```

## Entry Types

| Type | Description |
|------|-------------|
| `user-query` | User's input or question |
| `context` | Additional context (data used, DOM info) |
| `querying` | Agent is processing |
| `title` | Section or step title |
| `thought` | Agent's reasoning/thinking |
| `action` | Tool execution (code + output) |
| `answer` | Agent's response |
| `side-effect` | File changes, state mutations |

## Supported Tools

| Tool | Status | Reader |
|------|--------|--------|
| opencode | ✅ Working | `readers/opencode.py` |
| MiniMax | ✅ Working | `readers/minimax.py` |
| Antigravity IDE | ✅ Working | `readers/antigravity.py` |
| Chrome DevTools AI | ⚠️ Unknown storage | JS snippet (experimental) |
| Cursor | 🔜 Planned | — |
| Claude Code | 🔜 Planned | — |

### Chrome DevTools AI Status

Chrome DevTools AI stores session data in an unknown location. The `ai_assistance: {}` field in Preferences JSON is empty, despite extensive usage visible in screenshots. The actual storage mechanism remains unclear — possibly cloud sync or different local storage.

## Use Cases

### For Individuals
- Search your AI history: `grep -r "smtpjs" *.AgentSON`
- Resume sessions in different tools
- Backup that survives tool changes
- Personal training data for fine-tuning

### For Teams
- Audit trail of AI-generated code
- Onboarding: ship new devs your session archive
- Knowledge persistence across team changes

### For Agent Builders
- Standardized eval datasets
- Real session traces for fine-tuning
- Tool-use analysis across agents

## Fine-Tuning Export

Export AgentSON sessions to training formats:

```bash
# Unsloth/ShareGPT format (for LLaMA, Mistral, etc.)
agentson finetune *.AgentSON --format unsloth --output train.jsonl

# Olive format (Microsoft Olive pipeline)
agentson finetune *.AgentSON --format olive --output train.jsonl
```

Example output (Unsloth format):
```json
{
  "conversations": [
    {"from": "human", "value": "How do I fix the auth bug?"},
    {"from": "gpt", "value": "I'll look at the auth module..."}
  ],
  "source": "opencode",
  "session_id": "ses_xxx"
}
```

## PWA Viewer

The `pwa/` directory contains a standalone Progressive Web App for viewing `.AgentSON` files:

1. Open `pwa/index.html` in a browser
2. Drag-and-drop an `.AgentSON` file
3. Browse entries with keyboard navigation
4. Works offline — no server required

To host on GitHub Pages, enable Pages for the `pwa/` directory.

## Architecture

### Two-Layer Design

| Layer | What | Like |
|-------|------|------|
| **Open Spec** | `.AgentSON` file format | Dev Containers — portable, file-based, works offline |
| **Managed Instance** | Supabase backend | GitHub — sync, search, collaboration |

```
Git (local, file-based) → GitHub (cloud, collaboration)
AgentSON (file-based) → AgentSON Cloud (Supabase)
```

### The Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentSON Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Cursor    │  │ Claude Code │  │   opencode  │        │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         .AgentSON Files (Open Spec)                  │   │
│  │     Portable, vendor-neutral, file-based             │   │
│  └─────────────────────────┬───────────────────────────┘   │
│                             │                                │
│              ┌──────────────┼──────────────┐               │
│              ▼              ▼              ▼               │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │
│  │   Local CLI  │ │   Supabase   │ │  Web Viewer  │      │
│  │  (offline)   │ │  (optional)  │ │   (shared)   │      │
│  └──────────────┘ └──────────────┘ └──────────────┘      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Repository Structure

```
agentson/
├── README.md              # This file
├── PRD.md                 # Full product requirements
├── PERSONAS-AND-USER-STORIES.md  # User personas and stories
├── pyproject.toml         # Python packaging (pip install -e .)
├── setup.py               # Backward-compat shim
├── spec/
│   └── v1.json            # JSON Schema
├── readers/               # Tool-specific readers
│   ├── opencode.py        # ✅ Working
│   ├── minimax.py         # ✅ Working
│   ├── antigravity.py     # ✅ Working
│   └── libre.py           # ✅ Working (FreeStyle Libre 2)
├── importers/             # External format importers
│   └── chatgpt.py         # ✅ ChatGPT conversations.json
├── exporters/             # Training data exporters
│   └── finetune.py        # ✅ Unsloth + Olive formats
├── normalizer/            # Schema conversion (planned)
├── renderers/             # Output formats (planned)
├── cli/                   # Command-line interface
│   ├── main.py            # ✅ Working
│   └── supabase_client.py # ✅ Working
├── supabase/              # Managed instance schema
├── tests/                 # Test suite
│   ├── test_opencode.py   # ✅ Passing
│   ├── test_minimax.py    # ✅ Passing
│   └── test_antigravity.py # ✅ Passing
├── examples/              # Example .AgentSON files
│   ├── opencode_example.AgentSON
│   ├── minimax_example.AgentSON
│   └── antigravity_example.AgentSON
├── pwa/                   # Progressive Web App viewer
│   ├── index.html         # ✅ Drag-and-drop viewer
│   ├── manifest.json      # ✅ PWA manifest
│   └── sw.js              # ✅ Service worker
├── viewers/
│   └── web/index.html     # ✅ Working (drag-and-drop viewer)
├── training/
│   └── opencode_example_unsloth.jsonl  # Example training data
└── docs/
    └── sops/              # 14 Standard Operating Procedures
```

## Origin

AgentSON evolved from `.ailog` — a format originally designed for Chrome DevTools AI session export. The schema was discovered in Chrome's Preferences JSON and generalized to cover all AI coding agents.

The name "AgentSON" is a play on JSON — **Agent + JSON** — "Yet Another JSON" but metadata-rich and built for the agentic era.

### What Changed from .ailog

| Aspect | .ailog | AgentSON |
|--------|--------|----------|
| Scope | Chrome DevTools only | All AI coding agents |
| Schema | Undocumented | JSON Schema v1 |
| File extension | `.ailog` | `.AgentSON` |
| Name meaning | AI Log | Agent + JSON |

See [PRD.md](PRD.md) for the full product requirements document.

## License

MIT

---

*"Nobody has done for agent session logs what OpenAPI did for REST APIs or what containers.dev did for dev environments."*
