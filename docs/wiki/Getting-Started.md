# Getting Started

## What AgentSON is

AgentSON is a local-first format and toolset for exporting, validating, searching and inspecting AI-agent session histories. The project is Alpha. Reader coverage and fidelity vary by source.

The canonical v1.2 interchange format is JSONL: one JSON event per line, with stream-meta first. The .agentson extension is retained. Individual events are validated against spec/v1.2-entries.json. The JSON session envelope in spec/v1.2.json is a supported materialised/document representation, not the canonical JSONL wire format.

## Install

~~~bash
python -m pip install agentson
~~~

For a development checkout:

~~~bash
git clone https://github.com/andiekobbietks/AgentSON.git
cd AgentSON
python -m pip install -e ".[dev]"
~~~

## Inspect available commands

~~~bash
agentson --help
agentson help export
agentson help validate
~~~

The installed CLI help is authoritative for the commands and options available in that package version. Some adapters and destination integrations are experimental.

## Example local workflow

Export a session from a locally available OpenCode database:

~~~bash
agentson export --tool opencode --session SESSION_ID --output ./sessions/
agentson list --tool opencode
agentson validate ./sessions/
agentson search "authentication" --dir ./sessions/
agentson render ./sessions/opencode_SESSION_ID.agentson --format md
~~~

Replace SESSION_ID with a real local session identifier and check the output filename produced by the installed version.

## Context continuation

The resume command can create a portable Markdown context packet:

~~~bash
agentson resume ./sessions/opencode_SESSION_ID.agentson --target claude-code --output ./handoff.md
~~~

A context packet is not a runtime checkpoint. It does not restore hidden prompts, credentials, permissions, unsaved buffers, live processes or provider-private state. Review it before sharing or importing it. Pattern-based redaction is best-effort, not a guarantee.

The experimental OpenCode destination adapter can queue a capsule through the documented OpenCode v2 API. It does not immediately start an agent turn, but queued content may enter model context on a later turn. Treat the archive as untrusted and sensitive. See ADR-025.

## Important distinctions

- A reader extracts source data; it does not automatically provide a destination import.
- A valid archive does not prove complete or lossless capture.
- A read-back digest proves the tested stored bytes, not semantic equivalence.
- Portability, reconstruction and resumption require different evidence.
- AgentSON does not certify GDPR or EU AI Act compliance.

## Further reading

- Schema Reference
- Reader and Adapter Inventory
- Session Interoperability Architecture
- Cross-Harness Conformance Test Plan
- Contributing to AgentSON
