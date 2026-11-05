# Architecture Decision Records (ADRs)

ADRs capture significant architectural decisions with context and rationale.

---

## ADR Index

| # | Title | Date | Status |
|---|-------|------|--------|
| 001 | [AgentSON Format](ADR-001) | 2026-07-05 | Accepted |
| 002 | [JSON over SQLite](ADR-002) | 2026-07-05 | Accepted |
| 003 | [Vendor Neutral](ADR-003) | 2026-07-05 | Accepted |
| 004 | [Amber Design Tokens](ADR-004) | 2026-07-05 | Accepted |
| 005 | [Nightscout Integration](ADR-005) | 2026-07-05 | Accepted |
| 006 | [GitHub Pages](ADR-006) | 2026-07-05 | Accepted |
| 007 | [CodeRabbit](ADR-007) | 2026-07-05 | Accepted |
| 008 | [Trace Data Interchange](ADR-008) | 2026-07-05 | Accepted |
| 009 | [OSI Open Interchange](ADR-009) | 2026-07-05 | Accepted |
| 010 | [GDPR Data Liberation](ADR-010) | 2026-07-05 | Accepted |
| 011 | [Rename to AgentSON](ADR-011) | 2026-07-05 | Accepted |

---

## ADR-001: AgentSON Format

**Context:** Every AI coding agent stores session data in proprietary SQLite databases with unique schemas. No standard format exists for exporting or sharing session traces.

**Decision:** Create `.AgentSON` — a single-file JSON format for capturing AI agent session traces with full metadata, tool calls, and reasoning chains.

**Consequences:**
- (+) One file = one complete session, portable and shareable
- (+) JSON is human-readable and universally supported
- (-) JSON has no binary encoding (larger than SQLite)

---

## ADR-002: JSON over SQLite

**Context:** Session data is stored in SQLite databases locally. Should AgentSON be a SQLite export or a JSON file?

**Decision:** Use JSON files, not SQLite dumps. Each `.AgentSON` file is self-contained.

**Consequences:**
- (+) Single file can be emailed, shared, archived
- (+) No database dependency to read
- (-) No indexing (search requires full scan)

---

## ADR-003: Vendor Neutral

**Context:** AgentSON could depend on specific vendor APIs (OpenAI, Anthropic) for enhanced features.

**Decision:** Never depend on one company's API or format. Every external service is optional. Core features work offline.

**Consequences:**
- (+) If any vendor shuts down, AgentSON still works
- (+) Users own their data completely
- (-) Can't use vendor-specific features (e.g., OpenAI embeddings)

---

## ADR-004: Amber Design Tokens

**Context:** The original `.ailog` page used cyan/blue tokens (`#58a6ff`). Rebranding to AgentSON required new visual identity.

**Decision:** Use amber phosphor tokens: `#ffb000` accent, warm dark background, Space Mono + IBM Plex Sans fonts.

**Consequences:**
- (+) Distinct visual identity from `.ailog`
- (+) Warm, readable dark theme
- (-) Existing `.ailog` users may prefer old colors

---

## ADR-010: GDPR Data Liberation

**Context:** GDPR Article 20 gives users the right to export data in machine-readable format. Most AI tools don't provide this.

**Decision:** Position AgentSON as the tool to exercise GDPR data rights for AI session data. Add "Unsloth analogy" — democratizing data ownership like Unsloth democratized fine-tuning.

**Consequences:**
- (+) Strong legal and ethical justification
- (+) EU AI Act compliance built-in
- (-) May face resistance from vendors who profit from data lock-in

---

## ADR-011: Rename to AgentSON

**Context:** The project was originally `.ailog`. The name conflicted with existing projects (`hemashushu/ason`, `@ason-format/ason`).

**Decision:** Rename to AgentSON (Agent + JSON). Use `.agentson` as file extension.

**Consequences:**
- (+) Clear, descriptive name
- (+) No namespace collisions
- (+) Trademark/name cleared UK/EU/US/PyPI/npm
- (-) Breaking change from `.ailog` format
