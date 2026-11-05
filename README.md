# AgentSON

**Portable, provenance-aware interchange for AI agent session traces.**

[![CI](https://github.com/andiekobbietks/AgentSON/actions/workflows/ci.yml/badge.svg)](https://github.com/andiekobbietks/AgentSON/actions/workflows/ci.yml)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/pypi/pyversions/agentson.svg)](https://pypi.org/project/agentson/)

> **Status: Alpha / pre-release.** AgentSON's v1.2 schema is the canonical format decision, but the implementation is not yet a production-grade, lossless, cross-harness interchange system. Readers, importers, exporters and platform features have different levels of maturity. Verify the behaviour you depend on and retain the original source data.

## Purpose

AgentSON is an open format and toolset for representing the operational history of AI-agent sessions: user inputs, agent outputs, tool actions, observations, state changes, hand-offs and provenance.

The long-term goal is to let a session produced by one AI coding harness be **captured, represented, validated, exchanged, inspected and potentially resumed in another**, without silently losing meaning or provenance.

That is a direction, not a claim that arbitrary sessions can already be resumed across runtimes. AgentSON must preserve source-native evidence, identify unsupported or unmapped fields, and make conversion loss explicit.

## Design principles

- **Portability:** use documented, vendor-neutral structures rather than requiring one hosted service.
- **Provenance:** retain where an event came from and distinguish observed facts from reconstructed or inferred information.
- **Loss-aware conversion:** preserve native source material where possible; do not silently coerce unknown event types or fields.
- **Validation:** publish versioned JSON Schemas and test fixtures so producers and consumers can check conformance.
- **Local-first core:** reading, validation and export should not require an AgentSON-hosted service.
- **Separation of concerns:** the interchange format, source adapters, storage, transport, viewers and managed services are distinct layers.

## What AgentSON is (and is not)

| AgentSON is | AgentSON is not |
|---|---|
| A versioned session-trace data model | A universal agent runtime |
| A JSON Schema-governed interchange representation | A REST API or an OpenAPI specification |
| A place to preserve event and provenance information | Proof that every source adapter is lossless |
| A basis for inspection, analysis and future interoperability | A guarantee that a session can be resumed in another harness |
| An open-source format and local tooling | A compliance certification or legal determination |

AgentSON's severity specification is a data contract expressed with JSON Schema and Pydantic-style validation. It is not a REST resource model. Any API or transport built around AgentSON must define its own HTTP contract, authentication, authorisation, error model, versioning and operational controls.

## Format and schema

**v1.2 is the canonical schema decision** (see [ADR-015](spec/ADR-015-canonical-schema.md), [ADR-016](spec/ADR-016-ontology-enum-reconciliation.md) and [ADR-017](spec/ADR-017-core-vs-streaming.md)).

- Canonical interchange is a **JSONL stream**: one JSON event per line.
- The first event in a stream is `stream-meta`.
- Individual events are validated against [`spec/v1.2-entries.json`](spec/v1.2-entries.json).
- [`spec/v1.2.json`](spec/v1.2.json) describes the session-document representation used by document-oriented tooling and compatibility paths.
- The ontology defines 12 event primitives. See [`spec/ontology.md`](spec/ontology.md).
- v1 and v1.1 are legacy schemas; do not use them for new producers.

### Event primitives

| Primitive | Meaning |
|---|---|
| `stream-meta` | Stream header and participating-agent metadata |
| `user-query` | User input |
| `thought` | Reasoning-related content supplied by the source |
| `action` | Tool or operation invocation |
| `observation` | Information observed from a tool, user, system or sensor |
| `answer` | Agent response |
| `side-effect` | A state or artefact change |
| `user-feedback` | User correction, reaction or clarification |
| `system-event` | Runtime or system signal |
| `capabilities` | Agent capability declaration |
| `handoff` | Transfer of control |
| `presence` | Agent presence or status |

A `thought` event is a source-provided data category. Its presence does not mean that every harness exposes private chain-of-thought, nor should an adapter invent reasoning content that the source did not provide.

### Minimal JSONL example

Each line below is a separate JSON object:

```jsonl
{"type":"stream-meta","stream_id":"session-001","mode":"single","agents":[{"id":"assistant","name":"Assistant"}]}
{"type":"user-query","text":"Find the cause of the failing test."}
{"type":"action","agent":"assistant","tool":"shell.run","args":{"command":"pytest -q"},"tool_call_id":"call-001"}
{"type":"observation","agent":"assistant","source":"tool","text":"One test failed: expected 200, received 500.","correlation_id":"call-001"}
{"type":"answer","agent":"assistant","text":"The endpoint returned an internal server error."}
```

This is an illustrative stream, not a claim that every reader emits these exact fields. Consult the schema and source-adapter documentation for required fields and mapping behaviour.

## Installation

```bash
python -m pip install agentson
```

The repository's package metadata currently identifies the Python distribution as **0.1.0 / Alpha**. The schema version (v1.2) and Python package version are separate version tracks. Check the [PyPI project page](https://pypi.org/project/agentson/) for the version actually published.

For development:

```bash
git clone https://github.com/andiekobbietks/AgentSON.git
cd AgentSON
python -m pip install -e ".[dev]"
python -m pip check
python -m pytest -q
python -m build
```

## CLI quick start

Create the output directory before exporting:

```bash
mkdir -p sessions

# Export a session from a locally available OpenCode database
agentson export --tool opencode --session <session-id> --output ./sessions/

# List locally available sessions
agentson list --tool opencode

# Validate a file or recursively scan a directory
agentson validate ./sessions/

# Search exported .agentson files
agentson search "authentication" --dir ./sessions/

# Render a session as Markdown
agentson render ./sessions/session.agentson --format md
```

The CLI exposes source selectors for OpenCode, MiniMax, Antigravity, Chrome DevTools, Libre CSV, Claude Code, VibeEdge, Gemini, Cursor, Cline and Aider. Availability and completeness are adapter-specific; a selector being present in the CLI is not, by itself, evidence of production readiness or full-fidelity support. Check the relevant reader and tests before relying on a particular source.

Use `agentson --help` and `agentson help <topic>` for the commands and options available in the installed version. Some commands are experimental or explicitly not implemented; the CLI help text is authoritative for the installed build.

## Repository map

```text
.
├── spec/                 # Versioned JSON Schemas, ontology and format ADRs
├── readers/              # Source-specific session readers
├── importers/            # Importers for external conversation formats
├── exporters/            # Export and transformation utilities
├── cli/                  # Command-line interface
├── tests/                # Automated tests and fixtures
├── examples/             # Example session data
├── pwa/                  # Standalone browser/PWA viewer
├── docs/                 # Project documentation and web viewer
├── agentson_platform/    # Separate, optional platform functionality
├── .github/workflows/    # CI workflows
├── pyproject.toml         # Python package metadata and dependencies
├── CHANGELOG.md           # Change history
├── ROADMAP.md             # Planned work (not a delivery guarantee)
├── SECURITY.md            # Vulnerability-reporting policy
└── CONTRIBUTING.md        # Contribution and verification guidance
```

The optional platform is architecturally separate from the open interchange core. Hosted storage, dashboards, billing, ingestion services and other platform functions are not prerequisites for reading or validating local AgentSON files.

## Interoperability model

A reliable interchange pipeline has distinct stages:

1. **Capture:** obtain source-native events through a supported export, API or reader.
2. **Preserve:** retain the original source payload or a recoverable reference where licensing and privacy permit.
3. **Map:** translate source events into AgentSON primitives with explicit mapping metadata.
4. **Validate:** check the stream against the versioned schema and semantic constraints.
5. **Exchange:** transfer the validated representation through a separately specified transport.
6. **Inspect:** review events, provenance, omissions and conversion warnings.
7. **Resume (future capability):** reconstruct execution only where the target runtime can safely and meaningfully interpret the captured state.

A valid JSON document proves structural conformance to the schema; it does not prove semantic equivalence, complete capture, safe replay, or successful resumption. Those require source-specific fixtures, round-trip tests, loss reports and cross-runtime integration tests.

## Privacy, security and compliance

Agent sessions may contain credentials, personal data, confidential code, health information and other sensitive material. Treat exports as sensitive records.

- Review and redact data before sharing or publishing a session.
- Do not commit real session exports, credentials or personal data to the repository.
- Keep source permissions and retention obligations in force after export.
- Do not treat an export feature as proof of GDPR compliance or an AI Act conformity assessment.
- GDPR data portability rights depend on the legal conditions and scope in Article 20; they do not automatically cover every AI interaction or every category of data.
- EU AI Act transparency duties are use-case- and provision-specific. AgentSON does not certify compliance.

See [SECURITY.md](SECURITY.md) for vulnerability reporting and [CONTRIBUTING.md](CONTRIBUTING.md) for safe fixtures and development checks.

## Standards and architecture

- [Production-readiness assessment](docs/production-readiness-assessment.md)
- [ADR-023: Production readiness and the knowledge-catalogue boundary](spec/ADR-023-production-readiness-and-knowledge-catalog-architecture.md)
- [JSON Schema v1.2](spec/v1.2.json)
- [Flattened event schema](spec/v1.2-entries.json)
- [Event ontology](spec/ontology.md)
- [Architecture decisions](spec/)
- [Operating manual](docs/standards/)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

AgentSON considers relevant government and industry guidance where applicable, including the [GDS API technical and data standards](https://www.gov.uk/guidance/gds-api-technical-and-data-standards) and the [Technology Code of Practice](https://www.gov.uk/guidance/the-technology-code-of-practice). These are design references, not a claim of blanket compliance. API-specific requirements apply when an API is actually provided; the JSON Schema alone is not an API implementation.

## Contributing

Contributions should preserve portability, provenance and honest feature status. Please read [CONTRIBUTING.md](CONTRIBUTING.md), add regression tests for fixes, update schemas and examples when contracts change, and distinguish implemented behaviour from planned work.

## Licence

AgentSON is licensed under the [Apache License 2.0](LICENSE).
