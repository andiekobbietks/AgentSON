# Issue: Competitive landscape — AgentLog (braintied/agentlog)

## Status

**Pre-standard phase.** Multiple groups independently converge on portable agent execution representation. No standard formation, no lock-in effects, no dominant distribution channel yet.

## What exists (verified facts only)

| | AgentSON | AgentLog |
|---|---|---|
| **GitHub stars** | — | 0 |
| **Commits** | — | 9 |
| **Working readers** | 9 | 2 (Claude Code, Watchtower) |
| **Fine-tuning export** | Yes (Unsloth/Olive) | No |
| **Healthcare data** | Yes (FreeStyle Libre) | No |
| **License** | Apache 2.0 | Apache 2.0 |
| **Language** | Python | TypeScript |
| **Paid product** | No | Ora Cloud (claimed, unverified) |

## What we don't know

- Team size at Braintied
- Funding status
- Actual adoption (both repos have 0 stars)
- Whether Ora Cloud has paying customers

## The useful distinction

| Axis | Enterprise-first | Developer-first |
|------|-----------------|----------------|
| Sales motion | consulting / contracts | OSS adoption |
| Adoption path | CTO → org rollout | dev → grassroots |
| Constraints | compliance, SOC2, audit | usability, flexibility |

These are different go-to-market paths, not a competition yet.

## AgentSON's factual advantages

1. **9 readers vs 2** — covers Cursor, Cline, Aider (they don't)
2. **Fine-tuning export** — nobody else has Unsloth/Olive integration
3. **FreeStyle Libre 2** — no one else covers health data
4. **SOP library** — 14 operational procedures

## AgentLog's factual advantages

1. **TypeScript ecosystem** — where Cursor/Cline/Aider users live
2. **OTel GenAI mapping** — observability integration
3. **"Cortex" blog** — content marketing exists

## What actually matters

Not "who has more readers" but "what abstraction becomes the default mental model for agent execution representation."

That depends on:
- simplicity of the schema
- integration with existing tools (LangChain, MCP, etc.)
- clean separation of execution, memory, observability, training data
- incremental adoptability

## Sources

- AgentLog repo: https://github.com/braintied/agentlog
- Watchtower repo: https://github.com/braintied/watchtower
- Both have 0 stars as of July 2026
