# OpenCode Consumer Profile: Archive Capsule v1

**Status:** Experimental consumer adapter; live OpenCode CLI 2.2.5 archive-capsule integration test passed  
**Target:** OpenCode HTTP API v2 (pinned CI target: `@opencode/cli@2.2.5`)  
**AgentSON input:** v1.2 canonical JSON session envelope  
**Implementation:** `consumers/opencode.py`

## Purpose

This profile provides a receiving-harness path for a canonical AgentSON archive. It creates an OpenCode session and stores the complete archive in one synthetic message. It uses the v2 synthetic-message endpoint with `delivery: "queue"` and `resume: false`, which admits the message without scheduling the agent loop.

The adapter is deliberately an **archive capsule**, not a claim that OpenCode natively understands or restores every AgentSON event primitive.

## Import behaviour

1. Load a JSON object from a path or mapping.
2. Validate the complete envelope against the repository's v1.2 JSON Schema.
3. Require a local OpenCode endpoint by default (`127.0.0.1`, `::1`, or `localhost`).
4. Create a new session using `POST /api/session`.
5. Submit one synthetic message to `POST /api/session/{sessionID}/synthetic`, setting `delivery: "queue"` and `resume: false`.
6. If message insertion fails after session creation, attempt to delete the newly created empty session.
7. Return the OpenCode session ID, source identifiers, entry count, a deterministic archive digest, and declared limitations.
8. Verify read-back from `GET /api/session/{sessionID}/inbox`, extracting the synthetic message and comparing the embedded archive and digest.

No model response is requested during import. Imported actions, commands, prompts and tool outputs are not executed by the adapter. The `resume: false` API behaviour is the no-execution control for this profile.

## Preserved and not preserved

| Information | Profile behaviour |
|---|---|
| Complete v1.2 archive payload | Preserved as embedded JSON text in one synthetic message |
| Entry order and source identifiers | Preserved inside the embedded archive |
| Source provenance and extensions | Preserved inside the embedded archive |
| OpenCode native message history | One queued synthetic inbox item is created; it becomes transcript context only when delivered. The source event timeline is not reconstructed |
| Native OpenCode tool-call records | Not created |
| Workspace snapshot, environment and credentials | Not restored |
| Model/provider state or checkpoint | Not restored |
| Session resumption | Not supported by this profile |

The archive digest is SHA-256 over the adapter's deterministic compact JSON serialisation. It is a local integrity reference, not a signature and not proof that the source events are truthful.

## Security boundary

- Localhost is the default endpoint policy.
- OpenCode v2 protects its server with HTTP Basic authentication. Supply the server password through the `password` argument; the adapter sends it in the Authorization header and never embeds it in the URL.
- A remote endpoint requires explicit `allow_remote=True` and HTTPS.
- URLs containing embedded credentials, query strings or fragments are rejected.
- The archive is treated as untrusted historical evidence.
- The synthetic message explicitly labels the embedded archive as untrusted historical data.
- The result reports `immediate_agent_loop_started: false` and `future_model_context_exposure: true`.
- The v2 synthetic-message request uses `resume: false`; this prevents immediate agent-loop execution during import. However, OpenCode stores the synthetic message as session content and it can enter model context on a later turn. The archive is therefore not an isolated vault and the warning text is not a security boundary. Do not import archives containing untrusted instructions into a session that will later be used for autonomous work unless that future context exposure is acceptable.
- This warning and API flag are not a security sandbox for later user interactions. Users must still review imported context before asking a model to act on it.
- This adapter does not import credentials or issue tool permissions.

## Verification status

Automated mock tests verify schema rejection, v2 session creation, synthetic-message insertion with `resume: false`, archive read-back comparison, endpoint restrictions, best-effort cleanup and explicit future-model-context exposure.

A live integration test passed against OpenCode CLI 2.2.5. It started a real server with Basic authentication, imported the synthetic conformance fixture, read the queued synthetic item back through the v2 inbox API, compared the embedded JSON and digest, and deleted the test session. The recorded archive digest was `60c88f52174f7fa2a76a5eca11e0443a4113eac4cfc95d903f1fb95a73a1ceb3`.

A passing live test establishes archive-capsule storage fidelity against that OpenCode version. It does **not** establish native event reconstruction or session resumption. It is not, by itself, full semantic C2 conformance: the source producer must also be exercised end-to-end with a version-identified source session and semantic comparison.

## Usage

From a Python environment with AgentSON installed and an OpenCode v2 server running locally:

```python
from consumers.opencode import import_archive, verify_import

archive = "session.agentson"
import os

server_password = os.environ["OPENCODE_PASSWORD"]
result = import_archive(archive, password=server_password)
verification = verify_import(result, archive, password=server_password)
assert verification["verified"]
print(result["session_id"])
print(result["losses"])
```

The default endpoint is `http://127.0.0.1:4096`. Remote HTTPS use must be explicitly enabled:

```python
result = import_archive(
    "session.agentson",
    base_url="https://opencode.example.test",
    allow_remote=True,
    password=os.environ["OPENCODE_PASSWORD"],
)
```

## Upstream API references

- OpenCode v2 HTTP API: https://dev.opencode.ai/v2/docs/api
- OpenCode CLI: https://dev.opencode.ai/v2/docs/cli/
- OpenCode server: https://docs.opencode.ai/docs/server/
