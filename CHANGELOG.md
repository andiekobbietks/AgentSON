# Changelog

All notable changes to AgentSON will be documented here. AgentSON uses [Semantic Versioning](https://semver.org/).

## [1.1.0] - 2026-07-05

### Added

- **Top-level `task` field.** String. The user goal that initiated the trajectory. Optional. Maps cleanly to Fara-7B's expected `task` field.
- **Top-level `outcome` field.** Enum: `success | partial | aborted | error`. Optional (default `partial`). Lets consumers filter trajectories by outcome without walking `entries`.
- **New entry type: `observation`.** First-class observation entries with `text`, `source` (`agent | user | system | tool | sensor | other`), `correlation_id` (links to the `tool_call_id` of the causing action), `attachments` (image/file/audio/video), `status`, `timestamp`, `duration_ms`. Replaces the pattern of inlining observations into `action.output` when they're async, multi-modal, or from a separate source.
- **`tool_call_id` on `action` entries.** Unique per invocation. Observations set `correlation_id` to this value to pair them.
- **`status` extended to all entry types.** Was `action`-only in v1.0. Now valid on `thought`, `observation`, `answer`, etc.
- **`duration_ms` per entry.** Wall-clock duration for the entry (action execution time, observation latency, etc).
- **`error` field on `action` entries.** Structured error details: `{type, message, stack}` for failed actions.
- **Trajectory view docs** at `docs/spec/trajectory-view.md`. Documents the canonical `user-query → (thought → action → observation)* → answer` loop and when to use inline `action.output` vs. dedicated `observation` entries.
- **`$defs.trajectoryView`** in the schema. A documentation reference describing the trajectory shape (not a separate constraint).

### Changed

- `entries[].items.properties.type.enum` extended from 8 to 9 values (added `observation`).
- Schema `$id` updated to `v1.1.json`.

### Backward compatibility

- All v1.0 files validate unchanged against v1.1.
- New fields (`task`, `outcome`, `observation`, `tool_call_id`, `correlation_id`, `duration_ms`, `error`, `attachments`) are all optional.
- Existing tools that read `action.output` continue to work.

## [1.0.0] - 2026-07-04

- Initial release: JSON Schema with 8 entry types (`user-query`, `context`, `querying`, `title`, `thought`, `action`, `answer`, `side-effect`).
- 3 readers: `opencode.py`, `minimax.py`, `antigravity.py` (+ `libre.py` for Freestyle Libre 2 glucose data).
- 1 importer: `chatgpt.py`.
- 1 exporter: `finetune.py` (Unsloth + Olive).
- 14 SOPs (SOP-001 to SOP-014) covering Libre→AgentSON, Nightscout, WhatsApp bot, TV dashboard, MedGemma fine-tuning, Juggluco, NHS FHIR, West Africa voice alerts.
- 3 example files: `antigravity_example.AgentSON`, `minimax_example.AgentSON`, `opencode_example.AgentSON`.
- Live docs at `https://andiekobbietks.github.io/AgentSON/`.
- Author: Andrea Enning (AndieKobbieTech). PRD v1.0 04 July 2026.