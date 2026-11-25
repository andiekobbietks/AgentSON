# AgentSON Roadmap

**Last updated:** 25 November 2026

## Vision

AgentSON is a vendor-neutral interchange format and tooling project for preserving AI-agent session traces. This roadmap prioritises prospective readers using RICE as one decision aid; it does not treat the score as a substitute for strategic judgement or evidence.

## RICE scoring methodology

RICE = (Reach × Impact × Confidence) / Effort.

| Factor | Operational definition | Scale / rule |
|---|---|---|
| **Reach** | Estimated incremental monthly users who could benefit from this specific reader, expressed in **thousands of users** | Non-negative numeric estimate; document source, geography, date and overlap assumptions |
| **Impact** | Expected value of delivering this reader for portability, fidelity and usable session evidence | 1 = limited; 2 = material; 3 = high. Apply the anchors below |
| **Confidence** | Evidence-weighted confidence in the combined reach and impact assumptions | 0.3–1.0; explain evidence and uncertainty |
| **Effort** | End-to-end person-months for discovery, implementation, tests, documentation and initial maintenance | Must be strictly greater than zero; estimate consistently across readers |

### Impact anchors

Assess the same three dimensions for every reader: (a) fidelity of captured events, (b) coverage of important user workflows, and (c) portability value beyond the source tool.

- **1 — Limited:** one narrow workflow, partial or low-fidelity capture, or a practical workaround already exists.
- **2 — Material:** reliable coverage of common events in a meaningful workflow, with manageable gaps and useful portability.
- **3 — Very high:** high-fidelity coverage of critical workflows, materially unlocks cross-tool use or migration, and has no reasonable equivalent workaround.

Use the overall level that best fits the evidence; do not award a 3 merely because the source product is popular.

### Confidence calibration

Use these anchors as guidance rather than pretending confidence is a statistically measured probability:

- **1.0:** direct, current primary evidence for reach and a working prototype or measured implementation effort.
- **0.9:** strong primary evidence and limited technical unknowns.
- **0.7:** credible evidence, but some audience or implementation assumptions remain.
- **0.5:** proxy metrics or material uncertainty in reach, fidelity or effort.
- **0.3:** speculative estimate with little direct evidence.

Values between anchors are permitted only when the rationale is recorded.

### Scoring and governance rules

1. **Reach unit:** a Reach value of 2,000 means an estimated 2,000,000 monthly users, not 2,000 users. Scores are therefore comparable only while this unit remains unchanged.
2. **No zero-effort scores:** a completed reader is not a zero-effort future project. Move shipped readers to the existing-reader inventory and exclude them from prospective prioritisation. Never report infinity.
3. **Consistent effort:** estimate the same lifecycle boundary for every reader. Include discovery, implementation, tests, docs and initial maintenance; do not enter sunk cost as future effort.
4. **Evidence and confidence:** every estimate should eventually cite a dated source or a documented bottom-up estimate. Confidence must reflect source quality, uncertainty, overlap and implementation unknowns, not intuition alone.
5. **Avoid double counting:** users may use several tools. Reach should estimate the incremental audience for the reader, not sum overlapping vendor headline user counts.
6. **Global ranking:** the table below is sorted by calculated RICE score across all planned and deferred candidates. Market segment is descriptive, not a hidden priority tier.
7. **Strategic overrides:** security, platform importance, ecosystem leverage, regulatory obligations or dependency value may justify work that does not rank highly. Record the reason separately; do not manipulate RICE inputs to force the desired result.
8. **No false precision:** scores are prioritisation indicators, not forecasts of revenue, adoption or engineering productivity. Similar scores should be treated as ties unless better evidence distinguishes them.
9. **Refresh estimates:** revisit reach, confidence and effort when source data changes, a prototype is built, or an estimate becomes stale. Record the date and owner of each revision.

### Current estimate quality

The figures below are inherited from the previous roadmap and have **not yet been independently substantiated** with dated audience sources or implementation estimates. They are retained for auditability and recalculated consistently, not presented as verified market facts. The scores are provisional. In particular, the prior claim that Cursor and Claude Code represent approximately 3.5 billion monthly sessions and the claim of 80%+ market coverage are removed because the roadmap did not provide evidence supporting them.

## Prospective reader prioritisation

Reach is in thousands of estimated monthly users. RICE scores use that same unit and are shown to two decimal places where needed. Rows are ranked globally by the formula, not grouped into priority tiers.

| Rank | Reader | Market segment | Reach (000s) | Impact | Confidence | Effort (person-months) | RICE | Status |
|---:|---|---|---:|---:|---:|---:|---:|---|
| 1 | **GitHub Copilot** | Extensions | 5000 | 2 | 0.8 | 2.0 | **4000** | Planned |
| 2 | **Cursor** | Core | 2000 | 3 | 0.9 | 2.0 | **2700** | Planned |
| 3 | **Codex CLI** | Core | 1200 | 3 | 0.8 | 1.5 | **1920** | Planned |
| 4 | **Gemini CLI** | Core | 1000 | 2 | 0.7 | 1.0 | **1400** | Planned |
| 5 | **Cline** | Open Source | 500 | 3 | 0.9 | 1.0 | **1350** | Planned |
| 6 | **Aider** | Open Source | 400 | 3 | 0.9 | 0.8 | **1350** | Planned |
| 7 | **Kiro** | Core | 800 | 3 | 0.7 | 1.5 | **1120** | Planned |
| 8 | **Windsurf/Devin Desktop** | Core | 600 | 2 | 0.6 | 1.5 | **480** | Planned |
| 9 | **Amazon Q** | Extensions | 400 | 2 | 0.7 | 1.5 | **373.33** | Planned |
| 10 | **Continue** | Extensions | 200 | 2 | 0.8 | 1.0 | **320** | Planned |
| 11 | **JetBrains AI** | Extensions | 300 | 2 | 0.7 | 1.5 | **280** | Planned |
| 11 | **Goose** | Open Source | 200 | 2 | 0.7 | 1.0 | **280** | Planned |
| 13 | **Zed** | Open Source | 300 | 2 | 0.6 | 1.5 | **240** | Planned |
| 14 | **OpenHands** | Open Source | 150 | 2 | 0.7 | 1.0 | **210** | Planned |
| 15 | **Replit** | Builders | 500 | 1 | 0.6 | 2.0 | **150** | Planned |
| 16 | **Tabnine** | Extensions | 150 | 1 | 0.7 | 1.0 | **105** | Planned |
| 17 | **v0** | Builders | 300 | 1 | 0.5 | 1.5 | **100** | Planned |
| 18 | **Kilo Code** | Orchestrators | 80 | 2 | 0.6 | 1.0 | **96** | Planned |
| 19 | **Bolt.new** | Builders | 200 | 1 | 0.5 | 1.5 | **66.67** | Planned |
| 20 | **Sourcegraph Cody** | Extensions | 100 | 1 | 0.6 | 1.0 | **60** | Planned |
| 20 | **Devin** | Autonomous | 100 | 2 | 0.6 | 2.0 | **60** | Planned |
| 22 | **Lovable** | Builders | 150 | 1 | 0.5 | 1.5 | **50** | Planned |
| 23 | **Qwen Code** | China | 300 | 1 | 0.3 | 2.0 | **45** | Deferred |
| 24 | **Augment Code** | Extensions | 80 | 1 | 0.5 | 1.0 | **40** | Planned |
| 25 | **amux** | Orchestrators | 50 | 2 | 0.5 | 1.5 | **33.33** | Planned |
| 26 | **Claude Squad** | Orchestrators | 30 | 2 | 0.5 | 1.0 | **30** | Planned |
| 26 | **GLM Coding** | China | 200 | 1 | 0.3 | 2.0 | **30** | Deferred |
| 28 | **Qodo** | Extensions | 50 | 1 | 0.5 | 1.0 | **25** | Planned |
| 29 | **Kimi** | China | 150 | 1 | 0.3 | 2.0 | **22.5** | Deferred |
| 30 | **dmux** | Orchestrators | 20 | 2 | 0.5 | 1.0 | **20** | Planned |
| 31 | **Blitzy** | Autonomous | 20 | 1 | 0.4 | 2.0 | **4** | Planned |

### Interpretation

- The inherited inputs place GitHub Copilot first, followed by Cursor and Codex CLI. This differs from the old tier labels, which were not globally ordered by score.
- Cline and Aider tie at 1,350; JetBrains AI and Goose tie at 280; Sourcegraph Cody and Devin tie at 60; Claude Squad and GLM Coding tie at 30. Equal scores share a rank. Resolve ties using strategic fit, evidence quality, prototype findings or dependencies, not arbitrary decimal adjustments.
- The table does **not** establish that Copilot has the greatest incremental reach in reality. Its 5,000 (000s) input is unverified and must be sourced before committing engineering capacity.
- The combined "Windsurf/Devin Desktop" row is not an ideal unit of work. Split it into separately scoped reader projects before using its score for a delivery commitment.
- Deferred status is a strategic decision, not a claim that a low RICE score alone proves a reader should be deferred.

### Evidence register required before committing work

For each candidate, add:
- reach source URL, publication/access date, metric definition and geography;
- estimate of the proportion of users likely to use the relevant product feature;
- overlap adjustment for users already counted under other readers;
- confidence rationale and unresolved unknowns;
- effort breakdown by discovery, implementation, testing, documentation and initial maintenance;
- estimate owner and last-reviewed date.

Until that evidence is added, use this table to identify hypotheses for validation, not to make precise capacity or market-share claims.

---

## Existing Readers (v0.1.0)

| Tool | Status | Reader | Tests |
|------|--------|--------|-------|
| opencode | ✅ Working | `readers/opencode.py` | ✅ Passing |
| MiniMax | ✅ Working | `readers/minimax.py` | ✅ Passing |
| Antigravity IDE | ✅ Working | `readers/antigravity.py` | ✅ Passing |
| FreeStyle Libre 2 | ✅ Working | `readers/libre.py` | ✅ Passing |
| Chrome DevTools AI | ✅ Working | `readers/chrome_devtools.py` | ✅ 9 tests |
| Claude Code | ✅ Working | `readers/claude_code.py` | ✅ Passing |
| ChatGPT | ✅ Working | `importers/chatgpt.py` | ✅ Passing |
| MCP (protocol) | ✅ Working | `importers/mcp.py` | ✅ Loads |
| A2A (protocol) | ✅ Working | `importers/a2a.py` | ✅ Loads |
| AGNTCY (protocol) | ✅ Working | `importers/agntcy.py` | ✅ Loads |

---

## Version Milestones

| Version | Target Date | Criteria | Readers |
|---------|-------------|----------|---------|
| **v0.1.0** | 2026-07-05 | Initial release | 6 + importer |
| **v0.2.0** | 2026-07 | Protocol adapters + Docker/LXD Hub tools + Astro 7 site | 8 + 3 protocol importers |
| **v0.3.0** | 2026-08 | Corpus: 10+ readers, sample data from each | 15+ |
| **v1.0.0** | 2026-09 | Stable: all Tier 1 readers, CI/CD, docs | 20+ |

---

## Distribution Channels

| Channel | Status | Use Case |
|---------|--------|----------|
| **PyPI** | ✅ Done | Python CLI & library distribution |
| **Docker Hub** | 🛠 Tools built | OCI artifact distribution + Docker Agent integration |
| **LXD Hub** | 🛠 Tools built | System containers for persistent agent daemons |
| **npm** | 🔜 Planned | JavaScript/TypeScript CLI & stream module |

AgentSON sessions are **cross-registry compatible** — publish to Docker Hub as OCI artifacts, pull from LXD Hub as system containers. No conversion needed.

## What NOT to Build

| Component | Why Not | Who Does It Better |
|-----------|---------|-------------------|
| Model weights format | Not our scope, already defined by OSI | Hugging Face, MLCommons |
| Source code architecture | Already defined | Existing standards |
| Inference pipeline | Partially defined, adjacent but different | AIX standard |
| Cloud sync service | Supabase integration exists | Users can self-host |
| IDE integration | Premature, focus on format first | VS Code extensions later |

---

## Success Metrics

| Metric | v0.1.0 | v0.2.0 | v1.0.0 |
|--------|--------|--------|--------|
| Working readers | 5 | 10 | 20 |
| GitHub stars | 10 | 50 | 200 |
| Monthly PyPI downloads | 10 | 100 | 1,000 |
| Example .AgentSON files | 5 | 15 | 50 |
| Contributors | 1 | 3 | 10 |

---

## How to Contribute

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. The list below reflects provisional RICE ordering, not a commitment; validate the evidence register before scheduling work. Priority readers to build:

1. **GitHub Copilot** (provisional RICE: 4000) — highest inherited score; validate reach
2. **Cursor** (provisional RICE: 2700) — high-impact core reader
3. **Codex CLI** (provisional RICE: 1920) — high-impact core reader
4. **Gemini CLI** (provisional RICE: 1400) — high-reach core reader
5. **Cline / Aider** (provisional RICE: 1350 each) — open-source readers; tie requires qualitative decision
