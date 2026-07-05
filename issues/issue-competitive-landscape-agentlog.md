# Issue: Competitive landscape — AgentLog (braintied/agentlog)

## Summary

AgentLog is the closest competitor to AgentSON. Both are Apache 2.0, JSON-based formats for AI agent session interchange. This issue documents the competitive landscape and AgentSON's advantages.

## Head-to-head comparison

| | AgentSON | AgentLog |
|---|---|---|
| **Created by** | Andrea Enning (solo) | Braintied (company) |
| **License** | Apache 2.0 | Apache 2.0 |
| **Language** | Python | TypeScript |
| **Working readers** | 9 | 2 |
| **Fine-tuning export** | Yes (Unsloth/Olive) | No |
| **Healthcare data** | Yes (FreeStyle Libre) | No |
| **Observability** | No | OTel GenAI mapping |
| **Multi-agent** | No | Yes |
| **Backed by** | Solo developer | Company with product |

## AgentLog's ecosystem

- **AgentLog** — the session format spec (9 commits, 0 stars)
- **Watchtower** — auto-captures Claude Code sessions, AI-analyzes them (3 commits, 0 stars)
- **Ora Cloud** — paid enterprise version (multi-project, team mgmt, Sentry integration)
- **Cortex** — editorial publication (thought leadership blog)

## Their target audience

Enterprise SaaS teams, CTOs, engineering managers who want to track AI usage across teams.

## Our target audience

Individual developers who want to own their data, export sessions, and fine-tune on them.

## AgentSON's advantages

1. **Fine-tuning export** — Nobody else has Unsloth/Olive integration
2. **FreeStyle Libre 2** — No one else covers health data
3. **9 readers vs 2** — We cover Cursor, Cline, Aider (they don't)
4. **SOP library** — 14 operational procedures
5. **Python ecosystem** — Most AI tooling is Python

## AgentLog's advantages

1. **Company backing** — They have funding/team
2. **OTel mapping** — Observability integration
3. **Content marketing** — "Cortex" blog builds mindshare
4. **Enterprise play** — Ora Cloud targets CTOs

## Risk assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| They ship Cursor/Cline/Aider first | Low (we shipped first) | Keep shipping readers |
| They get enterprise adoption | Medium (different market) | Don't compete for enterprise |
| OTel becomes standard | Medium | Consider adding OTel mapping later |
| TypeScript ecosystem wins | Low | Python is where AI tooling lives |

## Action items

- [x] Ship Cursor, Cline, Aider readers (done)
- [ ] Get 100+ GitHub stars
- [ ] Get 500+ PyPI downloads
- [ ] Get written up in newsletters
- [ ] Consider OTel mapping for observability integration
