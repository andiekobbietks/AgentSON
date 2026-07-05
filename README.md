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
# List opencode sessions
python cli/main.py list --tool opencode

# Export a session
python cli/main.py export --tool opencode --session ses_xxx --output ./sessions/

# Export all sessions
python cli/main.py export --tool opencode --all --output ./sessions/

# Render as Markdown
python cli/main.py render session.AgentSON --format md

# Push to Supabase (optional)
python cli/main.py push session.AgentSON

# Pull from Supabase
python cli/main.py pull --search "nightscout"
```

## Schema

```json
{
  "$schema": "https://agentsong.dev/schema/v1.json",
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
| Chrome DevTools AI | ✅ Working | JS snippet |
| Cursor | 🔜 Planned | — |
| Claude Code | 🔜 Planned | — |

## Use Cases

### For Individuals
- Search your AI history: `grep -r "smtpjs" *.agentsong`
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

## Architecture

### Two-Layer Design

| Layer | What | Like |
|-------|------|------|
| **Open Spec** | `.agentsong` file format | Dev Containers — portable, file-based, works offline |
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
agentsong/
├── README.md              # This file
├── PRD.md                 # Full product requirements
├── spec/
│   └── v1.json            # JSON Schema
├── readers/               # Tool-specific readers
│   ├── opencode.py
│   ├── minimax.py
│   └── antigravity.py
├── normalizer/            # Schema conversion
├── renderers/             # Output formats (md, html)
├── cli/                   # Command-line interface
├── supabase/              # Managed instance schema
├── tests/                 # Test suite
└── examples/              # Example .agentsong files
```

## Origin

AgentSON evolved from `.ailog` — a format originally designed for Chrome DevTools AI session export. The schema was discovered in Chrome's Preferences JSON and generalized to cover all AI coding agents.

The name "AgentSON" is a play on JSON — **Agent + JSON** — "Yet Another JSON" but metadata-rich and built for the agentic era.

See [PRD.md](PRD.md) for the full product requirements document.

## License

MIT

---

*"Nobody has done for agent session logs what OpenAPI did for REST APIs or what containers.dev did for dev environments."*
