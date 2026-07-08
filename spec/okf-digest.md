# OKF Reference (Compressed — No Webfetch Needed)

**Source:** GoogleCloudPlatform/knowledge-catalog, Apache 2.0, v0.1 (June 2026)
**Spec:** 451 lines, `okf/SPEC.md`
**Repo:** https://github.com/GoogleCloudPlatform/knowledge-catalog

---

## What OKF Is

Open Knowledge Format — a vendor-neutral, agent- and human-friendly format for representing knowledge as a directory of markdown files with YAML frontmatter. Formalizes the Karpathy LLM wiki pattern into an interoperable spec.

## Structure

```
bundle/
├── index.md              # Entry point (okf_version: "0.1")
├── datasets/
│   ├── index.md          # Directory entry
│   └── my_table.md       # Concept: BigQuery Dataset
├── tables/
│   └── orders.md         # Concept: BigQuery Table
└── references/
    └── joins/
        └── a_b.md        # Concept: Reference (cross-link)
```

## Required Fields (v0.1)

| Field | Required | Purpose |
|-------|----------|---------|
| `type` | **YES** | What kind of thing (`BigQuery Table`, `Metric`, `Playbook`, etc.) |
| `title` | No | Display name; derive from filename if absent |
| `description` | No | One-line summary for indexes/search |
| `resource` | No | Canonical URI for underlying asset |
| `tags` | No | Cross-cutting YAML list |
| `timestamp` | No | ISO 8601 last-modified |
| (extra keys) | No | Producers may add; consumers must preserve |

## Reserved Files

- `index.md` — directory entry point, progressive disclosure, frontmatter only in root
- `log.md` — chronological change history, newest first

## Conformance Rules

A bundle conforms to OKF v0.1 if:
1. Every non-reserved `.md` file contains parseable YAML frontmatter
2. Every frontmatter block contains a non-empty `type` field
3. Reserved filenames follow their structure when present

**Consumers MUST NOT reject** bundles for:
- Missing optional fields
- Unknown types
- Extra frontmatter keys
- Broken cross-links
- Absent `index.md`

## Cross-Linking

```markdown
See [orders table](/tables/orders.md) for details.
```

- Links are standard markdown
- Bundle-relative paths (start with `/`) preferred
- Link semantics conveyed by prose, not by link type
- Edges = graph relationships

## Graph Structure

- File path without `.md` = concept ID (`tables/orders` → ID `tables/orders`)
- Directory structure = organizational hierarchy
- Markdown links = directed graph edges
- Result: a tree + a graph, simultaneously

## Visualizer Design System

- Cytoscape.js 3.28.1 (force-directed graph)
- Node coloring: `BigQuery Dataset:#8b5cf6`, `BigQuery Table:#3b82f6`, `Reference:#10b981`, default `#94a3b8`
- Node size: `30 + min(60, len(body)//200)`
- Colors: text `#0f172a`, background `#f8fafc`, border `#e2e8f0`
- `marked.js` 12.0 for markdown rendering
- Backlinks computed from edge list at load time
- Layout: cose (force), concentric, breadthfirst, circle, grid
- Search: dims non-matching nodes (opacity: 0.15)
- Detail panel: frontmatter grid, markdown body, backlinks section

## Agent Tools

- **Consumer:** `readers/reader.py` — walks .md files, extracts YAML frontmatter + markdown body
- **Producer:** `writers/writer.py` — creates .md files with YAML frontmatter from structured data
- **Enrichment:** `agent/agent.py` — walks BigQuery datasets, drafts OKF concept docs, web-enriches with LLM
- **Visualizer:** `viewer/generator.py` — pyvis-based HTML graph from OKF bundle

## Relationship to AgentSON

| Dimension | OKF | AgentSON |
|-----------|-----|----------|
| What it captures | Knowledge (what the agent *learned*) | Execution (what the agent *did*) |
| Time shape | Static wiki (last-known truth) | Trace log (temporal sequence) |
| Required fields | `type` only | `type`, `timestamp` |
| Links | Markdown links → graph edges | `parent_session_id` → tree |
| Format | Directory of .md + YAML frontmatter | NDJSON stream of typed entries |
| Stack position | Knowledge layer (below MCP) | Execution memory (above MCP) |

## Bridge Strategy

- `okf_adapter.py` — reads OKF bundles, converts to AgentSON-compatible structures
- `okf_export.py` — writes OKF concept docs from AgentSON session traces
- AgentSON = provenance layer for OKF knowledge ("which session wrote this?")

## Karpathy Origin

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."
> — Andrej Karpathy, LLM Wiki gist (5,000+ stars, April 2026)

OKF formalizes the markdown+frontmatter+links shape that Karpathy's LLM wiki pattern popularized.
