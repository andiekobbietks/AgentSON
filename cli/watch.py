"""
AgentSON watch — persistent adoption monitor.

Polls GitHub (and PyPI, if published) for signals that someone is
actually engaging with the repository: new forks, new stars, new
watchers, clone/view trend. State persists between runs, so only
*changes* are reported — not the same 0 every time.

Why this exists
---------------
The question "are bots scraping my repo?" is unanswerable. GitHub
exposes no crawl logs, no per-visitor identity, no scrape hits. That
ceiling applies to everyone, including Google.

What IS observable is legitimate adoption: forks, stars, watchers,
clone counts. Those are the signals that matter for CodeSupply
reporting — they tell you whether anyone has started using the work.

Subcommands
-----------
    agentson watch status       show current counts + last poll time
    agentson watch check        poll once, report changes, save state
    agentson watch loop         poll forever at an interval
    agentson watch install      register as a scheduled task / cron job
    agentson watch uninstall    remove the scheduled task
    agentson watch log          print the event log

Stdlib only — no new dependencies.
"""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

STATE_DIR = Path.home() / ".agentson"
STATE_PATH = STATE_DIR / "watch_state.json"
LOG_PATH = STATE_DIR / "watch.log"
TASK_NAME = "AgentSON Watch"

API = "https://api.github.com"
PYPI_STATS = "https://pypistats.org/api/packages/{name}/recent"
UA = "AgentSON-watch"


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def emit(msg, quiet=False):
    """Write a line to the event log and return it."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{now_iso()}] {msg}"
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")
    if not quiet:
        print(line)
    return line


def gh(path, token=None, accept="application/vnd.github+json"):
    """GET a GitHub API path. Returns parsed JSON, or None on failure."""
    headers = {"User-Agent": UA, "Accept": accept}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = Request(f"{API}{path}", headers=headers)
    try:
        with urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        note = f"GitHub {exc.code} on {path}"
        if exc.code == 403:
            note += " (rate limit? set GITHUB_TOKEN)"
        print(f"  warn: {note}", file=sys.stderr)
    except URLError as exc:
        print(f"  warn: network error on {path}: {exc.reason}", file=sys.stderr)
    return None


def http_json(url, accept="application/json"):
    req = Request(url, headers={"User-Agent": UA, "Accept": accept})
    try:
        with urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (HTTPError, URLError) as exc:
        print(f"  warn: {url} -> {exc}", file=sys.stderr)
        return None


def detect_repo():
    """Read the origin remote; fall back to the known public repo."""
    try:
        out = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True, text=True, timeout=10,
        )
        if out.returncode == 0:
            m = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?$", out.stdout.strip())
            if m:
                return f"{m.group(1)}/{m.group(2)}"
    except (OSError, subprocess.SubprocessError):
        pass
    return "andiekobbietks/AgentSON"


def load_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print("  warn: state file unreadable, starting fresh", file=sys.stderr)
    return {}


def save_state(state):
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(
        json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8"
    )


# --------------------------------------------------------------------------
# Pollers. Each returns None on failure, else a JSON-safe fragment.
# --------------------------------------------------------------------------

def poll_counts(repo, token):
    data = gh(f"/repos/{repo}", token)
    if not data:
        return None
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "watchers": data.get("subscribers_count", 0),
        "open_issues": data.get("open_issues_count", 0),
        "pushed_at": data.get("pushed_at"),
        "size_kb": data.get("size"),
    }


def poll_forks(repo, token, cap=100):
    data = gh(f"/repos/{repo}/forks?per_page={cap}&sort=oldest", token)
    if data is None:
        return None
    return [
        {
            "id": f["id"],
            "full_name": f["full_name"],
            "owner": f["owner"]["login"],
            "created_at": f["created_at"],
        }
        for f in data
    ]


def poll_stargazers(repo, token, cap=100):
    """Star list. Requires auth — GitHub returns 401 on the stargazers
    endpoint without a token (both media types). The star *count* is
    still public via poll_counts; only the per-user list needs auth.
    Returns None when unavailable so the caller can skip cleanly."""
    if not token:
        return None
    data = gh(
        f"/repos/{repo}/stargazers?per_page={cap}",
        token,
        accept="application/vnd.github.star+json",
    )
    if data is None:
        return None
    return [
        {"user": s["login"], "starred_at": s.get("starred_at")}
        for s in data
    ]


def poll_traffic(repo, token):
    """Clone/view counts. Requires a token with push access."""
    if not token:
        return None
    clones = gh(f"/repos/{repo}/traffic/clones", token)
    views = gh(f"/repos/{repo}/traffic/views", token)
    if not clones and not views:
        return None
    return {
        "clones_total": (clones or {}).get("count", 0),
        "clones_unique": (clones or {}).get("uniques", 0),
        "views_total": (views or {}).get("count", 0),
        "views_unique": (views or {}).get("uniques", 0),
        "window_days": 14,
    }


def poll_pypi(name):
    """Monthly downloads. Returns None if unpublished or unreachable."""
    if not name:
        return None
    data = http_json(PYPI_STATS.format(name=name))
    if not data:
        return None
    return {
        "downloads_last_month": data.get("data", {}).get("last_month", {}).get("downloads"),
        "last_day": data.get("data", {}).get("last_day", {}).get("downloads"),
    }


# --------------------------------------------------------------------------
# Diffing
# --------------------------------------------------------------------------

def diff(prev, curr):
    """Human-readable events for anything that changed since last poll."""
    events = []
    prev_stars = {s["user"] for s in (prev.get("stargazers") or [])}
    prev_forks = {f["id"] for f in (prev.get("forks") or [])}

    for s in (curr.get("stargazers") or []):
        if s["user"] not in prev_stars:
            events.append(f"new star by @{s['user']}")

    for f in (curr.get("forks") or []):
        if f["id"] not in prev_forks:
            events.append(f"new fork: {f['full_name']} by @{f['owner']}")

    pc, cc = prev.get("counts") or {}, curr.get("counts") or {}
    for label, key in (("watchers", "watchers"), ("open issues", "open_issues")):
        if key in pc and key in cc and pc[key] != cc[key]:
            events.append(f"{label}: {pc[key]} -> {cc[key]}")

    pt, ct = prev.get("traffic") or {}, curr.get("traffic") or {}
    if ct and (pt.get("clones_total") != ct.get("clones_total")):
        events.append(
            f"clones (14d): {pt.get('clones_total', 0)} -> {ct['clones_total']}"
            f" ({ct.get('clones_unique', 0)} unique)"
        )

    pp, cp = prev.get("pypi") or {}, curr.get("pypi") or {}
    if cp.get("downloads_last_month") is not None and (
        pp.get("downloads_last_month") != cp.get("downloads_last_month")
    ):
        events.append(
            f"PyPI downloads/mo: {pp.get('downloads_last_month')} -> "
            f"{cp['downloads_last_month']}"
        )

    return events


def run_poll(repo, pypi_name, quiet=False):
    """One full poll. Returns (state, events)."""
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    prev = load_state()

    curr = {
        "repo": repo,
        "polled_at": now_iso(),
        "poll_number": (prev.get("poll_number") or 0) + 1,
    }
    counts = poll_counts(repo, token)
    if counts is None:
        emit(f"poll failed for {repo} — GitHub unreachable or rate-limited", quiet)
        return prev, []

    curr["counts"] = counts
    forks = poll_forks(repo, token)
    stars = poll_stargazers(repo, token)
    if forks is not None:
        curr["forks"] = forks
    if stars is not None:
        curr["stargazers"] = stars

    traffic = poll_traffic(repo, token)
    if traffic is not None:
        curr["traffic"] = traffic

    pypi = poll_pypi(pypi_name)
    if pypi is not None:
        curr["pypi"] = pypi

    if prev.get("repo") != repo:
        events = []
    else:
        events = diff(prev, curr)

    save_state(curr)

    if events:
        for ev in events:
            emit(ev, quiet)
    elif not quiet:
        print(
            f"  no change — {counts['stars']} stars, {counts['forks']} forks, "
            f"{counts['watchers']} watchers (poll #{curr['poll_number']})"
        )
    return curr, events


# --------------------------------------------------------------------------
# Commands
# --------------------------------------------------------------------------

def cmd_check(args):
    repo = args.repo or detect_repo()
    run_poll(repo, args.pypi)


def cmd_loop(args):
    repo = args.repo or detect_repo()
    seconds = parse_interval(args.interval)
    print(f"watching {repo} every {args.interval} — Ctrl+C to stop")
    try:
        while True:
            run_poll(repo, args.pypi)
            time.sleep(seconds)
    except KeyboardInterrupt:
        print("\nstopped")


def cmd_status(args):
    repo = args.repo or detect_repo()
    state = load_state()
    if not state:
        print(f"no state yet for {repo} — run `agentson watch check`")
        return
    counts = state.get("counts", {})
    print(f"repo ............. {state.get('repo')}")
    print(f"last poll ........ {state.get('polled_at')}  (#{state.get('poll_number')})")
    print(f"stars ............ {counts.get('stars')}")
    print(f"forks ............ {counts.get('forks')}")
    print(f"watchers ......... {counts.get('watchers')}")
    print(f"open issues ...... {counts.get('open_issues')}")
    print(f"pushed at ........ {counts.get('pushed_at')}")
    if state.get("traffic"):
        t = state["traffic"]
        print(
            f"clones (14d) ..... {t.get('clones_total')} total, "
            f"{t.get('clones_unique')} unique"
        )
        print(
            f"views (14d) ...... {t.get('views_total')} total, "
            f"{t.get('views_unique')} unique"
        )
    if state.get("pypi"):
        print(f"PyPI dl/mo ....... {state['pypi'].get('downloads_last_month')}")
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print()
        print("  no GITHUB_TOKEN set — these are unavailable:")
        print("    star list (who starred)   — count still shown above")
        print("    clone / view trend        — needs push access")
        print("  set one:  $env:GITHUB_TOKEN = '<pat with public_repo read>'")
    print(f"state file ....... {STATE_PATH}")
    print(f"event log ........ {LOG_PATH}")


def cmd_log(args):
    if not LOG_PATH.exists():
        print("no events recorded yet")
        return
    lines = LOG_PATH.read_text(encoding="utf-8").splitlines()
    for line in lines[-args.tail:]:
        print(line)


def cmd_install(args):
    """Register a scheduled poll. System change — runs only on request."""
    if os.name == "nt":
        py = sys.executable
        script = str(Path(__file__).resolve())
        trigger = f'"{py}" "{script}" check --repo "{args.repo or detect_repo()}"'
        cmd = [
            "schtasks", "/Create", "/TN", TASK_NAME,
            "/SC", "HOURLY", "/MO", str(args.hours),
            "/TR", trigger, "/F",
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"scheduled: {TASK_NAME} every {args.hours}h")
            print(f"  run now:  schtasks /Run /TN \"{TASK_NAME}\"")
            print(f"  remove:   agentson watch uninstall")
        else:
            print(f"failed: {result.stderr.strip()}", file=sys.stderr)
            sys.exit(1)
    else:
        script = Path(__file__).resolve()
        minutes = args.hours * 60
        line = (
            f"*/{minutes} * * * * {sys.executable} {script} check"
            f" >> {LOG_PATH} 2>&1\n"
        )
        existing = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        cron = existing.stdout if existing.returncode == 0 else ""
        if str(script) in cron:
            print("already installed in crontab")
            return
        subprocess.run(["crontab", "-"], input=cron + line, text=True, check=True)
        print(f"installed cron entry every {minutes}m")


def cmd_uninstall(args):
    if os.name == "nt":
        result = subprocess.run(
            ["schtasks", "/Delete", "/TN", TASK_NAME, "/F"],
            capture_output=True, text=True,
        )
        print("removed" if result.returncode == 0 else "not installed")
    else:
        script = str(Path(__file__).resolve())
        existing = subprocess.run(
            ["crontab", "-l"], capture_output=True, text=True
        )
        if existing.returncode != 0:
            print("no crontab")
            return
        kept = [
            ln for ln in existing.stdout.splitlines() if script not in ln
        ]
        subprocess.run(
            ["crontab", "-"], input="\n".join(kept) + "\n", text=True, check=True
        )
        print("removed")


def parse_interval(value):
    """'6h' / '30m' / '1d' / bare number (treated as hours)."""
    m = re.fullmatch(r"(\d+)\s*([hmd]?)", str(value).strip().lower())
    if not m:
        raise argparse.ArgumentTypeError(f"bad interval: {value!r}")
    n, unit = int(m.group(1)), m.group(2) or "h"
    return n * {"h": 3600, "m": 60, "d": 86400}[unit]


def cmd_watch(args):
    """Dispatch `agentson watch <sub>` from the top-level CLI."""
    sub = getattr(args, "watch_command", None)
    handlers = {
        "check": cmd_check,
        "status": cmd_status,
        "log": cmd_log,
        "loop": cmd_loop,
        "install": cmd_install,
        "uninstall": cmd_uninstall,
    }
    if sub not in handlers:
        print(
            "Usage: agentson watch <check|status|log|loop|install|uninstall>",
            file=sys.stderr,
        )
        sys.exit(2)
    handlers[sub](args)


def build_parser(sub):
    """Register `agentson watch` on the shared subparsers object."""
    watch = sub.add_parser(
        "watch",
        help="Monitor adoption — forks, stars, watchers, clone trend",
    )
    wsub = watch.add_subparsers(dest="watch_command")

    for name, fn, helptext in (
        ("check", cmd_check, "Poll once, report changes, save state"),
        ("status", cmd_status, "Show current counts and last poll time"),
        ("log", cmd_log, "Print recent events"),
    ):
        p = wsub.add_parser(name, help=helptext)
        p.set_defaults(func=fn)
        p.add_argument("--repo", help="owner/name (default: from git remote)")
        p.add_argument("--pypi", help="PyPI package name for download stats")
        if name == "log":
            p.add_argument("--tail", type=int, default=25, help="Lines to show")

    loop = wsub.add_parser("loop", help="Poll forever at an interval")
    loop.set_defaults(func=cmd_loop)
    loop.add_argument("--interval", default="6h", help="e.g. 6h, 30m, 1d")
    loop.add_argument("--repo", help="owner/name (default: from git remote)")
    loop.add_argument("--pypi", help="PyPI package name for download stats")

    inst = wsub.add_parser("install", help="Register as scheduled task / cron")
    inst.set_defaults(func=cmd_install)
    inst.add_argument("--hours", type=int, default=6, help="Poll every N hours")
    inst.add_argument("--repo", help="owner/name (default: from git remote)")

    uninst = wsub.add_parser("uninstall", help="Remove the scheduled task")
    uninst.set_defaults(func=cmd_uninstall)

    return watch


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    parser = argparse.ArgumentParser(prog="agentson watch")
    build_parser(parser.add_subparsers(dest="watch_command"))
    args = parser.parse_args(argv)
    if not getattr(args, "func", None):
        parser.print_help()
        return 1
    args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
