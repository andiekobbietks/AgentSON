# OpenCode Consumer Profile

**Status:** Experimental  
**Target:** OpenCode CLI 2.2.5 HTTP API v2  
**Evidence boundary:** Archive-capsule storage/read-back test; not native reconstruction or session resumption.

## Purpose

The OpenCode consumer provides a first destination-side proof of concept for transferring an AgentSON archive into a newly created OpenCode session. It is separate from the OpenCode source reader.

## Import flow

1. Validate the source archive and supported v1.2 representation.
2. Validate the configured destination endpoint and authentication settings.
3. Create a new OpenCode session through its documented v2 API.
4. Queue the selected context packet and complete archive as a synthetic inbox item with delivery set to queue and resume set to false.
5. Read the inbox item back and compare the recovered archive and SHA-256 digest.
6. Attempt cleanup on failure where the API permits it.

## Safety boundary

- The adapter does not start an agent turn or replay historical tool calls during import.
- The queued archive may enter model context if a user later resumes work in that session.
- Imported content is untrusted. Review it for credentials, personal data and embedded instructions before transfer.
- Pattern-based redaction is not a complete detector.
- Basic-auth credentials must be sent in the Authorization header and must not be embedded in URLs.
- Remote targets require explicit opt-in and HTTPS; use localhost by default.
- A successful digest read-back proves that the tested destination stored the same archive bytes. It does not prove source authenticity, semantic understanding, native event reconstruction or checkpoint restoration.

## Verification and limitations

The PR #62 branch records a pinned OpenCode CLI 2.2.5 live integration test. Its ChatGPT-shaped source fixture is synthetic. This test demonstrates the adapter pipeline and archive-capsule read-back for that version; it is not a real-source C2 semantic conformance result.

Native OpenCode message/tool reconstruction, workspace state restoration and C4 resumption remain unclaimed. API changes may invalidate the profile; retest against each supported release.

## Related documents

- ADR-025: Cross-Harness Context Continuation
- Session Interoperability Architecture
- Cross-Harness Conformance Test Plan
- Reader Conformance Matrix
