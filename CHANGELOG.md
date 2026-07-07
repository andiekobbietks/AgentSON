# Changelog

All notable changes to AgentSON will be documented here. AgentSON uses [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed

- **`test_claude_code.py::test_read_session` failure** (flagged as a known
  issue in v0.1.1): not a reader bug. `readers/claude_code.py`'s own
  docstring documents a `{"type": "summary", ...}` JSONL entry as part of
  the real Claude Code transcript format, and `_to_agentson` correctly
  sets `outcome = "success"` only when it encounters one. The synthetic
  test fixture never included a summary entry, so `outcome` stayed at its
  `"partial"` default — the fixture didn't match the format it claimed to
  model. Added the missing `type: "summary"` entry to the fixture,
  matching the documented schema; no reader code changed.

### Known issues (flagged, not yet fixed)

Findings below are from a structured audit on 2026-07-07, confirmed by
reproduction against the real repo (not assumed from reading). Repair
path is tracked as work packets WP1–WP5; ADR-015/016/017 pending.

- **`spec/v1.2.json` enforces nothing.** Its top-level `required` array is
  empty and no `oneOf`/`anyOf` discriminates per-line event types, so an
  empty object `{}` validates successfully. The per-primitive required
  fields documented in `spec/ontology.md` (e.g. `stream-meta` →
  `stream_id`, `agents[]`) are not encoded in the schema. Reproduced via
  jsonschema Draft 2020-12 validation. (WP2)

- **`spec/ontology.md` contradicts the v1/v1.1 entry-type enum.** The
  ontology declares "exactly 12 primitives," but `context`, `querying`,
  and `title` exist in the v1 enum and not in the ontology, while
  `handoff`, `presence`, `capabilities`, `user-feedback`, `system-event`,
  `stream-meta`, and `observation` exist in the ontology and not in the
  v1 enum. ADR-014 covers only the `observation` case; the full
  reconciliation needs ADR-016. (WP1/WP2)

- **No `agentson validate` CLI command exists**, despite validation being
  a named core capability. Validation is currently only possible by
  calling jsonschema directly. (WP3)

- **Dependency declaration is inverted.** `pyproject.toml` declares only
  `requests` (which serves `push`/`pull` — flagged as core scope
  violations in ADR-013), while `jsonschema` — the single dependency core
  is supposed to have — is neither declared nor imported anywhere in the
  package. (WP3 / ADR-013)

- **`cmd_search` is defined twice in `cli/main.py`** (approx. lines 259
  and 423); the later definition silently shadows the earlier one. The
  surviving behavior is pinned by a Gherkin scenario so removal of the
  dead definition can be verified as behavior-neutral. (WP3)

- **No document states which schema version is canonical.** v1 and v1.1
  both require `id`/`tool`/`entries`; example files reference v1.1;
  `spec/adapter-spec.md` calls the v1.2 JSONL stream "canonical";
  ADR-001's framing is single-document. Four of ten shipped examples are
  JSONL streams, six are single documents. Resolution needs ADR-015. (WP1)

- **The v1.2 layer (ontology, adapter-spec, replay-semantics, JSONL
  streaming, handoff/presence/capabilities) landed without any ADR**,
  bypassing the project's own decision framework. `presence` and live-
  channel semantics additionally appear to fail the spec litmus test
  (coordination infrastructure rather than captured-episode fidelity);
  decision needed in ADR-017. (WP1)

- `readers/claude_code.py` uses the deprecated `datetime.datetime.utcnow()`
  (surfaced as a `DeprecationWarning` during test runs). Low priority,
  not user-facing, left open as a separate cleanup item.

### Added (unreleased, in progress)

- Gherkin/BDD regression suite scaffold under `tests/features/`: 71
  scenarios across 13 feature files in 7 taxonomy folders
  (spec_validation, importers, readers, cli, provenance, constants,
  quarantine_scope_violations). Status honestly stated: 1 of 13 families
  has executable step definitions and has been run (spec_validation:
  4 pass / 6 fail, all failures traced to the schema-version issues
  above, not to reader/CLI code). Remaining families are scenarios only,
  pending WP2/WP3 decisions. The quarantine folder pins current
  `finetune`/`push`/`pull` behavior solely so their extraction per
  ADR-013 can be verified as behavior-preserving.

## [0.1.1] - 2026-07-05

Patch release. Fixes bugs present in v0.1.0 that were claimed working but weren't.

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
