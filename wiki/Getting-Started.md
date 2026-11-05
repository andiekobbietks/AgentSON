# Getting Started

## What AgentSON is

AgentSON is an open interchange format and toolchain for AI-agent sessions. Its goal is to make sessions captured in one harness understandable and exchangeable in another while preserving source meaning and provenance.

The canonical v1.2 archive is a single JSON session envelope with an ordered `entries` array. It is not a guarantee that a different harness can reproduce or resume the original runtime.

## Install

```bash
pip install agentson
```

## Inspect available commands

```bash
agentson --help
```

Command availability depends on the installed package version. Consult the CLI help for the commands actually exposed by that release; do not assume every roadmap or historical README command is implemented.

## Current workflow

The README documents the project-level quick start. In general:

1. Select a supported source reader.
2. Export a session from the source harness.
3. Validate the resulting canonical v1.2 envelope against the versioned schema.
4. Inspect the session without executing imported actions.
5. Preserve the original archive and its provenance/loss report.

Use [Readers](Readers) to check module inventory and evidence. A module being present does not prove it is fully tested.

## Understand the format

- [Schema](Schema) — canonical envelope and event vocabulary.
- [Session interoperability architecture](https://github.com/andiekobbietks/AgentSON/blob/master/docs/architecture/session-interoperability.md) — capture, exchange, inspection, reconstruction and resumption.
- [ADR-024](https://github.com/andiekobbietks/AgentSON/blob/master/spec/ADR-024-canonical-session-archive-and-interoperability.md) — canonical archive decision.

## Important distinctions

- **Portable:** another consumer can parse and understand the archive.
- **Reconstructable:** a consumer can rebuild a useful representation while declaring missing state.
- **Resumable:** a compatible harness can continue from a validated checkpoint with permissions and safety checks.

A transcript that renders in a viewer is not proof of runtime reconstruction or resumption. Imported tool calls and outputs are untrusted and must not execute during inspection.
