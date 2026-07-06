"""Tests for .github/workflows/apply_adr_theme.py.

This script is invoked as a CI build step (not a Python package module), so
it is loaded here via importlib from its file path. Its TARGET/THEME
constants are relative paths that are resolved against the process's
current working directory at call time, so tests use ``monkeypatch.chdir``
to point it at temporary fixture directories rather than the real repo
files.
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
SCRIPT_PATH = REPO_ROOT / ".github" / "workflows" / "apply_adr_theme.py"
REAL_THEME_PATH = REPO_ROOT / ".github" / "workflows" / "adr-viewer-theme.html"
REAL_INDEX_PATH = REPO_ROOT / "docs" / "standards" / "adr-index.html"


def _load_module():
    spec = importlib.util.spec_from_file_location("apply_adr_theme", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


apply_adr_theme = _load_module()

SAMPLE_THEME = (
    "<style type=\"text/css\">\n"
    "            :root { --accent: #ffb000; }\n"
    "        </style>\n"
    "    </head>\n"
)


def _write_target(base_dir, body):
    target = base_dir / "docs" / "standards" / "adr-index.html"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(body, encoding="utf-8")
    return target


def _write_theme(base_dir, content=SAMPLE_THEME):
    theme = base_dir / ".github" / "workflows" / "adr-viewer-theme.html"
    theme.parent.mkdir(parents=True, exist_ok=True)
    theme.write_text(content, encoding="utf-8")
    return theme


class TestModuleConstants:
    def test_target_path(self):
        assert apply_adr_theme.TARGET == "docs/standards/adr-index.html"

    def test_theme_path(self):
        assert apply_adr_theme.THEME == ".github/workflows/adr-viewer-theme.html"


class TestMainSuccess:
    def test_replaces_head_tag_with_theme_block(self, tmp_path, monkeypatch):
        body = "<html><head><title>x</title></head><body>hi</body></html>"
        target = _write_target(tmp_path, body)
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = apply_adr_theme.main()

        assert result == 0
        new_content = target.read_text(encoding="utf-8")
        assert "<head><title>x</title>" in new_content
        assert "--accent: #ffb000" in new_content
        assert "<body>hi</body></html>" in new_content

    def test_output_has_exactly_one_head_closing_tag(self, tmp_path, monkeypatch):
        # The original </head> is consumed by the replace, and the theme
        # block itself supplies exactly one </head>, so the invariant
        # "exactly one </head>" should still hold after theming.
        body = "<html><head></head><body></body></html>"
        target = _write_target(tmp_path, body)
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        assert apply_adr_theme.main() == 0
        assert target.read_text(encoding="utf-8").count("</head>") == 1

    def test_prints_success_message(self, tmp_path, monkeypatch, capsys):
        _write_target(tmp_path, "<html><head></head><body></body></html>")
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        apply_adr_theme.main()

        captured = capsys.readouterr()
        assert "Applied theme to docs/standards/adr-index.html" in captured.out

    def test_preserves_content_outside_head(self, tmp_path, monkeypatch):
        body = (
            "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"></head>"
            "<body><h1>ADR-004: Amber Phosphor \u2014 tokens</h1></body></html>"
        )
        target = _write_target(tmp_path, body)
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        assert apply_adr_theme.main() == 0
        new_content = target.read_text(encoding="utf-8")
        assert "<meta charset=\"UTF-8\">" in new_content
        assert "ADR-004: Amber Phosphor \u2014 tokens" in new_content

    def test_writes_file_with_utf8_encoding(self, tmp_path, monkeypatch):
        body = "<html><head></head><body>caf\u00e9 \u2014 \u00e9\u00e8</body></html>"
        target = _write_target(tmp_path, body)
        _write_theme(tmp_path, content="<style>/* \u00fcmlaut */</style>\n    </head>\n")

        monkeypatch.chdir(tmp_path)
        assert apply_adr_theme.main() == 0
        new_content = target.read_text(encoding="utf-8")
        assert "caf\u00e9 \u2014 \u00e9\u00e8" in new_content
        assert "\u00fcmlaut" in new_content


class TestMainHeadCountValidation:
    def test_zero_head_tags_returns_error(self, tmp_path, monkeypatch, capsys):
        original_body = "<html><body>no head tag here</body></html>"
        target = _write_target(tmp_path, original_body)
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = apply_adr_theme.main()

        assert result == 1
        captured = capsys.readouterr()
        assert "found 0" in captured.out
        # File must be left untouched on error.
        assert target.read_text(encoding="utf-8") == original_body

    def test_multiple_head_tags_returns_error(self, tmp_path, monkeypatch, capsys):
        original_body = "<html><head></head><body></body></head></html>"
        target = _write_target(tmp_path, original_body)
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        result = apply_adr_theme.main()

        assert result == 1
        captured = capsys.readouterr()
        assert "found 2" in captured.out
        assert target.read_text(encoding="utf-8") == original_body

    def test_error_message_names_target_file(self, tmp_path, monkeypatch, capsys):
        _write_target(tmp_path, "<html><body>no head</body></html>")
        _write_theme(tmp_path)

        monkeypatch.chdir(tmp_path)
        apply_adr_theme.main()

        captured = capsys.readouterr()
        assert "docs/standards/adr-index.html" in captured.out


class TestCliInvocation:
    """End-to-end tests that invoke the script as a subprocess, exercising
    the ``if __name__ == "__main__": sys.exit(main())`` entry point."""

    def test_cli_success_exit_code(self, tmp_path):
        _write_target(tmp_path, "<html><head></head><body></body></html>")
        _write_theme(tmp_path)

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        assert "Applied theme" in result.stdout

    def test_cli_head_mismatch_exit_code(self, tmp_path):
        _write_target(tmp_path, "<html><body>no head</body></html>")
        _write_theme(tmp_path)

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode == 1
        assert "ERROR" in result.stdout

    def test_cli_missing_target_file_fails(self, tmp_path):
        _write_theme(tmp_path)
        # Deliberately do not create docs/standards/adr-index.html.

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "FileNotFoundError" in result.stderr

    def test_cli_missing_theme_file_fails(self, tmp_path):
        _write_target(tmp_path, "<html><head></head><body></body></html>")
        # Deliberately do not create the theme file.

        result = subprocess.run(
            [sys.executable, str(SCRIPT_PATH)],
            cwd=tmp_path,
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "FileNotFoundError" in result.stderr


class TestAgainstRealRepoArtifacts:
    """Read-only sanity checks against the real checked-in theme/output
    files, without ever writing to them, to guard against drift between
    the script's invariants and the committed artifacts."""

    def test_real_theme_file_exists(self):
        assert REAL_THEME_PATH.is_file()

    def test_real_theme_file_has_exactly_one_head_closing_tag(self):
        content = REAL_THEME_PATH.read_text(encoding="utf-8")
        assert content.count("</head>") == 1

    def test_real_generated_index_has_exactly_one_head_closing_tag(self):
        content = REAL_INDEX_PATH.read_text(encoding="utf-8")
        assert content.count("</head>") == 1

    def test_real_generated_index_contains_theme_content(self):
        theme_content = REAL_THEME_PATH.read_text(encoding="utf-8")
        index_content = REAL_INDEX_PATH.read_text(encoding="utf-8")
        assert theme_content in index_content