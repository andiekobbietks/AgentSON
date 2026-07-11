"""
Tests for check_status.ps1 — a PowerShell status-check script.

No PowerShell runtime (pwsh/powershell) or Pester test harness is
available in this Python-focused test environment, so these tests
validate the script's static structure and content instead of executing
it: balanced braces (a basic syntax sanity check), the expected git
commands, and the expected key-file list, mirroring the structural-test
approach already used for other non-Python artifacts in this repo (see
tests/test_adr_theme_html.py for HTML, tests/test_adr_viewer_workflow.py
for YAML).
"""
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / "check_status.ps1"


@pytest.fixture(scope="module")
def script_text():
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_script_file_exists():
    assert SCRIPT_PATH.is_file()


def test_braces_are_balanced(script_text):
    assert script_text.count("{") == script_text.count("}")


def test_sets_stop_error_action_preference(script_text):
    assert '$ErrorActionPreference = "Stop"' in script_text


def test_checks_for_git_repository(script_text):
    assert "Test-Path .git" in script_text


def test_runs_expected_git_status_command(script_text):
    assert "git status --porcelain" in script_text


def test_runs_expected_git_log_command(script_text):
    assert "git log --oneline -5" in script_text


def test_runs_expected_git_tag_command(script_text):
    assert "git tag --list" in script_text


def test_runs_expected_git_branch_command(script_text):
    assert "git branch -r" in script_text


def test_checks_all_expected_key_files(script_text):
    for key_file in ["README.md", "pyproject.toml", "CHANGELOG.md", "LICENSE", "PRD.md"]:
        assert key_file in script_text


def test_reads_license_file_head(script_text):
    assert 'Get-Content -Path "LICENSE" -First 5' in script_text


def test_searches_changelog_for_v0_1_0_entry(script_text):
    assert 'Select-String -Path "CHANGELOG.md" -Pattern "## v0.1.0"' in script_text


def test_key_files_block_uses_a_foreach_loop(script_text):
    assert "foreach ($file in $keyFiles)" in script_text