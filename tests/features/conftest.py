"""
Shared fixtures for the Gherkin/pytest-bdd suite.

Honesty note: this suite is being stood up for the first time. Where a
step can't yet be implemented against real code (e.g. there is no
`agentson validate` CLI command), the step is marked xfail with a reason
rather than faked into a pass. Do not remove an xfail marker without
actually making the underlying feature exist.
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / "spec" / "v1.json"


@pytest.fixture
def repo_root():
    return REPO_ROOT


@pytest.fixture
def schema():
    return json.loads(SCHEMA_PATH.read_text())


def run_cli(*args, cwd=None):
    """Invoke the real CLI as a subprocess, exactly as a user would."""
    cmd = [sys.executable, str(REPO_ROOT / "cli" / "main.py")] + list(args)
    result = subprocess.run(
        cmd, cwd=cwd or REPO_ROOT, capture_output=True, text=True, timeout=30
    )
    return result


@pytest.fixture
def cli():
    return run_cli
