# AgentSON Architecture Skill

**Purpose:** Reference document for AgentSON design decisions, architectural patterns, and critical path planning. Based on deep analysis of Claude conversations, ADRs, and codebase findings.

**Last Updated:** 2026-07-07

---

## Core Identity

**What AgentSON Is:**
- A portable, vendor-neutral JSON-based agent session recording format
- The "OSI layer for AI experience" — a trace-interchange standard
- Solves provenance and reproducibility, NOT live multi-agent consensus
- A trace standard that is a *precondition* for shared reality, not shared reality itself

**What AgentSON Is NOT:**
- A live coordination substrate (like OSPF for routers)
- A semantic bus with reconciliation
- A shared mutable store for real-time agent consensus
- A replay engine (replay-semantics.md is spec, not implementation)

---

## Critical Architecture Findings

### 1. The Format Split (MUST RESOLVE)

Two incompatible `.agentson` shapes coexist:

| Shape | Format | Schema | Used By |
|-------|--------|--------|---------|
| **Single-JSON-document** | One JSON object with `id`, `tool`, `entries[]` | v1.json, v1.1.json | 6 of 10 examples |
| **NDJSON/JSONL stream** | Line-delimited events, each with `type` | v1.2.json | 4 of 10 examples |

**Resolution Required:** ADR-015 must decide which is canonical.

### 2. Schema Enforcement Gap

- `v1.2.json` has `required: []` — validates ANYTHING including `{}`
- The 12-primitive ontology specifies required fields per type, but schema doesn't enforce them
- A schema that can't fail is worthless for a format whose pitch is "validate"

### 3. Ontology ↔ Enum Contradiction

| v1.json enum has | ontology.md has |
|------------------|-----------------|
| `context`, `querying`, `title` | NOT in 12 primitives |
| NOT in enum | `handoff`, `presence`, `capabilities`, `observation`, `stream-meta`, `user-feedback`, `system-event` |

**7 types divergent in one direction, 3 in the other.**

### 4. Dependency Inversion

- `pyproject.toml` declares `requests` (serves push/pull — ADR-013 violations)
- `jsonschema` (core's actual minimal dep) is NOT declared or imported
- No `agentson validate` command exists despite being in scope definition

---

## Critical Path & Work Packets

### Dependency Graph
```
WP1 (Decisions) → WP2 (Schema) ─┐
                                ├→ WP4 (Tests)
WP1 (Decisions) → WP3 (Core)  ─┘
                                
WP5 (Docs) runs parallel to WP2/WP3/WP4
```

### Work Packet Details

| WP | Description | Effort | Dependencies |
|----|-------------|--------|--------------|
| **WP1** | 3 ADRs: canonical schema (015), ontology↔enum (016), presence strip (017) | 1-2h (your judgment time) | None |
| **WP2** | Schema repair: real `required`, `oneOf` discriminated on `type`, fix examples | 2-4h | WP1 |
| **WP3** | Core alignment: add jsonschema, build `agentson validate`, extract push/pull | 3-5h | WP1 |
| **WP4** | Test suite: finish ~60 step defs, backward-compat family, wire pytest-bdd | 4-6h | WP2 + WP3 |
| **WP5** | Docs sync: README/PRD/adapter-spec/ontology consistency | 1-2h | WP1 |

### Critical Path Calculation
- **Aggressive:** WP1 (1h) → max(WP2, WP3) (3-5h) → WP4 (4-6h) = **8-13h**
- **With Buffer (30-50%):** **11-18h** total
- **WP5 floats alongside, non-blocking**

### 80/20 Rule Application

| Priority | WPs | Value Delivered |
|----------|-----|-----------------|
| **Must Have** | WP1 + WP3 core | Launch survives serious code review |
| **Should Have** | WP2 full + WP3 extraction + partial Gherkin | Correctness, no embarrassment |
| **Could Have** | WP4 full + WP5 docs | Regression confidence, polish |
| **Won't Have** | Replay engine, live-coordination | Explicitly deferred |

---

## MoSCoW Prioritization (Validated)

### Must Have (Launch Indefensible Without)
- WP1 decisions: ADR-015/016/017
- `jsonschema` as real dependency
- `agentson validate` command existing
- v1.2 schema actually enforcing something (required fields, discriminated oneOf)

### Should Have (Real Cost to Skip)
- Full enum reconciliation across all examples
- finetune/push/pull extraction out of core (ADR-013)
- spec_validation Gherkin family (honestly labeled partial)

### Could Have (Defer Without Real Risk)
- Remaining ~60 step definitions
- pytest-bdd + Pyrefly coverage floor wired into CI
- WP5 docs sync across README/PRD/adapter-spec

### Won't Have This Time
- A replay engine (replay-semantics.md stays spec doc)
- Any live-coordination/presence tooling

---

## Litmus Tests (Still Valid)

### Test 1: Spec Scope
> Does this improve fidelity/portability/replayability/analyzability of a *captured episode*?

### Test 2: Core vs Downstream
> Is this *defining* AgentSON or *using* AgentSON?

### Test 3: Definition of Done (ADD THIS)
> A spec change doesn't exist until it has:
> 1. An ADR applying the litmus test
> 2. A schema that actually enforces it
> 3. At least one scenario validating a real example against it

---

## Shared Reality Clarification

**What AgentSON Actually Solves:**
- Provenance and reproducibility — portable, vendor-neutral record
- Any tool can reconstruct exactly what an agent session did
- Prerequisite for future coordination work

**What AgentSON Does NOT Solve:**
- Live multi-agent consensus (needs shared, mutable, real-time state exchange)
- Coordination infrastructure (presence, live channels)
- Reconciliation between concurrent agents

**Legitimate Forward Path:**
- `agentson-archive` for multi-session lifecycle management
- S3-style tiering: Standard → Infrequent Access → Glacier
- Access-frequency-based demotion (LRU/Chrome tab discarding pattern)
- Foundation time series models (Chronos-2, Moirai-2) for zero-shot forecasting

---

## Theo's Workflow Patterns (Reference)

### Model Routing Strategy
| Model | Use Case | Cost | Intelligence | Taste |
|-------|----------|------|--------------|-------|
| **Fable 5** | Steering, complex tasks | High | Best-in-class | Best-in-class |
| **GPT-5.5** | Bulk mechanical work | Low (effectively free) | High | Low |
| **Opus 48** | API/SDK review | Medium | High | High |
| **Sonnet 5** | Cheap sub-agents | Low | Medium | Medium |

### Key Practices
1. **Reasoning Effort:** Keep on `high` (not `x-high`, `max`, or `ultra`)
2. **Skills System:** Codex review, Codex implementation, computer use
3. **Goal-Based Loops:** Explicit conditions, permission to merge, time-boxed
4. **Parallelization:** Work trees, workflows for fan-out + verify
5. **Vibe Proxy:** Auto-split traffic across accounts

### What AgentSON Would Solve for Theo
- **Audit trail:** All those goal-run sessions have no portable record
- **Replay:** Can't reconstruct what happened across 5.5-hour runs
- **Cross-session lineage:** parent_session_id/branched_from_entry not captured
- **Review evidence:** 14/16-unanimous review panel result exists only in chat

---

## Gherkin Test Suite Status

**Current:** 71 scenarios across 13 feature files (draft, not executed)
**Executed:** 4 pass / 6 fail (schema-version issues, not step bugs)

### Scenario Taxonomy
```
tests/features/
├── 00-schema-validation/      # v1.json, v1.1.json, v1.2.json
├── 10-import-formats/         # chatgpt, cursor, opencode, claude
├── 20-readers/                # per-tool reader implementations
├── 30-cli-commands/           # export, import, list, search, render
├── 40-extension-casing/       # .agentson, .ason naming
├── 50-provenance/             # parent_session_id, branched_from_entry
├── 60-cross-cutting/          # exit codes, error handling
├── 70-streaming/              # v1.2 JSONL format
└── 90-quarantined/            # finetune/push/pull (ADR-013 violations)
```

---

## Open Questions for Resolution

1. **Which shape is canonical?** Single-document (v1/v1.1) or NDJSON stream (v1.2)?
2. **Which schema version?** v1.json, v1.1.json, or v1.2.json?
3. **Fate of `context`/`querying`/`title`?** Deprecated or promoted into the 12?
4. **Fate of `presence`/live-channel?** Strip to future extensions note?
5. **When to build `agentson validate`?** Before or after schema repair?

---

## Next Actions (If Continuing)

### Immediate (WP1)
- [ ] Draft ADR-015: canonical schema story
- [ ] Draft ADR-016: ontology↔enum reconciliation
- [ ] Draft ADR-017: strip or justify presence/live-channel

### After WP1 Decisions
- [ ] WP2: Repair v1.2 schema enforcement
- [ ] WP3: Add jsonschema dep, build `agentson validate`
- [ ] WP4: Finish Gherkin step definitions
- [ ] WP5: Sync documentation

---

## OKF Digest (Compressed — No Webfetch Needed)

### What OKF Is
Open Knowledge Format v0.1 — Google Cloud's vendor-neutral spec (June 2026) for representing knowledge as a directory of markdown files with YAML frontmatter. 451 lines. Apache 2.0. No SDK required.

### OKF Structure
```
bundle/
├── index.md          # Entry point, frontmatter: okf_version: "0.1"
├── datasets/
│   └── my_table.md   # Concept doc
├── references/
│   └── joins/
│       └── a_b.md    # Cross-links via markdown links
```

### Required Fields (v0.1)
| Field | Required | Purpose |
|-------|----------|---------|
| `type` | YES | What kind of thing (e.g. `BigQuery Table`, `Metric`, `Playbook`) |
| `title` | No | Display name; derive from filename if absent |
| `description` | No | One-line summary for indexes/search |
| `resource` | No | Canonical URI for underlying asset |
| `tags` | No | Cross-cutting YAML list |
| `timestamp` | No | ISO 8601 last-modified |

### Reserved Files
- `index.md` — directory entry point, progressive disclosure
- `log.md` — chronological change history

### Key Design Decisions
- **Markdown links = graph edges.** `](/tables/orders.md)` → directed relationship.
- **Consumers MUST NOT reject** bundles for: missing optional fields, unknown types, extra frontmatter, broken links, absent index.md.
- **File path = concept ID.** `tables/orders.md` → ID is `tables/orders`.
- **Conformance**: parseable YAML frontmatter + non-empty `type` in every non-reserved .md file. That's it.

### OKF vs AgentSON (Complementary, Not Competitive)
| Dimension | OKF | AgentSON |
|-----------|-----|----------|
| What it captures | Knowledge (what the agent *learned*) | Execution (what the agent *did*) |
| Time shape | Static wiki (last-known truth) | Trace log (temporal sequence) |
| Required fields | `type` only | `type`, `timestamp` |
| Links | Markdown links → graph edges | `parent_session_id`, `correlation_id` → tree |
| Format | Directory of .md + YAML frontmatter | NDJSON stream of typed entries |
| Runtime | None (files) | None (JSONL) |
| Stack position | Knowledge layer (below MCP) | Execution memory + provenance layer (above MCP) |

### OKF Relationship to AgentSON
- OKF is the **knowledge** output: what the agent learned, packaged as a wiki
- AgentSON is the **execution** trace: what the agent did, packaged as a log
- **AgentSON provides provenance for OKF knowledge.** "Where did this concept doc come from? Which agent session wrote it?"
- **Bridge**: `okf_adapter.py` reads OKF bundles, `okf_export.py` writes OKF from .agentson traces

### Google's OKF Visualizer Design System
- Cytoscape.js 3.28.1 (force-directed graph)
- Node coloring by type: `BigQuery Dataset:#8b5cf6`, `BigQuery Table:#3b82f6`, `Reference:#10b981`
- Node size: `30 + min(60, len(body)//200)`
- Dark sidebar, light graph, `#0f172a` text, `#f8fafc` background
- `marked.js` for markdown rendering in detail panel
- Backlinks computed from edge list at load time
- Layout options: cose (force), concentric, breadthfirst, circle, grid
- Search dims non-matching nodes (opacity: 0.15)
- Auto-shows first BigQuery Dataset node

### First-Mover Strategy
- Don't compete with OKF. Be the bridge.
- AgentSON = "OpenTelemetry for MCP agents" — observability layer
- OKF = knowledge packaging format — wiki layer
- Build `okf_adapter.py` and `okf_export.py`
- Position as: "AgentSON provides provenance for OKF knowledge"

### Key Insight (from Karpathy)
Humans abandon wikis because the bookkeeping is tedious. LLMs don't get bored, don't forget cross-references, can touch 15 files in one pass. OKF formalizes the markdown+frontmatter+links shape that Karpathy's LLM wiki pattern popularized (5,000+ stars, 16M views on X).

---

## Key Quotes (Preserve These)

> "A trace/provenance standard is a *precondition* for shared reality, not shared reality itself — you can't build agent consensus on top of state nobody can verify or replay."

> "A schema that validates `{}` passes both litmus tests trivially — the tests judge what a schema *covers*, not whether it *enforces*."

> "A spec change doesn't exist until it has (1) an ADR applying the litmus test, (2) a schema that actually enforces it, and (3) at least one scenario validating a real example against it."

> "The v1.2 layer landed with no ADR at all. Your decision framework says the spec evolves only through the litmus test; the biggest spec change in the project's history bypassed the framework entirely."

---

## Reference Files (Actual State)

**EXISTS LOCALLY:**
- `spec/v1.json` — Single-document schema
- `spec/v1.1.json` — Single-document schema (dogfood example uses this)
- `spec/v1.2.json` — JSONL stream schema (requires nothing!)
- `wiki/ADRs.md` — Architecture Decision Records (001-011 only)

**DOES NOT EXIST LOCALLY (referenced in Claude conversations):**
- `spec/ontology.md` — 12-primitive formal ontology (NOT FOUND)
- `spec/adapter-spec.md` — CDP/MCP/browser-use/extension mappings (NOT FOUND)
- `spec/replay-semantics.md` — Stream interpretation rules (NOT FOUND)
- `tests/features/` — Gherkin test suite (NOT FOUND)

**CRITICAL GAPS CONFIRMED:**
- No `agentson validate` command in CLI
- No `jsonschema` import or usage in core code
- ADRs only go up to 011 (no 012-017)
- No ontology.md, adapter-spec.md, or replay-semantics.md files

---

## Visualizer Rebuild Process (OKF Design System)

### When to Use
When rebuilding any HTML visualizer (heartbeat, knowledge graph, trace viewer) using the Google OKF design system.

### Design System Reference (from Google OKF Visualizer)

**CSS Patterns:**
```css
/* Layout: flex column, 100vh */
body { margin: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif; font-size: 14px; color: #0f172a; background: #f8fafc; display: flex; flex-direction: column; height: 100vh; }

/* Header: flex row, space-between */
header { display: flex; align-items: center; justify-content: space-between; padding: 10px 16px; background: #fff; border-bottom: 1px solid #e2e8f0; }

/* Split panel: graph 60%, detail 40% */
main { display: flex; flex: 1; min-height: 0; }
#graph { flex: 1 1 60%; border-right: 1px solid #e2e8f0; }
#detail { flex: 0 0 40%; overflow-y: auto; padding: 18px 22px; }

/* Type chip: pill badge */
.type-chip { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 11px; font-weight: 600; color: #fff; text-transform: uppercase; }

/* Frontmatter grid: 2-column */
dl.frontmatter { display: grid; grid-template-columns: 90px 1fr; row-gap: 4px; column-gap: 12px; }

/* Node coloring by type */
BigQuery Dataset: #8b5cf6 (purple)
BigQuery Table: #3b82f6 (blue)
Reference: #10b981 (green)
Default: #94a3b8 (gray)

/* Node size formula */
width/height: 30 + min(60, len(body)//200)

/* Dimming for search */
.dim { opacity: 0.15 }
```

**JS Patterns:**
```javascript
// Cytoscape.js initialization
const cy = cytoscape({ container: document.getElementById("graph"), elements: [...nodes, ...edges], style: [...], layout: { name: "cose", animate: false, padding: 30 } });

// Search: dim non-matching
cy.nodes().forEach(n => n.toggleClass("dim", !hay.includes(q)));

// Detail panel: show on tap
cy.on("tap", "node", evt => showDetail(evt.target.id()));

// Backlinks: computed from edge list
const backlinks = {};
for (const edge of bundle.edges) { (backlinks[edge.data.target] ||= []).push(edge.data.source); }
```

### Step-by-Step Rebuild Process

1. **Document BEFORE state** — Save current version as `*-BEFORE.html` with comment header
2. **Study reference design** — Read Google OKF viz CSS/JS patterns above
3. **Build new version** — Use same CDN (Cytoscape.js 3.28.1), same color palette, same layout
4. **Test in browser** — Open in Edge, verify all interactions work
5. **Update changelog** — Document BEFORE/AFTER comparison

### Changelog Format

```markdown
## [version] - YYYY-MM-DD

### Changed
- Rebuilt heartbeat visualizer using OKF design system (Cytoscape.js)
- BEFORE: 43 lines, basic terminal-style, dark background, monospace
- AFTER: 300+ lines, interactive graph, split panel, search, type filter

### Added
- Knowledge graph visualization (session → entry nodes)
- Health filter (healthy/idle/stale/dead)
- Detail panel with frontmatter grid, sparkline, timeline
- Layout picker (force, concentric, breadthfirst, circle, grid)
```

---

## Compressed Documentation Index Process

### When to Use
When creating an agent-readable index of a codebase that fits in ~8KB.

### The Vercel Approach
Vercel compressed their entire docs into an 8KB markdown index with file paths + one-line descriptions. The agent reads the index, knows what exists, and only fetches specific files when needed.

### Step-by-Step Process

1. **Inventory all files** — Use glob to find everything
2. **Categorize** — Group by type (core, readers, exporters, tools, tests, docs)
3. **One-line descriptions** — Each file gets exactly one line
4. **Key concepts section** — Summarize the most important architectural decisions
5. **External references** — URLs, paths, connection details
6. **Session statistics** — Current state of the project

### Target Size
- 8KB = 8,192 bytes
- 150-200 lines
- Every file in the codebase mentioned at least once

### File Location
- `AGENT_INDEX.md` — compressed index
- Referenced from skill.md and AGENTS.md

---

## Scope Creep Tracking

### What Counts as Scope Creep
Any work NOT in the original spec/PRD that gets built during development.

### Current Scope Creep Inventory

| Item | Lines | Purpose | Justification |
|------|-------|---------|---------------|
| heart_monitor.py | 416 | Agent health dashboard | Needed for heartbeat field in spec |
| session_timing.py | 541 | Burst/idle analysis | R&D for time-series prediction |
| live_heartbeat.py | 170 | Terminal heartbeat display | Dogfooding tool |
| okf-digest.md | 118 | OKF compressed reference | Avoids webfetch |
| STRATEGY-WHITEPAPER.md | 460 | Strategy document | Vision articulation |
| PAPER-OUTLINE.md | 477 | Academic paper outline | Publication target |
| ANTIREZ-LINEAGE.md | 223 | Intellectual lineage | Context for spec decisions |
| PLAN-chrome-devtools-mcp-integration.md | 68 | Integration plan | PR #30 |
| agentson-architect.md | 335 | Skill reference | Prevents repetition |

**Total scope creep: 2,408 lines**

### Prevention Rule
Before building anything unplanned, ask:
1. Does this improve fidelity/portability/replayability/analyzability of a captured episode?
2. Is this defining or using AgentSON?
3. Can this be done in <2 hours?
4. Does this block the critical path (WP1→WP2/WP3→WP4)?

If answer to #1 is NO, don't build it.
