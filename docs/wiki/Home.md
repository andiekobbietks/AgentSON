# AgentSON Wiki

**Agent + JSON** — The open interchange format for AI agent session traces.

> Nobody has done for agent session logs what OpenAPI did for REST APIs or what containers.dev did for dev environments.

---

## Why This Exists

This project started with a FreeStyle Libre 2 continuous glucose monitor.

Managing a chronic condition means your most personal data — blood glucose readings every 5 minutes, 24/7 — lives inside a vendor's app. Abbott's FreeStyle Libre app stores your data. It doesn't export to JSON. It doesn't integrate with your AI tools. It doesn't connect to your doctor's system without jumping through NHS FHIR hoops.

The same lock-in problem exists everywhere:

| Domain | Vendor | Data trapped |
|--------|--------|--------------|
| Health | Abbott (FreeStyle Libre 2) | Glucose readings, trends, reports |
| AI coding | OpenAI, Anthropic, Google | Session transcripts, reasoning traces |
| Development | Cursor, Copilot, Claude Code | Code context, edit history |

**GDPR Article 20** gives you the right to export your data in a machine-readable format. **The EU AI Act** requires transparency about AI-generated content. Most tools don't provide this. AgentSON does.

> **Your health data. Your code sessions. Your data. One format.**

---

## Wiki Pages

| Page | Description |
|------|-------------|
| [Getting Started](Getting-Started) | Install, export your first session, understand the format |
| [Schema](Schema) | JSON Schema v1.1 reference — entry types, trajectory semantics |
| [Readers](Readers) | Tool-specific readers — what works, what's planned |
| [ADRs](ADRs) | Architecture Decision Records — why decisions were made |
| [SOPs](SOPs) | Standard Operating Procedures — health data, AI sessions, infra |
| [Coding Standards](Coding-Standards) | Non-negotiable rules for code |
| [Mental Models](Mental-Models) | How we think about problems before writing code |
| [Contributing](Contributing) | How to add a reader, write tests, submit PRs |

---

## Quick Links

- **PyPI:** [pypi.org/project/agentson](https://pypi.org/project/agentson/)
- **GitHub:** [github.com/andiekobbietks/AgentSON](https://github.com/andiekobbietks/AgentSON)
- **Live Docs:** [andiekobbietks.github.io/AgentSON](https://andiekobbietks.github.io/AgentSON/)
- **License:** Apache 2.0

---

*"The format that AI companies spend billions to own, AgentSON gives away for free."*
