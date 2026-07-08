# AgentSON Roadmap

**Last updated:** 05 July 2026

## Vision

AgentSON is the universal interchange format for AI agent session traces. This roadmap prioritizes readers by RICE score (Reach × Impact × Confidence / Effort) to maximize coverage of the 33-tool AI coding landscape.

## RICE Scoring

| Factor | Definition | Scale |
|--------|-----------|-------|
| **Reach** | Monthly active users who would benefit | Thousands |
| **Impact** | Value the reader adds (portability, training data) | 1 (low) – 3 (high) |
| **Confidence** | How sure we are about estimates | 0.5 – 1.0 |
| **Effort** | Person-months to build and test | 0.5 – 4.0 |

**RICE = (Reach × Impact × Confidence) / Effort**

---

## Tier 1: Core Market (Priority: Highest)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 1 | **Cursor** | Anysphere/SpaceX | 2000 | 3 | 0.9 | 2.0 | **2700** | 🔜 Planned |
| 2 | **Claude Code** | Anthropic | 1500 | 3 | 0.8 | 0.0 | **∞** | ✅ Working |
| 3 | **Kiro** | AWS/Amazon | 800 | 3 | 0.7 | 1.5 | **1120** | 🔜 Planned |
| 4 | **Codex CLI** | OpenAI | 1200 | 3 | 0.8 | 1.5 | **1920** | 🔜 Planned |
| 5 | **Gemini CLI** | Google | 1000 | 2 | 0.7 | 1.0 | **1400** | 🔜 Planned |
| 6 | **Windsurf/Devin Desktop** | Cognition | 600 | 2 | 0.6 | 1.5 | **480** | 🔜 Planned |

**Rationale:** These tools have the largest user bases and generate the richest session traces. Cursor and Claude Code alone represent ~3.5B monthly sessions. Building readers here gives AgentSON access to 80%+ of the AI coding market.

---

## Tier 2: Open Source (Priority: High)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 7 | **opencode** | Anomaly | 6500 | 3 | 1.0 | 0.0 | **∞** | ✅ Working |
| 8 | **Cline** | Cline Labs | 500 | 3 | 0.9 | 1.0 | **1350** | 🔜 Planned |
| 9 | **Aider** | Paul Gauthier | 400 | 3 | 0.9 | 0.8 | **1350** | 🔜 Planned |
| 10 | **Goose** | Block | 200 | 2 | 0.7 | 1.0 | **280** | 🔜 Planned |
| 11 | **OpenHands** | All-Hands | 150 | 2 | 0.7 | 1.0 | **210** | 🔜 Planned |
| 12 | **Zed** | Zed Industries | 300 | 2 | 0.6 | 1.5 | **240** | 🔜 Planned |

**Rationale:** Open-source tools have BYOK users who care about data ownership. These users are AgentSON's natural advocates. opencode already works. Cline and Aider are next because their users actively choose data sovereignty.

---

## Tier 3: Extensions (Priority: Medium)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 13 | **GitHub Copilot** | Microsoft | 5000 | 2 | 0.8 | 2.0 | **4000** | 🔜 Planned |
| 14 | **Amazon Q** | AWS | 400 | 2 | 0.7 | 1.5 | **373** | 🔜 Planned |
| 15 | **JetBrains AI** | JetBrains | 300 | 2 | 0.7 | 1.5 | **280** | 🔜 Planned |
| 16 | **Sourcegraph Cody** | Sourcegraph | 100 | 1 | 0.6 | 1.0 | **60** | 🔜 Planned |
| 17 | **Qodo** | Qodo | 50 | 1 | 0.5 | 1.0 | **25** | 🔜 Planned |
| 18 | **Augment Code** | Augment | 80 | 1 | 0.5 | 1.0 | **40** | 🔜 Planned |
| 19 | **Continue** | Continue | 200 | 2 | 0.8 | 1.0 | **320** | 🔜 Planned |
| 20 | **Tabnine** | Tabnine | 150 | 1 | 0.7 | 1.0 | **105** | 🔜 Planned |

**Rationale:** Extensions wrap existing IDEs. High reach (Copilot alone has 5M+ users) but lower impact because they inherit the host IDE's storage. Copilot is highest priority here due to sheer market share.

---

## Tier 4: Builders (Priority: Low-Medium)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 21 | **Bolt.new** | StackBlitz | 200 | 1 | 0.5 | 1.5 | **67** | 🔜 Planned |
| 22 | **v0** | Vercel | 300 | 1 | 0.5 | 1.5 | **100** | 🔜 Planned |
| 23 | **Lovable** | Lovable | 150 | 1 | 0.5 | 1.5 | **50** | 🔜 Planned |
| 24 | **Replit** | Replit | 500 | 1 | 0.6 | 2.0 | **150** | 🔜 Planned |

**Rationale:** Builder traces are prompt→app, not agent→code. Lower training value but still portable. Replit has the largest user base.

---

## Tier 5: Orchestrators (Priority: Low)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 25 | **amux** | amux | 50 | 2 | 0.5 | 1.5 | **33** | 🔜 Planned |
| 26 | **Claude Squad** | Claude Squad | 30 | 2 | 0.5 | 1.0 | **30** | 🔜 Planned |
| 27 | **Kilo Code** | Kilo Code | 80 | 2 | 0.6 | 1.0 | **96** | 🔜 Planned |
| 28 | **dmux** | dmux | 20 | 2 | 0.5 | 1.0 | **20** | 🔜 Planned |

**Rationale:** Orchestrators manage fleets of agents. Traces are aggregate, not individual. Lower training value but useful for fleet analytics.

---

## Tier 6: Autonomous (Priority: Low)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 29 | **Devin** | Cognition | 100 | 2 | 0.6 | 2.0 | **60** | 🔜 Planned |
| 30 | **Blitzy** | Blitzy | 20 | 1 | 0.4 | 2.0 | **4** | 🔜 Planned |

**Rationale:** Fully autonomous agents generate long-running task traces. High value per trace but small user base. Devin shares infrastructure with Windsurf (Cognition), so building Windsurf first covers both.

---

## Tier 7: China Plans (Priority: Deferred)

| # | Tool | Company | Reach | Impact | Confidence | Effort | RICE | Status |
|---|------|---------|-------|--------|------------|--------|------|--------|
| 31 | **GLM Coding** | Z.ai | 200 | 1 | 0.3 | 2.0 | **30** | ⏸ Deferred |
| 32 | **Kimi** | Moonshot AI | 150 | 1 | 0.3 | 2.0 | **23** | ⏸ Deferred |
| 33 | **Qwen Code** | Alibaba | 300 | 1 | 0.3 | 2.0 | **45** | ⏸ Deferred |

**Rationale:** Growing fast in Asia but documentation is in Chinese, storage formats are undocumented, and regulatory environment is uncertain. Defer until Tier 1-3 readers are stable.

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

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines. Priority readers to build:

1. **Cursor** (RICE: 2700) — biggest market
2. **Claude Code** (RICE: 2400) — most loved
3. **Cline** (RICE: 1350) — open source, BYOK
4. **Aider** (RICE: 1350) — open source, terminal
5. **Gemini CLI** (RICE: 1400) — free, Apache 2.0
