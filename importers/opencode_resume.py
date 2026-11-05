"""Native OpenCode destination adapter using its documented HTTP API.

This adapter creates a fresh OpenCode session and queues the AgentSON packet
with resume=False, so OpenCode stores the context without starting an agent
turn or executing historical tool calls.
"""
from __future__ import annotations

import base64
import json
import os
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


class OpenCodeResumeError(RuntimeError):
    """Raised when the OpenCode session handoff cannot be completed."""


def _request(
    base_url: str,
    path: str,
    *,
    method: str = "GET",
    body: Optional[Dict[str, Any]] = None,
    timeout: float = 15.0,
) -> Any:
    url = base_url.rstrip("/") + path
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"

    username = os.environ.get("OPENCODE_SERVER_USERNAME", "opencode")
    password = os.environ.get("OPENCODE_SERVER_PASSWORD")
    if password:
        token = base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        headers["Authorization"] = f"Basic {token}"

    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read()
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise OpenCodeResumeError(
            f"OpenCode API returned HTTP {exc.code} for {method} {path}: {detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise OpenCodeResumeError(
            f"Could not reach OpenCode at {base_url}: {exc}. "
            "Start it with 'opencode serve' and check --server-url."
        ) from exc

    if not raw:
        return None
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise OpenCodeResumeError(f"OpenCode returned a non-JSON response for {path}") from exc


def create_opencode_session(
    packet: str,
    *,
    server_url: str = "http://127.0.0.1:4096",
    title: str = "AgentSON continuation",
    timeout: float = 15.0,
) -> str:
    """Create a native OpenCode session, queue context without running it, verify it.

    Uses the documented OpenCode v2 HTTP API:
      POST /api/session
      POST /api/session/{sessionID}/prompt with resume=false
      GET  /api/session/{sessionID}/message
    """
    if not isinstance(packet, str) or not packet.strip():
        raise ValueError("Continuation packet must be a non-empty string")
    if not server_url.startswith(("http://", "https://")):
        raise ValueError("OpenCode server URL must start with http:// or https://")

    _request(server_url, "/api/info", timeout=timeout)
    created = _request(
        server_url,
        "/api/session",
        method="POST",
        body={"title": title},
        timeout=timeout,
    )
    session = created.get("data", created) if isinstance(created, dict) else None
    session_id = session.get("id") if isinstance(session, dict) else None
    if not isinstance(session_id, str) or not session_id:
        raise OpenCodeResumeError("OpenCode created a response without a session ID")

    encoded_id = quote(session_id, safe="")
    _request(
        server_url,
        f"/api/session/{encoded_id}/prompt",
        method="POST",
        body={"text": packet, "resume": False},
        timeout=timeout,
    )

    messages = _request(
        server_url,
        f"/api/session/{encoded_id}/message",
        timeout=timeout,
    )
    serialised = json.dumps(messages, ensure_ascii=False, sort_keys=True)
    marker = "AgentSON continuation packet"
    if marker not in serialised:
        raise OpenCodeResumeError(
            f"OpenCode accepted the handoff for session {session_id}, but the "
            "read-back did not contain the packet marker. Inspect the session "
            "before relying on this transfer."
        )
    return session_id
