"""
Tests for check_opencode.py — an ad hoc debug script (hardcoded to a
Windows path, ``C:\\Users\\LLM-Test\\...``) used to manually inspect
opencode sessions on one particular machine.

The script has no functions or ``if __name__ == "__main__"`` guard: all
of its logic runs at module scope. On any machine other than the one it
was written for (including this test environment), the hardcoded
``db_path`` does not exist, so it must fall through to the "not found"
branch without raising. These tests exercise that fallback path via
subprocess, since running the file is the only way to exercise its logic
without a hardcoded Windows filesystem.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "check_opencode.py"


def _run():
    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_script_file_exists():
    assert SCRIPT_PATH.is_file()


def test_runs_without_error_when_hardcoded_db_path_is_absent():
    # On this machine the hardcoded Windows db_path can never exist, so
    # the script should gracefully report that instead of raising.
    result = _run()
    assert result.returncode == 0


def test_reports_missing_sqlite_file():
    result = _run()
    assert "SQLite file not found" in result.stdout


def test_reports_the_hardcoded_windows_path():
    result = _run()
    assert r"C:\Users\LLM-Test\.local\share\opencode\opencode.db" in result.stdout


def test_does_not_attempt_to_list_a_nonexistent_directory():
    # The parent directory (…\.local\share\opencode) also does not exist
    # on this machine, so the "Files in directory:" branch must not run.
    result = _run()
    assert "Files in directory:" not in result.stdout