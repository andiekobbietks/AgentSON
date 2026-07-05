# Changelog

All notable changes to AgentSON will be documented here. AgentSON uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **File extension casing** (`.AgentSON` → `.agentson`): every writer, reader,
  CLI export path, and search glob across `cli/main.py`, `readers/claude_code.py`,
  `importers/chatgpt.py`, and `tests/test_claude_code.py` used the brand-name
  casing instead of the lowercase extension decided in ADR-011. Fixed everywhere
  in one pass rather than piecemeal, since a partial fix (writer changed, glob
  not) would have silently broken file search on case-sensitive filesystems.
- **`importers/chatgpt.py` could not be imported at all**: a missing indent
  under a `with open(...)` block was a hard `IndentationError`, meaning
  `agentson import chatgpt` has not functioned since this file was committed,
  despite being listed as shipped in the v0.1.0 release notes below.
- **`importers/chatgpt.py` crashed on real ChatGPT exports**: `_detect_model`
  used `node.get("message", {})`, which only supplies the default for a
  *missing* key — ChatGPT's root node has an explicit `"message": null`, so
  the call returned `None` and the next `.get()` raised `AttributeError`.
  This means the "validated against a real export, hidden system-injected
  profile data correctly excluded" claim in the v0.1.0 notes below did not
  reflect a working state of this file; there was also no test file for this
  importer prior to this fix. Added `tests/test_chatgpt_importer.py` with a
  fixture matching the real null-root-message export shape.
- **`readers/opencode.py` silently dropped `reasoning` parts and
  misread `tool` parts**: the reader was built against an older opencode
  part shape (`type: "tool-invocation"`, fields `toolName`/`args`/`result`).
  Verified against a real opencode message/parts export, current opencode
  emits `type: "reasoning"` (previously unhandled, entries silently lost)
  and `type: "tool"` with fields nested under `state` instead. Added
  `tests/fixtures/opencode_real_sample.json` (a real export, not synthetic)
  and `tests/test_opencode_real_sample.py`; old shape kept as a fallback
  for older opencode exports, not removed.

### Known issues (flagged, not yet fixed)

- `tests/test_claude_code.py::test_read_session` fails on `master`
  independent of the above: expects `outcome == "success"`, actual value
  is `"partial"`. Confirmed pre-existing (reproduces on `master` before
  any changes in this entry) and unrelated to the fixes above. Left open
  as a separate issue rather than folded into this fix, since the cause
  hasn't been diagnosed yet.

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
- Operating manual: mental models, coding standards, workflow rules, 10 ADRs
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
