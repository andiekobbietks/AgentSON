"""Tests for the .github/workflows/adr-viewer.yml GitHub Actions workflow.

Note: PyYAML parses YAML 1.1, where the bare key ``on`` is interpreted as
the boolean ``True`` rather than the string ``"on"``. This is a well-known
quirk when parsing GitHub Actions workflow files with ``yaml.safe_load``,
so tests look the trigger config up via the boolean key.
"""
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).parent.parent
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "adr-viewer.yml"


@pytest.fixture(scope="module")
def workflow_text():
    return WORKFLOW_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def workflow(workflow_text):
    return yaml.safe_load(workflow_text)


def _on_config(workflow_dict):
    # "on:" is parsed as the boolean True key under PyYAML's default
    # (YAML 1.1) resolver.
    return workflow_dict.get("on", workflow_dict.get(True))


def test_workflow_file_exists():
    assert WORKFLOW_PATH.is_file()


def test_workflow_is_valid_yaml(workflow):
    assert isinstance(workflow, dict)


def test_workflow_name(workflow):
    assert workflow["name"] == "Regenerate ADR index"


def test_workflow_has_push_and_workflow_dispatch_triggers(workflow):
    on_config = _on_config(workflow)
    assert on_config is not None
    assert "push" in on_config
    assert "workflow_dispatch" in on_config


def test_workflow_push_trigger_targets_master(workflow):
    on_config = _on_config(workflow)
    assert on_config["push"]["branches"] == ["master"]


def test_workflow_push_trigger_scoped_to_adr_directory(workflow):
    on_config = _on_config(workflow)
    assert on_config["push"]["paths"] == ["docs/standards/adrs/**"]


def test_workflow_dispatch_trigger_has_no_required_inputs(workflow):
    on_config = _on_config(workflow)
    assert on_config["workflow_dispatch"] == {}


def test_workflow_grants_contents_write_permission(workflow):
    assert workflow["permissions"] == {"contents": "write"}


def test_workflow_defines_build_adr_index_job(workflow):
    assert "build-adr-index" in workflow["jobs"]


def test_job_runs_on_ubuntu_latest(workflow):
    job = workflow["jobs"]["build-adr-index"]
    assert job["runs-on"] == "ubuntu-latest"


class TestJobSteps:
    @pytest.fixture(scope="class")
    def steps(self, workflow):
        return workflow["jobs"]["build-adr-index"]["steps"]

    def test_first_step_checks_out_repo(self, steps):
        assert steps[0]["uses"] == "actions/checkout@v4"

    def test_second_step_sets_up_python_3_11(self, steps):
        step = steps[1]
        assert step["uses"] == "actions/setup-python@v5"
        assert step["with"]["python-version"] == "3.11"

    def test_install_adr_viewer_step(self, steps):
        step = next(s for s in steps if s.get("name") == "Install adr-viewer")
        assert step["run"].strip() == "pip install adr-viewer"

    def test_generate_adr_index_step_uses_expected_paths(self, steps):
        step = next(s for s in steps if s.get("name") == "Generate ADR index")
        run = step["run"]
        assert "--adr-path docs/standards/adrs/" in run
        assert "--output docs/standards/adr-index.html" in run
        assert "--title" in run
        assert "AgentSON" in run

    def test_apply_theme_step_invokes_script(self, steps):
        step = next(
            s for s in steps
            if s.get("name") == "Apply amber-phosphor theme (ADR-004 tokens)"
        )
        assert step["run"].strip() == "python3 .github/workflows/apply_adr_theme.py"

    def test_apply_theme_step_runs_after_generate_index(self, steps):
        names = [s.get("name") for s in steps]
        generate_idx = names.index("Generate ADR index")
        theme_idx = names.index("Apply amber-phosphor theme (ADR-004 tokens)")
        assert theme_idx == generate_idx + 1

    def test_check_for_changes_step_stages_generated_file(self, steps):
        step = next(s for s in steps if s.get("name") == "Check for changes")
        assert step["id"] == "check"
        assert "git add docs/standards/adr-index.html" in step["run"]
        assert "GITHUB_OUTPUT" in step["run"]

    def test_open_pr_step_is_conditional_on_changes(self, steps):
        step = next(
            s for s in steps if s.get("name") == "Open PR with regenerated index"
        )
        assert step["if"] == "steps.check.outputs.changed == 'true'"

    def test_open_pr_step_uses_create_pull_request_action(self, steps):
        step = next(
            s for s in steps if s.get("name") == "Open PR with regenerated index"
        )
        assert step["uses"] == "peter-evans/create-pull-request@v6"
        with_config = step["with"]
        assert with_config["branch"] == "automated/adr-index-update"
        assert with_config["delete-branch"] is True
        assert "docs/standards/adr-index.html" in with_config["commit-message"] or (
            "regenerate" in with_config["commit-message"].lower()
        )

    def test_steps_are_in_expected_order(self, steps):
        expected_order = [
            "actions/checkout@v4",
            "actions/setup-python@v5",
        ]
        actual_uses = [s.get("uses") for s in steps if s.get("uses")]
        assert actual_uses[:2] == expected_order

    def test_all_run_steps_have_names(self, steps):
        # Every step that executes a shell command should be named for
        # readability in the Actions UI (the checkout/setup-python steps
        # are the only unnamed ones, and they don't use `run:`).
        for step in steps:
            if "run" in step:
                assert "name" in step, f"Unnamed run step: {step}"