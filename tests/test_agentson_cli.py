"""
Tests for agentson_cli.py — a thin script wrapper that works around the
Windows executable installation issue by invoking ``cli.main.main()``
directly via ``python agentson_cli.py`` instead of relying on the
``agentson`` console-script entry point.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "agentson_cli.py"


def _run(args):
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_script_file_exists():
    assert SCRIPT_PATH.is_file()


def test_no_args_prints_cli_help_and_exits_zero():
    result = _run([])
    assert result.returncode == 0
    assert "usage" in result.stdout.lower()
    assert "agentson" in result.stdout.lower()


def test_dispatches_to_cli_main_search_subcommand():
    # No .agentson files exist under the repo-root-relative default search
    # dir for this made-up term, so the real cli.main.cmd_search prints the
    # "no files found" message rather than raising — confirms the script
    # wires argv through to cli.main.main() end-to-end.
    result = _run(["search", "a-term-that-should-not-exist-anywhere", "--dir", str(REPO_ROOT / "tests")])
    assert result.returncode == 0
    assert "matching" in result.stdout.lower() or "no .agentson files found" in result.stdout.lower()


def test_unknown_subcommand_exits_nonzero():
    result = _run(["not-a-real-subcommand"])
    assert result.returncode != 0