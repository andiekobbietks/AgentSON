"""
Local playground server for AgentSON Platform.

WHY: the premium tier must be visible without a cloud account. The server
uses only the standard library (``http.server``, ``json``, ``pathlib``), so
the 16-package core is untouched. It reads the *real* scan output on disk
(report.json) and serves the dashboard, the digest API and the GRC evidence
package from it — no seeded or invented numbers.

Usage:
    agentson platform serve                 # auto-finds the latest scan
    agentson platform serve --scan-dir DIR  # explicit scan folder
    agentson platform serve --port 8090
Then open http://localhost:8090/
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

SCAN_REPORT_NAME = "report.json"
SCAN_MARKDOWN_NAME = "report.md"


def find_latest_scan(base: Optional[str] = None) -> Optional[Path]:
    """Locate the most recent scan folder containing report.json."""
    roots = [Path(base)] if base else [
        Path.cwd(),
        Path.home() / "AppData" / "Local" / "Temp" / "opencode",
    ]
    best: Optional[Path] = None
    best_mtime = 0.0
    for root in roots:
        if not root.exists():
            continue
        for candidate in root.glob("**/scan-*/" + SCAN_REPORT_NAME):
            try:
                mtime = candidate.stat().st_mtime
            except OSError:
                continue
            if mtime > best_mtime:
                best_mtime = mtime
                best = candidate.parent
    return best


def load_digest(scan_dir: Path) -> Dict[str, Any]:
    report = scan_dir / SCAN_REPORT_NAME
    with open(report, encoding="utf-8") as f:
        return json.load(f)


def _severity_rows(digest: Dict[str, Any]) -> List[Dict[str, Any]]:
    counts = digest.get("by_severity", {})
    order = ("critical", "high", "medium", "low")
    return [{"severity": s, "count": counts.get(s, 0)} for s in order]


def _html_escape(text: str) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_dashboard(digest: Dict[str, Any], scan_dir: Path) -> str:
    totals = digest.get("totals", {})
    sev_rows = _severity_rows(digest)
    by_tool = digest.get("by_tool", {})
    by_cat = digest.get("by_category", {})

    sev_html = "".join(
        "<tr><td>%s</td><td class='metric'>%s</td></tr>"
        % (_html_escape(r["severity"]), r["count"])
        for r in sev_rows
    )
    tool_html = "".join(
        "<tr><td>%s</td><td>%s</td></tr>" % (_html_escape(k), v)
        for k, v in sorted(by_tool.items(), key=lambda kv: -kv[1])
    )
    cat_html = "".join(
        "<tr><td>%s</td><td>%s</td></tr>" % (_html_escape(k), v)
        for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1])
    )

    return """<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AgentSON Platform - Enterprise Compliance &amp; Audit</title>
<style>
  body { background:#0d1117; color:#e6edf3; font-family:monospace; padding:2rem; }
  h1 { color:#ffb000; border-bottom:2px solid #ffb000; padding-bottom:.5rem; }
  h2 { color:#ffb000; font-size:1.05rem; margin-top:0; }
  .card { border:1px solid #ffb000; border-radius:6px; padding:1rem; margin:1rem 0; background:#161b22; }
  .metric { font-weight:bold; color:#ffb000; }
  a { color:#5b9ef6; text-decoration:none; }
  a:hover { color:#ffb000; text-decoration:underline; }
  table { width:100%%; border-collapse:collapse; }
  th,td { text-align:left; padding:.3rem .4rem; border-bottom:1px solid #30363d; }
  .muted { color:#8b949e; font-size:.85rem; }
</style></head><body>
<h1>AgentSON Platform - Enterprise Compliance &amp; Audit</h1>
<p class="card">
  <span class="metric">%(sessions)s</span> sessions &middot;
  <span class="metric">%(entries)s</span> entries &middot;
  <span class="metric">%(findings)s</span> findings &middot;
  <span class="metric">%(high)s</span> high or critical<br>
  <span class="muted">generated %(generated)s &middot; classifier %(classifier)s &middot; scan %(scan)s</span>
</p>
<div style="display:flex;gap:2rem;flex-wrap:wrap;">
  <div class="card" style="flex:1;min-width:240px;">
    <h2>By severity</h2><table>%(sev)s</table>
  </div>
  <div class="card" style="flex:1;min-width:240px;">
    <h2>By tool</h2><table>%(tool)s</table>
  </div>
  <div class="card" style="flex:1;min-width:240px;">
    <h2>By category</h2><table>%(cat)s</table>
  </div>
</div>
<p class="card">
  <b>Premium actions:</b>
  <a href="/api/digest">/api/digest</a> &middot;
  <a href="/api/findings?severity=critical&limit=100">/api/findings</a> &middot;
  <a href="/export-evidence">GRC evidence package</a> &middot;
  <a href="/report.md">Markdown report</a>
</p>
<p class="muted">AgentSON Platform v0.1.0 &middot; Apache-2.0 core + proprietary premium modules &middot; local preview, zero telemetry</p>
</body></html>""" % {
        "sessions": totals.get("sessions", 0),
        "entries": totals.get("entries", 0),
        "findings": totals.get("findings", 0),
        "high": totals.get("high_or_critical", 0),
        "generated": _html_escape(digest.get("generated_at", "")),
        "classifier": _html_escape(digest.get("classifier", "")),
        "scan": _html_escape(str(scan_dir)),
        "sev": sev_html,
        "tool": tool_html,
        "cat": cat_html,
    }


class PlatformHandler(BaseHTTPRequestHandler):
    scan_dir: Path = Path(".")

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: Any, code: int = 200) -> None:
        body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        self._send(code, body, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802 - stdlib naming
        from urllib.parse import parse_qs, urlparse

        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        try:
            digest = load_digest(self.scan_dir)
        except (OSError, ValueError) as exc:
            self._json({"error": "scan report unreadable", "detail": str(exc)}, 500)
            return

        if route == "/":
            body = render_dashboard(digest, self.scan_dir).encode("utf-8")
            self._send(200, body, "text/html; charset=utf-8")
        elif route == "/api/digest":
            totals = dict(digest.get("totals", {}))
            self._json(
                {
                    "generated_at": digest.get("generated_at"),
                    "classifier": digest.get("classifier"),
                    "totals": totals,
                    "by_severity": digest.get("by_severity", {}),
                    "by_category": digest.get("by_category", {}),
                    "by_tool": digest.get("by_tool", {}),
                }
            )
        elif route == "/api/findings":
            findings = digest.get("findings", [])
            severity = query.get("severity", [None])[0]
            tool = query.get("tool", [None])[0]
            limit = int(query.get("limit", ["100"])[0])
            if severity:
                findings = [f for f in findings if f.get("severity") == severity]
            if tool:
                findings = [f for f in findings if f.get("tool") == tool]
            self._json({"count": len(findings), "findings": findings[:limit]})
        elif route == "/export-evidence":
            from cli.grc_export import build_evidence

            package = build_evidence(
                digest_path=str(self.scan_dir / SCAN_REPORT_NAME)
            )
            body = json.dumps(package, indent=2, ensure_ascii=False).encode("utf-8")
            self._send(200, body, "application/json; charset=utf-8")
        elif route == "/report.md":
            md = self.scan_dir / SCAN_MARKDOWN_NAME
            if not md.exists():
                self._json({"error": "report.md not found"}, 404)
                return
            self._send(200, md.read_bytes(), "text/markdown; charset=utf-8")
        else:
            self._json({"error": "not found", "path": route}, 404)

    def log_message(self, fmt: str, *args: Any) -> None:
        print("  [platform] " + fmt % args)


def serve(port: int = 8080, scan_dir: Optional[str] = None, base: Optional[str] = None) -> None:
    """Run the local preview server. Blocks until interrupted."""
    resolved = Path(scan_dir) if scan_dir else find_latest_scan(base)
    if resolved is None:
        raise SystemExit(
            "No scan found. Run first:\n"
            "  agentson platform scan --output .\n"
            "then: agentson platform serve"
        )
    if not (resolved / SCAN_REPORT_NAME).exists():
        raise SystemExit("No report.json in %s" % resolved)

    handler = type("BoundHandler", (PlatformHandler,), {"scan_dir": resolved})
    server = HTTPServer(("127.0.0.1", port), handler)
    print("")
    print("  AgentSON Platform - local preview")
    print("  http://localhost:%d/" % port)
    print("  scan: %s" % resolved)
    print("  Ctrl-C to stop")
    print("")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped")
    finally:
        server.server_close()
