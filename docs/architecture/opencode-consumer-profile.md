# OpenCode Consumer Profile: Archive Capsule v1

**Status:** Experimental consumer adapter; contract tests only  
**Target:** OpenCode local server API  
**AgentSON input:** v1.2 canonical JSON session envelope  
**Implementation:** `consumers/opencode.py`

## Purpose

This profile provides a receiving-harness path for a canonical AgentSON archive. It creates an OpenCode session and stores the complete archive in one user context message using OpenCode's documented `noReply: true` behaviour.

The adapter is deliberately an **archive capsule**, not a claim that OpenCode natively understands or restores every AgentSON event primitive.

## Import behaviour

1. Load a JSON object from a path or mapping.
2. Validate the complete envelope against the repository's v1.2 JSON Schema.
3. Require a local OpenCode endpoint by default (`127.0.0.1`, `::1`, or `localhost`).
4. Create a new OpenCode session with a title identifying the source harness and source session.
5. Submit one text part containing the full ordered archive, explicitly labelled as historical and untrusted, with `noReply: true`.
6. If message insertion fails after session creation, attempt to delete the newly created empty session.
7. Return the OpenCode session ID, source identifiers, entry count, a deterministic archive digest, and declared limitations.

No model response is requested during import. Imported actions, commands, prompts and tool outputs are not executed by the adapter.

## Preserved and not preserved

| Information | Profile behaviour |
|---|---|
| Complete v1.2 archive payload | Preserved as embedded JSON text |
| Entry order and source identifiers | Preserved inside the embedded archive |
| Source provenance and extensions | Preserved inside the embedded archive |
| Native OpenCode message/event structure | Not reconstructed; archive is one user context message |
| Native OpenCode tool-call records | Not created |
| Workspace snapshot, environment and credentials | Not restored |
| Model/provider state or checkpoint | Not restored |
| Session resumption | Not supported by this profile |

The archive digest is SHA-256 over the adapter's deterministic compact JSON serialisation. It is a local integrity reference, not a signature and not proof that the source events are truthful.

## Security boundary

- Localhost is the default endpoint policy.
- A remote endpoint requires explicit `allow_remote=True` and HTTPS.
- URLs containing embedded credentials, query strings or fragments are rejected.
- The archive is treated as untrusted historical evidence.
- The context message warns the receiving model not to execute recorded actions. This warning is not a security sandbox; users must still review imported context before asking a model to act on it.
- This adapter does not import credentials or issue tool permissions.

## Verification status

The automated tests mock the OpenCode HTTP API. They verify schema rejection before network calls, session creation, no-reply context insertion, embedded archive equality, endpoint policy and best-effort cleanup after a failed insertion.

**Not yet demonstrated:** a live import into a running OpenCode instance, read-back from OpenCode's message API, or native event reconstruction. Therefore this profile is not yet C2 conformance under the project's current definition. It is an implemented receiving adapter with mocked API contract coverage.

## Usage

From a Python environment with AgentSON installed and an OpenCode server running locally:

```python
from consumers.opencode import import_archive

result = import_archive("session.agentson")
print(result["session_id"])
print(result["losses"])
```

The default endpoint is `http://127.0.0.1:4096`. Remote HTTPS use must be explicitly enabled:

```python
result = import_archive(
    "session.agentson",
    base_url="https://opencode.example.test",
    allow_remote=True,
)
```

OpenCode server API reference: https://docs.opencode.ai/docs/server/  
OpenCode SDK reference: https://docs.opencode.ai/docs/sdk/
