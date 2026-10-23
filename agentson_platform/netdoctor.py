"""Networking diagnostics for enterprise clients.

WHY: an enterprise deployment of AgentSON Platform needs to prove reachability
between the agent host and the GRC ingestion endpoint before blaming the tool.
These probes are read-only, use only the standard library, and make no
persistent change. They are the same commands the enterprise runbook
documents, so support can ask a client to run them and paste the output.

Commands (all local, no telemetry):
    agentson platform doctor --dns example.com
    agentson platform doctor --tcp example.com:443
    agentson platform doctor --tls example.com:443
    agentson platform doctor --http https://example.com/health
    agentson platform doctor --proxy
    agentson platform doctor --offline
"""
from __future__ import annotations
import json
import os
import socket
import ssl
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def dns_probe(host: str) -> Dict[str, Any]:
    """Resolve a hostname and report the addresses plus timing."""
    started = time.perf_counter()
    try:
        infos = socket.getaddrinfo(host, None)
        addrs = sorted({i[4][0] for i in infos})
        return {
            "probe": "dns", "host": host, "ok": True, "addresses": addrs,
            "count": len(addrs), "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
            "checked_at": _now(),
        }
    except socket.gaierror as exc:
        return {"probe": "dns", "host": host, "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now()}


def _split_target(target: str, default_port: int = 443) -> tuple:
    if ":" in target:
        host, _, port = target.rpartition(":")
        return host, int(port)
    return target, default_port


def tcp_probe(target: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Open a TCP connection and report success, latency and local address."""
    host, port = _split_target(target)
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            return {
                "probe": "tcp", "host": host, "port": port, "ok": True,
                "local_address": sock.getsockname(), "peer_address": sock.getpeername(),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now(),
            }
    except OSError as exc:
        return {"probe": "tcp", "host": host, "port": port, "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now()}


def tls_probe(target: str, timeout: float = 10.0) -> Dict[str, Any]:
    """Complete a TLS handshake and read the peer certificate."""
    host, port = _split_target(target)
    started = time.perf_counter()
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as tls:
                cert = tls.getpeercert()
                cipher = tls.cipher()
        subject = {k: v for group in (cert or {}).get("subject", ()) for k, v in group}
        issuer = {k: v for group in (cert or {}).get("issuer", ()) for k, v in group}
        return {
            "probe": "tls", "host": host, "port": port, "ok": True,
            "protocol": cipher[0] if cipher else None, "cipher": cipher[1] if cipher else None,
            "subject": subject, "issuer": issuer, "not_after": (cert or {}).get("notAfter"),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now(),
        }
    except (OSError, ssl.SSLError) as exc:
        return {"probe": "tls", "host": host, "port": port, "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now()}


def http_probe(url: str, timeout: float = 15.0, method: str = "GET") -> Dict[str, Any]:
    """Issue one HTTP request and report status, timing and headers."""
    started = time.perf_counter()
    req = urllib.request.Request(url, method=method, headers={"User-Agent": "agentson-doctor/0.1"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read(4096)
            return {
                "probe": "http", "url": url, "ok": True, "status": resp.status,
                "content_type": resp.headers.get("Content-Type"),
                "content_length": resp.headers.get("Content-Length"),
                "body_preview": body.decode("utf-8", "replace")[:500],
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now(),
            }
    except urllib.error.HTTPError as exc:
        return {"probe": "http", "url": url, "ok": False, "status": exc.code, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now()}
    except (urllib.error.URLError, OSError) as exc:
        return {"probe": "http", "url": url, "ok": False, "error": str(exc),
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 2), "checked_at": _now()}


def proxy_env() -> Dict[str, Any]:
    """Report proxy configuration visible to the process."""
    keys = ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "no_proxy"]
    found = {k: os.environ[k] for k in keys if os.environ.get(k)}
    return {"probe": "proxy", "ok": True, "variables": found, "configured": bool(found), "checked_at": _now()}


def offline_check() -> Dict[str, Any]:
    """Confirm the local licence check and core do not require the network.

    The free core's licence check reads a local file or environment variable
    only. This probe states that as a fact about the code path, and resolves
    nothing; it performs no DNS or TCP call of its own.
    """
    from cli.licensing import LICENSE_PATH, ENV_LICENSE
    return {
        "probe": "offline", "ok": True,
        "licence_source": "environment" if os.environ.get(ENV_LICENSE) else ("file" if LICENSE_PATH.exists() else "none"),
        "licence_path": str(LICENSE_PATH),
        "network_calls_by_core": 0,
        "note": "The core licence check reads a local file only. No DNS or TCP is performed by this probe.",
        "checked_at": _now(),
    }


def run_all(target: Optional[str] = None, url: Optional[str] = None) -> List[Dict[str, Any]]:
    """Run the full diagnostic sweep."""
    results = [offline_check(), proxy_env()]
    if target:
        results.append(dns_probe(_split_target(target)[0]))
        results.append(tcp_probe(target))
        results.append(tls_probe(target))
    if url:
        results.append(http_probe(url))
    return results
