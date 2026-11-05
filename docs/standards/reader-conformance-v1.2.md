# Reader conformance against AgentSON v1.2

**Status:** initial audit; not a certification of lossless interchange.  
**Contract:** `spec/v1.2-entries.json` and the v1.2 JSONL stream header.  
**Preservation boundary:** `source_payload` preserves the object returned by a reader, not the vendor's original database row, protobuf bytes, or transcript bytes unless the reader itself retained them.

## Conformance matrix

| Reader | Source representation observed in repository | Canonical projection | Reader-level fields retained | Known loss / uncertainty | Evidence status |
|---|---|---|---|---|---|
| OpenCode | SQLite session/message/part records; current parts include `reasoning` and `tool` with nested `state` | `thought`, `answer`, `action`, `user-query` | Projected reader event is copied into `source_payload`; session tool/agent metadata and selected session fields are retained | SQLite columns and message-level token/cost/model/path/finish fields are not necessarily represented in each event. The existing real sample covers one assistant message, not a full database export. | Real message/parts fixture exists; canonical serializer round-trip regression added. |
| Claude Code | Native JSONL transcript records with nested content blocks (`text`, `tool_use`, `tool_result`) | Reader flattens transcript blocks to AgentSON entries | Flattened reader events are eligible for `source_payload`; project/session metadata is retained only to the extent the reader returns it | Native block boundaries, tool-result pairing, parent/child agent links, and unhandled record types may be flattened or omitted before the serializer sees them. The reader's own `export_session` method writes a legacy JSON document directly; use the canonical CLI export path for v1.2 output. | Source format and reader implementation inspected; no committed native transcript fixture in this conformance batch. |
| MiniMax / Mavis | SQLite `sessions`, `session_messages`, `token_usage`, and `session_peers`; message blobs include thinking and tool calls | Reader already emits v1.2-style primitives including `stream-meta`, `thought`, `action`, `observation`, and `user-query` | Existing stream header and source event records are retained; reader-level metadata is represented in its stream header | Token usage, peer/task-tree details, raw tool-call argument strings, and source status codes need explicit field-by-field fixture assertions. Existing stream passthrough is not a substitute for source-semantic validation. | Implementation inspected; current CLI-path regression is synthetic, not a captured Mavis database fixture. |
| Antigravity | SQLite steps with protobuf/binary payloads, step type codes, status, format, subtrajectory flag, generation metadata | Current reader returns role/type/text/code fields; integer step types do not directly map to the v1.2 primitive enum | Reader-returned event object retained in `source_payload`; newly retained session `version`, `variant`, and `metrics` under `source_session.source_metadata` | Reader currently stamps each step with `datetime.now()`, which is an invented observation time, not a source timestamp. Protobuf extraction is heuristic and may discard binary structure before serialization. Integer step types are not semantically classified by the generic serializer. | Synthetic reader-shape regression added for session metadata and raw reader event retention; no real protobuf fixture. |
| Chrome DevTools | Markdown conversation export; sections and fenced code/data blocks | Content-driven mapping to `observation`, `thought`, `action`, `answer`, and `side-effect` | Structured attachments and parsed fields survive in reader output and are copied into `source_payload` | Original Markdown layout, section headings, and exact formatting are not byte-preserved by the current reader projection. Tool names and event types can be inferred from prose/code. Reader currently declares a v1.1 schema URI. | Reader implementation inspected; no captured export fixture in this conformance batch. |
| Libre / CSV | CSV readings and metadata | Sensor observations | Reader-returned row/event fields can be retained | CSV dialect, source units, timezone assumptions, and row-level quality metadata need fixture-based checks. | Not audited in this batch. |

## Required classification vocabulary

Each mapping should be classified independently at the **field** level:

- **Preserved:** same source value and meaning survive in the canonical event or source payload.
- **Normalized:** representation changes, but meaning and value remain recoverable (for example, ISO timestamp to Unix milliseconds).
- **Inferred:** value or semantic type is assigned by reader/serializer logic rather than explicit source evidence.
- **Unavailable:** source does not provide the field, or the reader does not expose it.
- **Lost-before-serializer:** source information is discarded by the reader, so `source_payload` cannot recover it.
- **Unverified:** no representative fixture or assertion yet.

Do not label a whole reader "lossless" based on schema validation. A stream can be valid JSONL and still contain inferred event classifications or upstream data loss.

## Immediate remediation priorities

1. **Antigravity timestamps:** stop using wall-clock `datetime.now()` as an event timestamp. Use source-provided timestamps only; otherwise omit `timestamp` and record the extraction time separately as export metadata.
2. **Antigravity step semantics:** map known step codes through a documented versioned table. Unknown codes should remain explicit unknown source events with their integer code in `source_payload`, not be treated as a meaningful generic assistant action.
3. **Claude Code raw blocks:** retain native content blocks and transcript record identity before flattening, including tool-use/result correlation and subagent references.
4. **MiniMax:** add a fixture containing token usage, peer relationships, thinking, tool-call arguments/results, and non-success status codes.
5. **OpenCode:** extend the existing sample to cover user messages, assistant text, multiple tool states, failed/in-progress tools, message metadata, and session-level todos.
6. **Chrome DevTools:** add a real Markdown export fixture with observations, actions, answer, side effect, attachments, and export timestamp.
7. **Libre:** add representative CSV fixtures for units, timestamps/timezones, missing readings, and malformed rows.

## What this batch verifies

The added tests verify that:
- a real OpenCode message/parts sample already in the repository can be projected into canonical JSONL using the reader-shaped events;
- reader-specific Antigravity session fields outside the common session envelope remain available under `source_session.source_metadata`;
- original reader-level event objects remain attached to their canonical projections as `source_payload`;
- the resulting stream validates against the v1.2 entry schema.

The OpenCode test currently builds the expected reader-level event shape from the fixture rather than invoking a live SQLite reader. It is a serializer/fixture regression, not end-to-end proof of the OpenCode adapter. This limitation is intentional and explicit until a reusable database fixture exercises the actual reader.
