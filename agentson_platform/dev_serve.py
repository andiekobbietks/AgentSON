"""AgentSON dev mode — stdlib supervisor (like npm run dev).

WHY: the user asked whether it runs like npm dev. The supervisor watches
*.py under cli/, agentson_platform/, readers/ for mtime changes, restarts
the server process, and prints a dev banner with current file hashes.
No external watcher (watchdog) — keeps core at 16 packages.
"""
from __future__ import annotations
import os, time, sys, subprocess, signal, hashlib
from pathlib import Path

WATCH_DIRS = ["cli", "agentson_platform", "readers"]
POLL = 1.0

def _hashes() -> str:
    h = hashlib.md5()
    for d in WATCH_DIRS:
        root = Path(__file__).parent.parent / d
        if not root.exists():
            continue
        for p in sorted(root.rglob("*.py")):
            try:
                h.update(str(p.stat().st_mtime).encode())
                h.update(p.read_bytes()[:4096])
            except Exception:
                pass
    return h.hexdigest()[:12]


def serve_watch(port: int = 8090, scan_dir=None) -> None:
    print("  AgentSON dev serve — watching .py files (poll %.1fs)" % POLL)
    proc = None
    last = _hashes()
    while True:
        cur = _hashes()
        if cur != last:
            print("  [dev] file change detected — restarting server (hash %s -> %s)" % (last, cur))
            last = cur
            if proc is not None:
                try:
                    proc.send_signal(signal.SIGTERM)
                    proc.wait(timeout=3)
                except Exception:
                    proc.kill()
            cmd = [sys.executable, "-m", "agentson_platform.server", "--port", str(port)]
            if scan_dir:
                cmd += ["--scan-dir", str(scan_dir)]
            proc = subprocess.Popen(cmd, cwd=str(Path(__file__).parent.parent))
        else:
            if proc is None:
                cmd = [sys.executable, "-m", "agentson_platform.server", "--port", str(port)]
                if scan_dir:
                    cmd += ["--scan-dir", str(scan_dir)]
                proc = subprocess.Popen(cmd, cwd=str(Path(__file__).parent.parent))
                print("  [dev] server started (pid %d) on port %d" % (proc.pid, port))
        time.sleep(POLL)
