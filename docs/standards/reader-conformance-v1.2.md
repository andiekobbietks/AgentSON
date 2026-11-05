# Reader conformance against AgentSON v1.2

**Status:** initial audit; not a certification of lossless interchange.  
**Contract:** `spec/v1.2-entries.json` and the v1.2 JSONL stream header.  
**Preservation boundary:** `source_payload` preserves the object returned by a reader, not the vendor's original database row, protobuf bytes, or transcript bytes unless the reader itself retained them.

## Conformance matrix

| Reader | Source representation observed in repository | Canonical projection | Reader-level fields retained | Known loss / uncertainty | Evidence status |
|---|---|---|---|---|---|
| OpenCode | Legacy 1.x `session/message/part/todo`; current 2.x `session_v2/session_message/session_part/session_inbox` | `user-query`, `thought`, `answer`, `action`, `side-effect`, `system-event` | Raw session, message and part rows plus decoded JSON payloads are retained in `source_metadata` / `source_payload`; v2 inbox records are retained. Extraction opens the database read-only. | v2 blob bytes and `blob_ref` relationships are not yet exported; external tool-output files are only recovered when the inline truncation marker resolves; queued inbox semantics are preserved as source records but not replayed as user turns; unrecognised message/part types are preserved as `system-event`, not semantically interpreted. | A checked-in real OpenCode message/parts export is now loaded through the actual 1.x SQLite reader and canonical JSONL exporter. Separate synthetic SQLite integration tests exercise 1.x and the upstream 2.x table shape, including completed/error/running tools, shell, inbox, unknown message types, raw provenance and read-only enforcement. |
| Claude Code | Native JSONL transcript records with nested content blocks (`text`, `tool_use`, `tool_result`) | Reader flattens known content blocks; unknown records/blocks become `system-event` | Recognised entries retain their full native JSONL record and content block; unknown top-level records and content blocks are retained; malformed JSON lines are retained with line number and parse error; source file SHA-256 and line count are recorded. No fallback timestamp is fabricated. | Parent/child agent transcript linkage and multimodal reconstruction remain incomplete. Observation text is a 2,000-character projection, but the full native result remains in source payload. | Synthetic native JSONL fixture exercises known blocks, nested tool-result correlation, an unknown block, an unknown record and malformed line retention. Real anonymised multi-agent transcript coverage remains needed. |
| MiniMax / Mavis | SQLite `sessions`, `session_messages`, `token_usage`, and `session_peers`; message blobs include thinking and tool calls | `stream-meta`, `thought`, `action`, `observation`, `user-query`, `answer`, fallback `system-event` | Raw session, message rows, decoded message blobs, raw tool-call argument/result strings, token usage rows and peer rows are retained; SQLite access is read-only | Status codes are normalized into v1.2 action states; original integer codes remain in source payload. Source-version coverage and peer/task-tree semantics remain unverified against multiple real databases. | Synthetic SQLite fixture exercises the actual reader and asserts raw tool-call and token provenance; no captured Mavis database yet. |
| Antigravity | SQLite steps with protobuf/binary payloads, step type codes, status, format, subtrajectory flag, generation metadata | Current reader returns role/type/text/code fields; integer step types do not directly map to the v1.2 primitive enum | Original step payload bytes and trajectory/generation metadata blobs are retained as base64 with SHA-256; decoded snippets remain projections. SQLite access is read-only. | Protobuf extraction remains heuristic; integer step types are not semantically classified. Base64 preserves the bytes the reader receives, not protobuf message descriptors or linked subtrajectory databases. | Synthetic SQLite fixture asserts byte-for-byte step payload and metadata-blob preservation; no captured real protobuf fixture. |
| Chrome DevTools | Markdown conversation export; sections and fenced code/data blocks | Content-driven mapping to `observation`, `thought`, `action`, `answer`, and `side-effect` | Exact source Markdown and SHA-256 are retained once in session source metadata; each projected entry also retains its raw source section/subsection. | Tool names and event types can be inferred from prose/code. The parser's interpretation may change while the raw Markdown remains available; source attachment bytes are not embedded when the export only contains placeholders. | Synthetic Markdown fixture asserts exact raw Markdown and subsection preservation through canonical JSONL. No real user export fixture. |
| Libre / CSV | CSV readings and metadata | Sensor observations | Each valid raw row and header list are retained; rejected rows retain line number, reason and original values. | CSV quoting/line endings are not byte-preserved; naive timestamps are interpreted in the system timezone and labelled `source-local`; invalid rows are preserved as rejected evidence but excluded from metrics. | Synthetic CSV fixture asserts raw row preservation and malformed-row evidence through canonical JSONL. No real user export fixture. |

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
4. **MiniMax:** raw message/tool-call/token/peer evidence is now retained and tested against a synthetic SQLite fixture. Remaining: a captured anonymised Mavis database, broader release/schema coverage and validation of peer/task-tree semantics.
5. **OpenCode:** implemented 1.x and 2.x SQLite schema detection, real-sample execution through the production reader, completed/error/running tool-state coverage, inbox preservation, raw-row provenance, and read-only extraction. Remaining: captured full 2.x database, blob attachment handling, event-table coverage, and release-pinned source exports.
6. **Chrome DevTools:** raw Markdown and section evidence are now preserved and tested. Remaining: a real anonymised export and source attachment-byte coverage.
7. **Libre:** raw rows and malformed-row evidence are now preserved and tested. Remaining: real anonymised exports covering additional CSV dialects, units and timezone variants.

## What this batch verifies

The added tests verify that:
- OpenCode 1.x and 2.x temporary SQLite databases are read end-to-end through OpencodeReader, including session listing, messages, parts, reasoning, completed/error/running tool states, shell messages, todos/inbox records, unknown message preservation, raw provenance, read-only enforcement, and canonical JSONL schema validation;
- synthetic native-format fixtures exercise the actual Claude Code JSONL reader, Chrome DevTools Markdown parser, MiniMax SQLite reader, Antigravity SQLite reader, and Libre CSV reader, then pass their reader outputs through canonical JSONL export and schema validation;
- source evidence is asserted for MiniMax raw message/tool-call/token/peer rows, Antigravity binary step payload and metadata blobs, Chrome raw Markdown, and Libre raw/rejected CSV rows;
- MiniMax's pre-existing stream-meta header is enriched with session metadata instead of dropping token, metric and source-specific fields;
- the checked-in real OpenCode message/parts sample is loaded into a temporary 1.x SQLite database and passed through the production reader and canonical JSONL exporter (not a reimplemented test-only mapper);
- Claude Code's direct reader export path emits canonical v1.2 JSONL rather than a legacy JSON document;
- Claude Code native assistant blocks and nested tool results survive under event-level source_payload, and end-turn text is classified as an answer;
- reader-specific Antigravity session fields outside the common session envelope remain available under `source_session.source_metadata`;
- original reader-level event objects remain attached to their canonical projections as `source_payload`;
- the resulting stream validates against the v1.2 entry schema.

The OpenCode message/parts sample is a real captured source export; the SQLite container around it is temporary test scaffolding, not a captured full database. Other adapter fixtures in this batch remain synthetic and source-shaped. Tests demonstrate only the represented cases, not universal source-version compatibility. Real anonymised full database exports, blob/attachment fixtures, and broader version coverage remain necessary before claiming production interoperability.


## Privacy boundary for preserved source evidence

Native source evidence may contain personal data, credentials, private paths, or binary attachments. A canonical export is therefore still sensitive even when its event schema validates.

The JSONL-aware `PIIRedactor` now:
- recursively scans string values inside `source_payload` and `source_metadata`, including JSON-encoded native row data and preserved Markdown;
- removes non-empty opaque fields whose names end in `_base64` from a redacted copy, sets a matching `_base64_omitted` marker, and retains adjacent SHA-256 digests where present;
- preserves the original source file unless the caller explicitly chooses the same path as the redaction output.

This is a conservative omission policy, not a guarantee that all sensitive information is detected. The regex-based fallback has limited coverage; the optional model path is not a substitute for human review. Keep original native exports access-controlled, review redacted output before sharing, and do not treat a successful redaction run as proof that a file is free of personal data.
