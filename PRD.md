# AgentSON — Product Requirements Document

## Document Status

| Field | Value |
|-------|-------|
| **Version** | 1.0 |
| **Date** | 04 July 2026 |
| **Author** | Andrea Enning (AndieKobbieTech) |
| **Status** | Draft — Ready for Review |

---

## Executive Summary

**AgentSON** — **Agent + JSON** — is a vendor-neutral, portable session capture format and toolkit that enables developers to export, search, hydrate, and replay AI agent sessions across heterogeneous tooling — without losing structured metadata, tool traces, or reasoning chains.

### What's in a Name

| Component | Meaning |
|-----------|---------|
| **Agent** | AI coding agents (Cursor, Claude Code, opencode, MiniMax, etc.) |
| **SON** | JSON — the format it's built on |

Like **JSON** itself — which was "just another data format" but became universal because it was simple, readable, and worked everywhere — **AgentSON** is "just another JSON" but designed specifically for the agentic era.

**AgentSON = Agent + JSON**

It solves a problem that currently has no standard solution: every AI coding agent (Chrome DevTools AI, Cursor, Claude Code, Copilot Chat, opencode, MiniMax, Antigravity IDE) stores session data in its own proprietary SQLite database with a unique schema. There is no shared wire format, no standard export API, and no way to move session context from one tool to another without lossy manual conversion.

AgentSON is the answer to that gap.

---

## 1. Problem Statement

### 1.1 The Current State

Every AI coding agent on the market today stores session data in a proprietary format:

| Tool | Database | Tables | Schema |
|------|----------|--------|--------|
| **opencode** | `opencode.db` | 21 | session, message, part, todo, event |
| **MiniMax** | `sqlite.db` | 20 | sessions, session_messages, token_usage |
| **Antigravity IDE** | `*.db` | 7 | trajectory_meta, steps, gen_metadata |
| **Chrome DevTools AI** | Preferences JSON | — | user-query, thought, action, answer |

Each database is:
- **Locally accessible** — no encryption, no auth required
- **Different schema** — no shared table structure
- **No export API** — must write custom Python scripts to extract data
- **Lossy when exported** — Markdown export loses tool traces, diffs, metadata

### 1.2 The Evidence

On a single Windows laptop, three AI coding tools were found with three different SQLite databases:

```
opencode.db      → 1.6 GB, 21 tables, 7,769 messages, 30,295 parts
minimax.sqlite   → 22 MB, 20 tables, 1,490 messages
antigravity.db   → 7 MB, 7 tables, 437 steps
```

To export a single session from opencode required:
```python
# Custom Python script — 80+ lines
cursor.execute("SELECT * FROM message WHERE session_id = ?")
cursor.execute("SELECT * FROM part WHERE session_id = ?")
cursor.execute("SELECT * FROM todo WHERE session_id = ?")
# ... parse JSON-within-SQLite, assemble into new structure
```

To export the same session from MiniMax required a **different** script because the schema is different.

To export from Antigravity required a **third** script — and the built-in export button is buggy and often fails.

### 1.3 The Gap

**Nobody has done for agent session logs what OpenAPI did for REST APIs or what containers.dev did for dev environments.**

- Agent definition standards exist (A2A, ACP, Agent Format) — but they describe capabilities, not session transcripts
- Agent memory standards are emerging (memorywire, May 2026) — but they address memory persistence, not action traces
- Academic benchmark datasets exist (Mind2Web, UI-TARS, GUI-Owl) — but they capture curated lab tasks, not live, unstructured work

**The missing piece is a portable, vendor-neutral format for capturing real, ordinary work sessions — not benchmark construction, not memory persistence, but the full trace of what an agent did, thought, and produced during a live session.**

---

## 2. Origin Story

### 2.1 Phase 1: Chrome DevTools AI Export (June 2026)

The problem was first discovered when Chrome DevTools AI Assistance removed its Markdown export button in Chrome 149 (June 2, 2026). A workaround was built — a JavaScript snippet that walks the shadow DOM and extracts the conversation into Markdown.

During this work, a typed schema was discovered in Chrome's Preferences JSON:

```json
{
  "type": "user-query",
  "query": "in what kind of stack was this site entirely coded?",
  "title": "Gathering tech stack information",
  "thought": "I need to identify the tech stack by looking at...",
  "action": {"code": "const scripts = Array.from(...)", "output": "{...}"},
  "answer": "Based on the architectural patterns...",
  "side-effect": "Updated styles.css line 142"
}
```

This schema — `user-query`, `title`, `thought`, `action{code,output}`, `answer`, `side-effect` — turned out to be the **minimal complete vocabulary** for any agent that has thoughts, takes actions, and produces answers.

### 2.2 Phase 2: `.ailog` Format (June 2026)

The schema was formalized as `.ailog` — a single-file, vendor-neutral transcript format for AI agent sessions. A detailed analysis identified 85 use cases across personal, team, community, commercial, and educational categories.

The key insight: **every AI coding agent produces the same conceptual output** (thoughts + actions + answers), but they all store it differently. A shared format would enable:
- Portable session archives
- Cross-tool context hydration
- Searchable AI history
- Reproducible agent traces

### 2.3 Phase 3: AgentSON (July 2026)

`.ailog` evolved into **AgentSON** as the scope expanded from Chrome DevTools to cover all AI coding agents on the system. The name is a play on **JSON** — **Agent + JSON** — "Yet Another JSON" but metadata-rich and built for the agentic era.

**Agent Session Object Notation** — a structured representation of agent session data that can be read, written, and transferred across any tooling.

**File extension:** `.AgentSON`

---

## 3. Product Vision

### 3.1 What AgentSON Is

AgentSON is:

1. **A specification** — a JSON Schema defining the structure of agent session data
2. **A set of readers** — SQLite parsers for each supported tool's database
3. **A normalizer** — converts tool-specific schemas into the AgentSON format
4. **A CLI** — command-line tool for exporting, searching, and rendering sessions
5. **A VSCode extension** — hydrates context across tools within the IDE
6. **An export API** — programmatic access to session data from any tool

### 3.2 What AgentSON Is NOT

AgentSON is NOT:

- A real-time observability platform (that's Langfuse, Helicone)
- A chat UI (it's a file format + tooling)
- A memory persistence layer (that's memorywire, Letta)
- Vendor-specific (it works across all tools)
- A replacement for tool-native export (it standardizes the output)

### 3.3 Core Value Proposition

> "Capture live, ordinary work as structured, portable session data — not curated benchmark tasks, not memory snapshots, but the full trace of what happened."

---

## 4. User Personas

### 4.1 Solo Developer (Primary)

**Who:** Individual developers using one or more AI coding agents daily.

**Pain:**
- 54+ DevTools AI chats scattered across Chrome, all basically unsearchable
- When Cursor crashes, session history is lost
- Can't resume a conversation in a different tool without re-explaining
- No way to grep "what did I use to fix X?" across AI sessions

**Value:**
- Personal search engine over all AI work
- Portable session archive that survives tool changes
- Re-feed any session to a fresh model as context

### 4.2 Team Lead

**Who:** Engineering managers and tech leads overseeing AI-assisted development.

**Pain:**
- No audit trail of what AI generated or saw
- Onboarding new devs requires explaining AI workflows from scratch
- Knowledge leaves when people leave

**Value:**
- Audit trail for legal/security review
- Onboarding archive: "here's how we actually work"
- Knowledge persistence across team changes

### 4.3 Agent Builder / AI Startup

**Who:** Teams building AI agents, coding assistants, or AI-powered tools.

**Pain:**
- No standardized eval datasets for agent behavior
- Training data is vendor-locked or synthetic
- Can't reproduce agent behavior across sessions

**Value:**
- `.AgentSON` files become reproducible benchmark fixtures
- Real session traces for fine-tuning agentic models
- Tool-use analysis across agents

### 4.4 Researcher

**Who:** Academic researchers studying human-AI collaboration.

**Pain:**
- Each academic dataset defines its own bespoke schema
- No cross-agent comparison possible
- Reproducibility is difficult

**Value:**
- Standardized format for cross-agent comparison
- Real-world session data (not lab conditions)
- Reproducible agent traces for papers

---

## 5. Technical Architecture

### 5.1 AgentSON Schema (v1)

```json
{
  "$schema": "https://agentsong.dev/schema/v1.json",
  "id": "session-2026-07-04-001",
  "tool": {
    "name": "opencode",
    "version": "0.0.13",
    "session_id": "ses_1069f6208ffeXozEyNyMW6RXOO"
  },
  "agent": {
    "name": "mimo-v2.5-free",
    "provider": "opencode",
    "variant": "high"
  },
  "started_at": "2026-06-24T10:00:00Z",
  "ended_at": "2026-07-04T23:17:00Z",
  "context": {
    "working_directory": "C:\\Users\\LLM-Test\\Documents",
    "platform": "win32",
    "shell": "powershell"
  },
  "entries": [
    {
      "type": "user-query",
      "text": "What did we do so far?",
      "timestamp": 1782300319717
    },
    {
      "type": "thought",
      "text": "The user is asking for a summary of prior work...",
      "model": "mimo-v2.5-free",
      "tokens": {"input": 553261, "output": 107858}
    },
    {
      "type": "action",
      "tool": "bash",
      "code": "Get-ChildItem -Path \"C:\\Users\\LLM-Test\\Documents\" -Filter \"*.csv\"",
      "output": "libre_data.csv",
      "status": "success"
    },
    {
      "type": "answer",
      "text": "Here's what we've accomplished so far...",
      "format": "markdown"
    },
    {
      "type": "side-effect",
      "action": "file_write",
      "path": "C:\\Users\\LLM-Test\\Downloads\\AGENTSON-PRD.md",
      "diff": "+187 lines"
    }
  ],
  "metadata": {
    "total_tokens": 661119,
    "cost": 0.0,
    "messages": 194,
    "parts": 601
  }
}
```

### 5.2 Supported Source Formats

| Source Tool | Database Location | Reader Module |
|-------------|-------------------|---------------|
| **opencode** | `~/.local/share/opencode/opencode.db` | `readers/opencode.py` |
| **MiniMax** | `~/.minimax/sqlite.db` | `readers/minimax.py` |
| **Antigravity IDE** | `~/.gemini/antigravity-ide/conversations/*.db` | `readers/antigravity.py` |
| **Chrome DevTools AI** | `~\AppData\Local\Google\Chrome\User Data\*\Preferences` | `readers/chrome_devtools.py` |
| **Cursor** | `~/.cursor/User/workspaceStorage/*/state.vscdb` | `readers/cursor.py` (planned) |
| **Claude Code** | `~/.claude/sessions/` | `readers/claude_code.py` (planned) |

### 5.3 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    AgentSON Architecture                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Cursor    │  │ Claude Code │  │   opencode  │  ...   │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘        │
│         │                │                │                  │
│         ▼                ▼                ▼                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │         .AgentSON Files (Open Spec)                 │   │
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
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    API Layer                         │   │
│  │  GET /sessions?search=nightscout                    │   │
│  │  POST /sessions (upload .AgentSON)                 │   │
│  │  GET /sessions/:id (download)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.4 Two-Layer Design

| Layer | What | Like |
|-------|------|------|
| **Open Spec** | `.AgentSON` file format | Dev Containers — portable, file-based, works offline |
| **Managed Instance** | Supabase backend | GitHub — sync, search, collaboration |

```
Git (local, file-based) → GitHub (cloud, collaboration)
AgentSON (file-based) → AgentSON Cloud (Supabase)
```

---

## 6. Features

### 6.1 Phase 1 — Core Export (MVP)

| Feature | Priority | Status |
|---------|----------|--------|
| AgentSON JSON Schema v1 | P0 | Draft |
| opencode reader | P0 | Working |
| MiniMax reader | P0 | Working |
| Antigravity IDE reader | P0 | Working |
| Chrome DevTools AI reader | P1 | Working (JS snippet) |
| `agentsong export` CLI | P0 | Planned |
| `agentsong search` CLI | P1 | Planned |
| `agentsong render` CLI (md, html) | P1 | Planned |

### 6.2 Phase 2 — Cross-Tool Hydration

| Feature | Priority | Status |
|---------|----------|--------|
| VSCode extension | P0 | Planned |
| Context hydration API | P0 | Planned |
| `agentsong hydrate` command | P0 | Planned |
| Cursor reader | P1 | Planned |
| Claude Code reader | P1 | Planned |

### 6.3 Phase 3 — Advanced Features

| Feature | Priority | Status |
|---------|----------|--------|
| `agentsong diff` — compare sessions | P2 | Planned |
| `agentsong replay` — re-feed to model | P2 | Planned |
| Web viewer (drag-and-drop) | P2 | Planned |
| Team sync / cloud storage | P3 | Planned |
| Analytics dashboard | P3 | Planned |

---

## 7. CLI Interface

### 7.1 Export

```bash
# Export current opencode session
agentsong export --tool opencode --session ses_1069f6208ffeXozEyNyMW6RXOO

# Export all MiniMax sessions
agentsong export --tool minimax --all

# Export specific Antigravity conversation
agentsong export --tool antigravity --id 9a54d356-610a-4225-bcba-f0e3048cf866

# Export to specific format
agentsong export --tool opencode --format json --output ./sessions/
agentsong export --tool opencode --format md --output ./sessions/
```

### 7.2 Search

```bash
# Search all sessions for a term
agentsong search "nightscout" --all

# Search specific tool
agentsong search "fhir" --tool opencode

# Search with date range
agentsong search "sensor" --from 2026-06-01 --to 2026-06-30

# Output as JSON
agentsong search "diabetes" --format json
```

### 7.3 Render

```bash
# Render session as Markdown
agentsong render session.AgentSON --format md

# Render session as HTML with syntax highlighting
agentsong render session.AgentSON --format html

# Render to terminal
agentsong render session.AgentSON --format terminal
```

### 7.4 Hydrate

```bash
# Hydrate context from one tool to another
agentsong hydrate --from opencode --to cursor --session ses_xxx

# Hydrate last session automatically
agentsong hydrate --auto

# Upload to Supabase (optional)
agentsong push session.AgentSON

# Pull from Supabase
agentsong pull --search "nightscout"
```

---

## 8. Repository Structure

```
agentsong/
├── README.md                    # Project overview and quick start
├── PRD.md                       # This document
├── spec/
│   └── v1.json                  # AgentSON JSON Schema
├── readers/
│   ├── opencode.py              # opencode SQLite reader
│   ├── minimax.py               # MiniMax SQLite reader
│   ├── antigravity.py           # Antigravity IDE SQLite reader
│   ├── chrome_devtools.py       # Chrome DevTools AI parser
│   ├── cursor.py                # Cursor reader (planned)
│   └── claude_code.py           # Claude Code reader (planned)
├── normalizer/
│   ├── __init__.py
│   └── convert.py               # Tool-specific → AgentSON conversion
├── renderers/
│   ├── markdown.py              # → .md (Chrome-compatible)
│   ├── html.py                  # → .html (syntax highlighted)
│   └── terminal.py              # → terminal output
├── cli/
│   ├── __init__.py
│   └── main.py                  # CLI entry point
├── supabase/
│   ├── schema.sql               # Database schema
│   ├── migrations/              # Supabase migrations
│   └── edge-functions/          # API edge functions
├── vscode-extension/
│   ├── package.json
│   └── src/
│       └── extension.ts         # VSCode extension
├── viewers/
│   └── web/                     # Drag-and-drop web viewer
├── tests/
│   ├── test_opencode.py
│   ├── test_minimax.py
│   └── test_antigravity.py
└── examples/
    ├── opencode_session.AgentSON    # Example export
    ├── minimax_session.AgentSON
    └── antigravity_session.AgentSON
```

---

## 9. Success Metrics

### 9.1 Adoption

| Metric | Target (3 months) | Target (6 months) |
|--------|-------------------|-------------------|
| GitHub stars | 100 | 500 |
| PyPI downloads | 500 | 5,000 |
| VSCode installs | 100 | 1,000 |
| Supported tools | 4 | 8 |

### 9.2 Usage

| Metric | Target |
|--------|--------|
| Sessions exported per user | 10+ |
| Search queries per user | 50+ |
| Cross-tool hydrations | 5+ per user |

### 9.3 Community

| Metric | Target |
|--------|--------|
| Contributors | 5+ |
| Issues closed | 20+ |
| PRs merged | 10+ |

---

## 10. Competitive Landscape

| Project | What It Does | AgentSON Difference |
|---------|--------------|---------------------|
| **antigravity-history** | Export Antigravity conversations | Single-tool only, Markdown/JSON |
| **memorywire** (arXiv May 2026) | Memory wire format standard | Memory ≠ action traces |
| **OpenLLMetry** | Distributed tracing for LLMs | Telemetry pipeline, not file-based |
| **Langfuse** | LLM observability platform | Heavy infra, not portable |
| **Mind2Web / UI-TARS** | Benchmark datasets | Curated tasks, not live work |

**AgentSON's unique position:** The only project focused on **portable, file-based, vendor-neutral agent session capture for live, ordinary work** — not benchmarks, not memory, not observability.

---

## 11. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tools lock down SQLite access | Low | High | Document workarounds, advocate for export APIs |
| Schema changes break readers | Medium | Medium | Versioned readers, community maintenance |
| Low adoption | Medium | Medium | Start with own use case, prove value |
| Legal/privacy concerns | Low | Medium | Local-only processing, no cloud upload |
| Competition from vendors | Medium | Low | Vendor-neutral positioning, open spec |

---

## 12. Roadmap

### Q3 2026 (July–September)

- [ ] Publish AgentSON v1 specification
- [ ] Release opencode, MiniMax, Antigravity readers
- [ ] Release CLI (`agentsong export`, `search`, `render`)
- [ ] Publish to PyPI
- [ ] Write README with 85 use cases
- [ ] Submit to Hacker News / Reddit / Dev.to

### Q4 2026 (October–December)

- [ ] Release VSCode extension
- [ ] Add Cursor and Claude Code readers
- [ ] Implement `agentsong hydrate`
- [ ] Build web viewer
- [ ] Deploy Supabase managed instance
- [ ] Add `agentsong push/pull` for cloud sync
- [ ] Reach 100 GitHub stars

### Q1 2027 (January–March)

- [ ] Add team sync features
- [ ] Build analytics dashboard
- [ ] Full-text search via Supabase
- [ ] API access for third-party tools
- [ ] Reach 500 GitHub stars
- [ ] Seek sponsorship or funding

---

## 13. Appendix: The Evidence

### 13.1 SQLite Databases Found on System

```
C:\Users\LLM-Test\.local\share\opencode\opencode.db     (1.6 GB, 21 tables)
C:\Users\LLM-Test\.minimax\sqlite.db                    (22 MB, 20 tables)
C:\Users\LLM-Test\.gemini\antigravity-ide\conversations\9a54d356-*.db  (7 MB, 7 tables)
```

### 13.2 Schemas Compared

**opencode (21 tables):**
- session, message, part, todo, event, project, workspace, permission, session_share, account, account_state, control_account, event_sequence, migration, session_message, data_migration, project_directory, session_input, session_context_epoch, sqlite_sequence, __drizzle_migrations

**MiniMax (20 tables):**
- sessions, session_messages, session_peers, agents, token_usage, permissions, skills, skill_hub, activity_screenshots, activity_insights, questionnaire_requests, session_turn_file_change_journal, session_turn_file_changes, session_project_groups, browser_tab_claims, delegation_message, logic_version, preferences, permission_requests, sqlite_sequence

**Antigravity IDE (7 tables):**
- trajectory_meta, steps, gen_metadata, executor_metadata, parent_references, trajectory_metadata_blob, battle_mode_infos

### 13.3 Custom Scripts Required for Export

**opencode export:**
```python
cursor.execute("SELECT * FROM message WHERE session_id = ?", (sid,))
cursor.execute("SELECT * FROM part WHERE session_id = ?", (sid,))
cursor.execute("SELECT * FROM todo WHERE session_id = ?", (sid,))
```

**MiniMax export:**
```python
cursor.execute("SELECT * FROM session_messages WHERE session_id = ?", (sid,))
cursor.execute("SELECT * FROM token_usage WHERE session_id = ?", (sid,))
```

**Antigravity export:**
```python
cursor.execute("SELECT * FROM steps WHERE ...")
cursor.execute("SELECT * FROM gen_metadata WHERE ...")
```

**Three different databases. Three different schemas. Three different scripts. No standardization.**

---

## 14. Supabase Managed Instance

### 14.1 Why Supabase?

A managed instance supercharges AgentSON with:

| Feature | Without Supabase | With Supabase |
|---------|------------------|---------------|
| Portable files | ✅ | ✅ |
| Works offline | ✅ | ✅ |
| Vendor-neutral | ✅ | ✅ |
| No sync across devices | ❌ | ✅ |
| No team features | ❌ | ✅ |
| No full-text search | ❌ | ✅ |
| No API access | ❌ | ✅ |

### 14.2 Schema

```sql
-- Supabase schema
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tool TEXT NOT NULL,
  agent TEXT,
  started_at TIMESTAMPTZ,
  ended_at TIMESTAMPTZ,
  data JSONB NOT NULL,
  search_vector TSVECTOR GENERATED ALWAYS AS (
    to_tsvector('english', data->>'entries')
  ) STORED,
  user_id UUID REFERENCES auth.users(id),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Full-text search index
CREATE INDEX sessions_search_idx ON sessions USING GIN(search_vector);

-- RLS policies
ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own sessions" ON sessions
  FOR SELECT USING (auth.uid() = user_id);
```

### 14.3 API Endpoints

```bash
# Upload session
POST /sessions
Content-Type: application/json
Authorization: Bearer <token>

# Download session
GET /sessions/:id

# Search sessions
GET /sessions?search=nightscout

# List user's sessions
GET /sessions?user_id=<uuid>
```

### 14.4 CLI Integration

```bash
# Push to Supabase
agentsong push session.AgentSON

# Pull from Supabase
agentsong pull --search "nightscout"

# Sync all sessions
agentsong sync --all
```

---

## 15. Conclusion

AgentSON is not a hypothetical product. The problem it solves has been demonstrated on this machine, with real databases, real scripts, and real data. The gap is documented. The use cases are enumerated. The schema is defined.

**AgentSON = Agent + JSON**

It's "Yet Another JSON" — but metadata-rich and built for the agentic era. Like JSON itself, it's simple, readable, and works everywhere. The difference: this one captures the full trace of what an AI agent did, thought, and produced.

The only thing left is to build it.

---

*"Nobody has done for agent session logs what OpenAPI did for REST APIs or what containers.dev did for dev environments."*

*AgentSON is that.*
