# OpenCode storage compatibility and fidelity

**Status:** implementation support for legacy 1.x and current 2.x SQLite layouts; not a lossless OpenCode archive.
**Reader:** `readers/opencode.py`
**Canonical output:** AgentSON v1.2 JSONL with the original `.agentson` extension.

## Source schema references

The 2.x table layout is checked against OpenCode's upstream Drizzle definitions:

- [OpenCode session SQL tables](https://github.com/anomalyco/opencode/blob/dev/packages/core/src/session/sql.ts): `session_v2`, `session_message`, `session_part`, `session_inbox`, `blob`, and `blob_ref`.
- [OpenCode session message types](https://github.com/anomalyco/opencode/blob/dev/packages/schema/src/session-message.ts): user, assistant, synthetic, system, skill, shell, compaction, idle, and assistant content blocks.
- [OpenCode CLI export documentation](https://dev.opencode.ai/v2/docs/cli/commands/): native session export is a JSON transfer format; this reader currently reads SQLite directly rather than using CLI export as its transport.

The older 1.x storage generation uses `session`, `message`, `part`, and optional `todo` tables. The reader detects the generation from table presence and does not assume that 1.x and 2.x have interchangeable column names.

## Supported layouts

| Generation | Session table | Transcript table | Content table | Additional table |
|---|---|---|---|---|
| 1.x | `session` | `message` | `part` | optional `todo` |
| 2.x | `session_v2` | `session_message` | `session_part` | optional `session_inbox` |

The reader opens file-backed databases in SQLite read-only mode. This avoids schema migrations, writes, or accidental creation of a missing database during extraction. WAL-mode databases should be copied consistently before offline archival if the source application is actively writing; this reader does not itself create a SQLite backup snapshot.

## Mapping and preservation

| OpenCode source | AgentSON projection | Fidelity boundary |
|---|---|---|
| 1.x user text part | `user-query` | Raw message row, raw part row and decoded JSON are retained. |
| 1.x assistant text part | `answer` | Same; the reader treats each text part as an answer projection. |
| 1.x reasoning part | `thought` | Native part payload retained. |
| 1.x `tool` part | `action` | Tool name, input, call ID, state and output retained in source payload; status normalized for the canonical field. |
| 1.x `tool-invocation` | `action` | Legacy fallback retained; native source shape retained. |
| 1.x todo row | `side-effect` | Raw todo row retained; no event timestamp is invented. |
| 2.x user message | `user-query` | Full message row and decoded data retained; attachments remain source-native. |
| 2.x assistant text/reasoning part | `answer` / `thought` | Full part row and decoded data retained. |
| 2.x assistant tool part | `action` | Tool ID/call ID, state, input, content and metadata retained in source payload; status normalized. |
| 2.x shell message | `action` | Command, output, status and raw message retained. |
| 2.x synthetic/system/skill/compaction/idle and future message types | `system-event` | Raw type and payload retained; no unsupported semantics are guessed. |
| 2.x inbox row | `system-event` | Raw payload and delivery metadata retained; it is not replayed as a delivered user turn. |

Every projected event retains a `source_payload` containing the SQLite row and decoded JSON. The session header retains the raw session row under `source_session.source_metadata.session_row`, plus the detected schema generation. This is decoded-row preservation, not a byte-for-byte copy of the database file or its WAL.

## Test evidence

- `tests/test_opencode_real_sample.py` loads the checked-in real OpenCode message/parts sample into a temporary 1.x SQLite container, then invokes the production reader and canonical JSONL exporter.
- `tests/test_reader_conformance_fixtures.py` builds a 1.x fixture and a 2.x fixture and tests actual reader entry points, including completed, failed and running tools, shell messages, inbox records, unknown message types, provenance and read-only enforcement.
- Both paths validate the resulting stream against the v1.2 entry schema.

The 2.x fixture is synthetic and based on the upstream schema definitions; it is not a captured full OpenCode 2.x database. The 1.x real sample is a captured message/parts export wrapped in a temporary SQLite database; it is not a captured full database.

## Known gaps (do not claim lossless interchange)

1. **Blob attachments:** `blob` and `blob_ref` are not currently loaded. Binary image/file bytes and the full relationship graph are not represented in the canonical projection.
2. **External tool output:** the legacy inline truncation marker is resolved when its referenced file exists. A missing or expired sidecar leaves the source preview only. 2.x `metadata.outputPath` and shell sidecar references need explicit versioned handling.
3. **Event table:** the 2.x event/event-sequence tables are not imported. The transcript message/part records remain the primary source for this reader.
4. **Inbox semantics:** queued/steered prompts are preserved as inbox source records, but delivery/retry/cancel semantics are not reconstructed as normal user turns.
5. **Subagent/session graph:** `parent_id`, fork metadata and cross-session references survive in the raw session row, but the reader does not recursively export child sessions or create canonical hand-off edges.
6. **Unknown types:** future message/part types are retained as `system-event` with source payload. Their semantics remain unknown until a versioned mapping and fixture are added.
7. **Version coverage:** the v2 synthetic fixture follows the upstream `dev` SQL/type definitions observed during this change. A captured database from a pinned released OpenCode version is still needed for release-level assurance.
8. **Snapshot and state data:** session snapshots, file diffs, permissions, revert state, instruction state and project/workspace metadata are retained only where present in the session row; related tables are not yet traversed.

## Acceptance rule

Do not label OpenCode "lossless" or "fully compatible" solely because the exported JSONL validates. A compatibility claim must name the source release/schema generation, fixture provenance, tested record types, and remaining unrepresented data. Retain the original database or native CLI export whenever exact reconstruction matters.
