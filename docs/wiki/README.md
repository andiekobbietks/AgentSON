# AgentSON Wiki Mirror

This directory contains the Markdown source of the [AgentSON GitHub Wiki](https://github.com/andiekobbietks/AgentSON/wiki).

## Legacy directory

The root-level `wiki/` directory is a historical duplicate and is not the publishing source. Do not edit it. Use `docs/wiki/` for wiki content and keep the hosted GitHub Wiki synchronised from these files.

## Authoritative source

**The `docs/` directory in the main repository is the authoritative source for AgentSON documentation.** The GitHub Wiki is a published mirror of these files. Edits should be made here first, then mirrored to the wiki.

## Files

| File | Purpose |
|------|---------|
| [Home.md](Home.md) | Wiki index and overview |
| [Getting-Started.md](Getting-Started.md) | Install, export your first session, understand the format |
| [Schema.md](Schema.md) | JSON Schema reference |
| [Session Interoperability Architecture](https://github.com/andiekobbietks/AgentSON/blob/master/docs/architecture/session-interoperability.md) | Cross-harness capture, exchange, inspection, reconstruction and resumption boundaries |
| [Cross-Harness Conformance Test Plan](https://github.com/andiekobbietks/AgentSON/blob/master/docs/architecture/conformance-test-plan.md) | Executable conformance levels, adapter pair matrix and known gaps |
| [Readers.md](Readers.md) | Tool-specific readers |
| [ADRs.md](ADRs.md) | Architecture Decision Records index |
| [SOPs.md](SOPs.md) | Standard Operating Procedures |
| [Coding-Standards.md](Coding-Standards.md) | Non-negotiable rules for code |
| [Mental-Models.md](Mental-Models.md) | How we think about problems |
| [Contributing.md](Contributing.md) | How to contribute |
| [SOP-015-Creating-GitHub-Wiki.md](SOP-015-Creating-GitHub-Wiki.md) | Wiki maintenance procedure |

## Syncing to the wiki

The wiki repository is `https://github.com/andiekobbietks/AgentSON.wiki.git`. When content in `docs/wiki/` changes, copy the updated Markdown files to the wiki repository and push.
