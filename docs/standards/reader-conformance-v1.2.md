# Reader conformance against AgentSON v1.2

**Status:** initial audit; not a certification of lossless interchange.  
**Contract:** `spec/v1.2-entries.json` and the v1.2 JSONL stream header.  
**Preservation boundary:** `source_payload` preserves the object returned by a reader, not the vendor's original database row, protobuf bytes, or transcript bytes unless the reader itself retained them.

## Conformance matrix

| Reader | Source representation observed in repository | Canonical projection | Reader-level fields retained | Known loss / uncertainty | Evidence status |
|---|---|---|---|---|---|
| OpenCode | SQLite session/message/part records; current parts include `reasoning` and `tool` with nested `state` | `thought`, `answer`, `action`, `user-query` | Projected reader event is copied into `source_payload`; session tool/agent metadata and selected session fields are retained | SQLite columns and message-level token/cost/model/path/finish fields are not necessarily represented in each event. The existing real sample covers one assistant message, not a full database export. | Synthetic SQLite database now exercises the actual OpenCode reader end-to-end: session/message/part/todo queries, list_sessions, reasoning, tool state, text, metadata and canonical JSONL validation. It is not a captured production database. |
| Claude Code | Native JSONL transcript records with nested content blocks (`text`, `tool_use`, `tool_result`) | Reader flattens transcript blocks to AgentSON entries | Flattened reader events are eligible for `source_payload`; project/session metadata is retained only to the extent the reader returns it | Native block boundaries and tool-result pairing are retained for the tested content blocks. Parent/child agent links, non-text multimodal payloads, and unhandled record types still need explicit coverage; the reader's 2,000-character observation preview is still a projection limit, though the raw block is retained. The reader's direct `export_session` path has now been routed through the canonical v1.2 serializer and has a regression test. | Synthetic native JSONL fixture now exercises the actual reader, including assistant thinking, tool-use, nested user-message tool-result correlation, and end-turn answer classification. Native source blocks are retained in each projected event's source_payload; fixture provenance and limits are documented in tests/fixtures/README.md. |
| MiniMax / Mavis | SQLite `sessions`, `session_messages`, `token_usage`, and `session_peers`; message blobs include thinking and tool calls | Reader already emits v1.2-style primitives including `stream-meta`, `thought`, `action`, `observation`, and `user-query` | Existing stream header and source event records are retained; reader-level metadata is represented in its stream header | Token usage, peer/task-tree details, raw tool-call argument strings, and source status codes need explicit field-by-field fixture assertions. Existing stream passthrough is not a substitute for source-semantic validation. | Implementation inspected; current CLI-path regression is synthetic, not a captured Mavis database fixture. |
| Antigravity | SQLite steps with protobuf/binary payloads, step type codes, status, format, subtrajectory flag, generation metadata | Current reader returns role/type/text/code fields; integer step types do not directly map to the v1.2 primitive enum | Reader-returned event object retained in `source_payload`; newly retained session `version`, `variant`, and `metrics` under `source_session.source_metadata` | The reader previously stamped each step with `datetime.now()`; this batch removes those fabricated event timestamps and records extraction time as session metadata. Protobuf extraction remains heuristic and may discard binary structure before serialization. Integer step types are not semantically classified by the generic serializer. | Synthetic reader-shape regression added for session metadata and raw reader event retention; no real protobuf fixture. |
| Chrome DevTools | Markdown conversation export; sections and fenced code/data blocks | Content-driven mapping to `observation`, `thought`, `action`, `answer`, and `side-effect` | Structured attachments and parsed fields survive in reader output and are copied into `source_payload` | Original Markdown layout, section headings, and exact formatting are not byte-preserved by the current reader projection. Tool names and event types can be inferred from prose/code. Reader currently declares a v1.1 schema URI. | Synthetic Markdown fixture now exercises the actual parser and canonical export, including image attachment, action and answer cases. No real user export fixture. |
| Libre / CSV | CSV readings and metadata | Sensor observations | Reader-returned row/event fields can be retained | CSV dialect, source units, timezone assumptions, and row-level quality metadata need fixture-based checks. | Synthetic CSV fixture now exercises the actual parser and canonical export for CGM/manual source, reading type and low/normal/high status. No real user export fixture. |

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

1. **Antigravity timestamps:** implemented in this batch. The reader now omits event timestamps when the source does not expose them and records extraction time in session metadata.
2. **Antigravity step semantics:** map known step codes through a documented versioned table. Unknown codes should remain explicit unknown source events with their integer code in `source_payload`, not be treated as a meaningful generic assistant action.
3. **Claude Code raw blocks:** implemented for user, assistant text/thinking, tool-use, tool-result, and summary records. Remaining work is subagent transcript linkage, multimodal blocks, and unhandled transcript variants.
4. **MiniMax:** add a fixture containing token usage, peer relationships, thinking, tool-call arguments/results, and non-success status codes.
5. **OpenCode:** extend the existing sample to cover user messages, assistant text, multiple tool states, failed/in-progress tools, message metadata, and session-level todos.
6. **Chrome DevTools:** add a real Markdown export fixture with observations, actions, answer, side effect, attachments, and export timestamp.
7. **Libre:** add representative CSV fixtures for units, timestamps/timezones, missing readings, and malformed rows.

## What this batch verifies

The added tests verify that:
- a temporary OpenCode SQLite database is read end-to-end through OpencodeReader, including session listing, messages, parts, reasoning, tool state, todos, and canonical JSONL schema validation;
- synthetic native-format fixtures exercise the actual Claude Code JSONL reader, Chrome DevTools Markdown parser, MiniMax SQLite reader, Antigravity SQLite reader, and Libre CSV reader, then pass their reader outputs through canonical JSONL export and schema validation;
- MiniMax's pre-existing stream-meta header is enriched with session metadata instead of dropping token, metric and source-specific fields;
- a real OpenCode message/parts sample already in the repository can be projected into canonical JSONL using the reader-shaped events;
- Claude Code's direct reader export path emits canonical v1.2 JSONL rather than a legacy JSON document;
- Claude Code native assistant blocks and nested tool results survive under event-level source_payload, and end-turn text is classified as an answer;
- reader-specific Antigravity session fields outside the common session envelope remain available under `source_session.source_metadata`;
- original reader-level event objects remain attached to their canonical projections as `source_payload`;
- the resulting stream validates against the v1.2 entry schema.

All newly added reader fixtures are synthetic and source-shaped, not captured production exports. They demonstrate the adapter paths exercised, not universal source-version compatibility. The OpenCode test still builds reader-shaped events from its existing message/parts fixture rather than invoking the SQLite reader end-to-end. Real anonymised exports and broader version coverage remain necessary before claiming production interoperability.
