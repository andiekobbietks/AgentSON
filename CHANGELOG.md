# Changelog

All notable changes to AgentSON will be documented here. AgentSON uses [Semantic Versioning](https://semver.org/).

## [0.1.0] - 2026-07-05

Initial public release. Apache 2.0 license.

### Specification

- **JSON Schema v1** (`spec/v1.json`) — 8 entry types: `user-query`, `context`, `querying`, `title`, `thought`, `action`, `answer`, `side-effect`
- **JSON Schema v1.1** (`spec/v1.1.json`) — Trajectory semantics: `task`, `outcome`, `observation` entry type, `tool_call_id`, `correlation_id`, `status` on all entries, `duration_ms`, `error` on actions
- Backward compatible: all v1.0 files validate against v1.1

### Readers (6)

- `readers/opencode.py` — opencode SQLite sessions
- `readers/minimax.py` — MiniMax SQLite sessions
- `readers/antigravity.py` — Antigravity IDE protobuf sessions
- `readers/libre.py` — FreeStyle Libre 2 CSV glucose data
- `readers/chrome_devtools.py` — Chrome DevTools AI session traces (9 tests)
- `readers/claude_code.py` — Claude Code JSONL session transcripts

### Importers (1)

- `importers/chatgpt.py` — ChatGPT `conversations.json` → AgentSON

### Exporters (1)

- `exporters/finetune.py` — Unsloth (ShareGPT) + Olive (chat-messages) training formats

### CLI

- `agentson export` — Export sessions from any supported tool
- `agentson import` — Import ChatGPT conversations
- `agentson list` — List sessions with metadata
- `agentson search` — Full-text search across sessions
- `agentson finetune` — Export to training formats
- `agentson render` — Render sessions as Markdown
- `agentson push` — Push to Supabase (optional)
- `agentson pull` — Pull from Supabase (optional)

### Web Viewer

- `docs/viewer/index.html` — Full-featured: file extension + schema validation, download as .AgentSON, search/filter, sort toggle, copy per entry, side-by-side layout, role-based colors, collapsible JSON metadata preview
- `pwa/` — Standalone PWA with offline support

### Documentation

- 14 SOPs (SOP-001 to SOP-014) covering glucose monitoring, AI session export, Nightscout, WhatsApp bot, TV dashboard, MedGemma, NHS FHIR, West Africa voice alerts
- Operating manual: mental models, coding standards, workflow rules, 9 ADRs
- Live docs at `https://andiekobbietks.github.io/AgentSON/`

### Examples

- `examples/opencode_example.AgentSON`
- `examples/minimax_example.AgentSON`
- `examples/antigravity_example.AgentSON`
- `examples/chrome_devtools_example.AgentSON`

### Infrastructure

- PyPI package: `pip install agentson`
- GitHub Actions CI: Pyrefly type checking, pytest
- Branch protection: `andierules` ruleset (PR required, linear history)
- CodeRabbit for AI code review (optional, not required)

### License

- Changed from MIT to Apache 2.0 (patent grant + attribution)
