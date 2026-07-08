# AgentSON — Maximum Entropy Index

> **STOP. What you remember about AgentSON is WRONG for this project. Always search docs and read before any task.**
> **Prefer retrieval-led reasoning over pre-training-led reasoning.**
> **If docs missing, run: agentson export opencode --all**

## Model Routing

| Model | Use Case | Intelligence | Taste | Cost |
|-------|----------|-------------|-------|------|
| **Fable 5** | Steering, complex tasks, reviews | 10 | 10 | High |
| **GPT-5.5** | Bulk mechanical work, data analysis | 8 | 4 | Free (CodeX sub) |
| **Opus 48** | API/SDK review, second-pass review | 8 | 8 | Medium |
| **Sonnet 5** | Cheap sub-agents, workflows | 6 | 6 | Low |

**Defaults:** Keep reasoning effort on `high`. Do NOT use `x-high`, `max`, or `ultra` — they overthink and cost more for worse results.

**Routing rules:**
- Anything user-facing (UI, copy, API design) → taste > 7 required
- Reviews → Fable or Opus 48 (optionally 55 for extra perspective)
- Bulk mechanical work (migrations, data analysis) → 55 (effectively free)
- Computer use → shell out to GPT-55 via CodeX

**Cost is a tiebreaker only when axes conflict.** Intelligence > Taste > Cost. Don't let cost prevent using the right model.

## Skills

### Codex Review
Ask Codex CLI (GPT-55) for independent code review of uncommitted changes, a branch diff, or a specific implementation.
- **When:** User wants a second-pass review, or change is broad enough for another perspective
- **Workflow:** Identify review target → create temp artifact dir → run Codex review → read report → verify claims against code → present
- **Commands:** `codex "review this diff: $(git diff)"` or `codex "review branch: $(git log main..HEAD --oneline)"`
- **If Codex finds nothing:** Say that clearly, mention what was inspected

### Codex Implementation
Run Codex (GPT-55) for bounded work on a work tree.
- **When:** Task is mechanical, well-scoped, or needs GPT-55's pattern matching
- **Workflow:** Define scope → spawn work tree → run Codex → verify output → merge
- **Commands:** `codex "implement this spec: <spec>"`
- **Time heuristic:** <3 min = simple, merge. 15+ min = pay attention. 1+ hour = architecture problem.

### Computer Use
Ask Codex CLI (GPT-55) for local app verification needing computer use, browser automation, screenshots, or runtime inspection.
- **When:** User asks to test a flow, verify UI behavior, inspect running app, capture screenshots
- **Commands:** `codex --computer "verify <flow> in <app>"`
- **Note:** GPT-55's computer use is better than Claude's. Always delegate.

## Schema Status (Critical)

| Schema | Required Fields | Validates | Verdict |
|--------|----------------|-----------|---------|
| `spec/v1.json` | Per-primitive from ontology | Single-document shape | ✅ Authoritative |
| `spec/v1.1.json` | Per-primitive + trajectory | Single-document + trajectory | ✅ Working |
| `spec/v1.2.json` | Per-primitive + oneOf discriminated union | JSONL stream (canonical) | ✅ Accepted (ADR-015) |

**v1.2 is canonical.** ADR-015 accepted. JSONL is the only format. v1/v1.1 deprecated.

## Ontology ↔ Enum Reconciliation

ADR-016 accepted. The 12 primitives are the source of truth. The schema enum matches exactly.

| Removed (demoted to metadata) | Added (new primitives) |
|-------------------------------|------------------------|
| `context` → session metadata | `observation` |
| `querying` → `thought` subtype | `user-feedback` |
| `title` → display metadata | `system-event` |
| | `capabilities` |

## Dependency Graph

```
WP1 (ADR-015/016/017) ✅ ──→ WP2 (Schema: real required + oneOf) ✅
                         ──→ WP3 (Core: jsonschema + validate cmd) ✅
                         ──→ WP4 (Tests: 70 step defs) ✅
                         ──→ WP5 (Docs sync) — IN PROGRESS
```

**All critical path items DONE** (2026-07-08). WP5 in progress.

## Platform Context

A separate managed service (Data Rights Intelligence Platform) is defined in ADR-018–021 and spec'd in `docs/platform/mvp-spec.md`. It sits architecturally above AgentSON but does not impact the core format, CLI, or readers.

```
AgentSON (open source)              Platform (managed service)
  ├── CLI (export/search/render)       ├── Crawler (wraps agentson export)
  ├── Readers (7 working)              ├── Analyst (LLM truth-teller)
  ├── Schema (v1.2 canonical)          ├── Enforcer (opt-out injection)
  └── Apache 2.0                       └── Supabase + billing
```

Revenue from the platform funds AgentSON development. Both can exist without the other.

**Sprint 1 BUILT (2026-07-08):** Crawl → Classify → Report loop working end-to-end.
- `agentson platform detect` — lists installed AI tools + data paths
- `agentson platform scan` — detects tools, exports all sessions, classifies, writes Markdown + JSON report
- 62 sessions from 3 tools (opencode/minimax/antigravity) analyzed, 111 concerns found, 50 high/critical
- Tier 1 rule-based classifier: detects API keys, emails, phones, file paths, telemetry signals, URLs
- SLM classifier stub with graceful fallback to rules

## File Map (Vercel Compressed Index)

| Path | Purpose | Status |
|------|---------|--------|
| `spec/v1.json` | Schema v1 | ✅ Deprecated |
| `spec/v1.1.json` | Schema v1.1 | ✅ Deprecated |
| `spec/v1.2.json` | Schema v1.2 (canonical) | ✅ Accepted |
| `spec/v1.2-entries.json` | Flattened entry schema | ✅ CLI-ready |
| `spec/ontology.md` | 12 primitives | ✅ Source of truth |
| `spec/adapter-spec.md` | CDP/MCP/browser-use specs | ✅ |
| `spec/replay-semantics.md` | Replay rules | ✅ |
| `spec/okf-digest.md` | OKF reference | ✅ |
| `spec/ADR-015-canonical-schema.md` | JSONL is canonical | ✅ Accepted |
| `spec/ADR-016-ontology-enum-reconciliation.md` | 12 primitives = source of truth | ✅ Accepted |
| `spec/ADR-017-core-vs-streaming.md` | Core vs streaming separation | ✅ Accepted |
| `docs/standards/adrs/adr-018-managed-service-architecture.md` | Platform separation from core AgentSON | ✅ Accepted 2026-07-08 |
| `docs/standards/adrs/adr-019-llm-analysis-privacy-model.md` | Three-tier LLM privacy model | ✅ Accepted 2026-07-08 |
| `docs/standards/adrs/adr-020-data-rights-enforcement.md` | Opt-out injection scope & legal boundary | ✅ Accepted 2026-07-08 |
| `docs/standards/adrs/adr-021-business-model-self-sustainability.md` | Tiered pricing & self-sustainability | ✅ Accepted 2026-07-08 |
| `docs/platform/mvp-spec.md` | MVP architecture: Crawler→Analyze→Report→Enforce | ✅ Spec complete |
| `readers/opencode.py` | OpenCode reader | ✅ |
| `readers/claude_code.py` | Claude Code reader | ✅ |
| `readers/chrome_devtools.py` | Chrome DevTools reader | ✅ |
| `cli/main.py` | CLI (13 commands: +reconstruct, +platform) | ✅ |
| `cli/compliance.py` | GDPR/EU AI Act compliance engine (dual-track EU/UK) | ✅ Resolved 2026-07-08 |
| `cli/reconstruct.py` | Three-mode reconstructor (forensic/narrative/live) | ✅ Resolved 2026-07-08 |
| `agentson_platform/tool_registry.py` | Tool path registry (8 tools, cross-platform) | ✅ Sprint 1 |
| `agentson_platform/crawler.py` | Auto-detect + export all sessions from all tools | ✅ Sprint 1 |
| `agentson_platform/digest.py` | ComplianceDigest schema (dataclass) | ✅ Sprint 1 |
| `agentson_platform/classifier.py` | Tier 1 rule-based classifier (PII + telemetry) | ✅ Sprint 1 |
| `agentson_platform/classifier_slm.py` | SLM-enhanced classifier (graceful fallback) | ✅ Sprint 1 |
| `agentson_platform/report.py` | Markdown + JSON report renderer | ✅ Sprint 1 |
| `agentson_platform/scan.py` | End-to-end Crawl→Analyze→Report entry point | ✅ Sprint 1 |
| `tests/test_schema.py` | 70 schema validation tests | ✅ |
| `tools/flatten_schema.py` | Generates v1.2-entries.json | ✅ |
| `tools/heart_monitor.py` | Health dashboard | ✅ |
| `tools/session_timing.py` | Burst/idle analysis | ✅ |
| `tools/pii_redactor.py` | PII detection | ✅ |
| `exporters/excel.py` | Excel export | ✅ |
| `exporters/pdf_export.py` | PDF export | ✅ |

## Concept Map

```
OKF (knowledge)          AgentSON (provenance)
├── What agent LEARNED   ├── What agent DID
├── Static wiki          ├── Temporal trace
├── markdown + YAML      ├── JSONL stream
└── Below MCP            └── Above MCP

Stack: L0 Identity → L1 Execution → L2 Knowledge → L3 Display
```

## Critical Gaps

1. ~~**No `agentson validate` command**~~ — ✅ Implemented (WP3)
2. ~~**No `jsonschema` in pyproject.toml**~~ — ✅ Added
3. ~~**`requests` serves push/pull**~~ — ✅ Removed (ADR-013)
4. ~~**No ADR-015/016/017**~~ — ✅ Accepted (2026-07-08)
5. ~~**GDPR compliance model unimplemented**~~ — ✅ Resolved (`cli/compliance.py` + `cli/reconstruct.py` + schema v1.2 updated)
6. **CHANGELOG.md stale** — needs v0.2.1 entry
7. ~~**chrome-devtools not in CLI export/list**~~ — ✅ In CLI export (already had handler in cmd_export)
8. ~~**Data Rights Platform not built**~~ — ✅ Sprint 1 BUILT (`agentson_platform/` — Crawl→Classify→Report working)
9. **claude-code reader wired into CLI** — ✅ Added to export + list commands (Sprint 1)
10. **Sprint 2** — Supabase backend + web dashboard + auth + Stripe (not started)
11. **Sprint 3** — LLM Tier 3 analysis + injection engine (not started)

## Session Context

- SQLite DB: `~/.local/share/opencode/opencode.db` (137 sessions, 10,861 messages)
- Current session: 25+ hours, 177 steps, 0.1 bpm heart rate, 0.1% activity ratio
- Chrome Dev CDP: port 9222 (Chrome Dev only, Stable broken)
- Edge CDP: port 9226 (with `--user-data-dir=%TEMP%\edge_cdp_demo`)
- MiKTeX: `C:\Users\LLM-Test\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdflatex.exe`
- mcp-use venv: `mcp_env/Scripts/python`
- **Package naming:** `agentson_platform/` not `platform/` — `platform` shadows Python stdlib and breaks `attrs`/`jsonschema`

## Evolution Rule

When something goes wrong or a solution works:
1. Diagnose the root cause
2. Fix it
3. Add the solution to THIS FILE so the next agent doesn't repeat the mistake
4. Keep this file as the living knowledge base — every problem solved becomes permanent knowledge

**This file is not static. It evolves with every session.**
