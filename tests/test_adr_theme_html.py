"""Tests for the static HTML artifacts added by the ADR theming PR:

- .github/workflows/adr-viewer-theme.html (the theme fragment spliced into
  the generated index by apply_adr_theme.py)
- docs/standards/adr-index.html (the committed, already-themed output)

These are data/markup files rather than executable code, so the tests here
validate their structural invariants (well-formedness, required selectors,
required tokens) rather than behavior.
"""
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parent.parent
THEME_PATH = REPO_ROOT / ".github" / "workflows" / "adr-viewer-theme.html"
INDEX_PATH = REPO_ROOT / "docs" / "standards" / "adr-index.html"

EXPECTED_STATUS_CLASSES = [
    "adr-accepted",
    "adr-superseded",
    "adr-amended",
    "adr-unknown",
    "adr-pending",
]

EXPECTED_CSS_VARIABLES = [
    "--bg",
    "--surface",
    "--border",
    "--text",
    "--text-muted",
    "--accent",
]


class _LenientHTMLValidator(HTMLParser):
    """Collects parser errors encountered while scanning the document."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []

    def error(self, message):  # pragma: no cover - only hit on malformed markup
        self.errors.append(message)


def _parse_without_errors(html_text):
    parser = _LenientHTMLValidator()
    parser.feed(html_text)
    parser.close()
    return parser.errors


@pytest.fixture(scope="module")
def theme_text():
    return THEME_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def index_text():
    return INDEX_PATH.read_text(encoding="utf-8")


class TestThemeFragment:
    def test_file_exists(self):
        assert THEME_PATH.is_file()

    def test_ends_with_head_closing_tag(self, theme_text):
        assert theme_text.rstrip().endswith("</head>")

    def test_has_exactly_one_head_closing_tag(self, theme_text):
        assert theme_text.count("</head>") == 1

    def test_defines_expected_css_custom_properties(self, theme_text):
        for var in EXPECTED_CSS_VARIABLES:
            assert f"{var}:" in theme_text, f"missing CSS variable {var}"

    def test_accent_color_matches_adr_004(self, theme_text):
        assert "--accent: #ffb000;" in theme_text

    def test_defines_status_color_overrides_for_every_status_class(self, theme_text):
        for status in EXPECTED_STATUS_CLASSES:
            assert f".panel-heading.{status}" in theme_text, f"missing override for {status}"

    def test_preserves_superseded_strikethrough_rule(self, theme_text):
        assert ".adr-superseded > .panel-title > a" in theme_text
        assert "text-decoration: line-through" in theme_text

    def test_loads_expected_google_fonts(self, theme_text):
        assert "fonts.googleapis.com" in theme_text
        assert "Space+Mono" in theme_text
        assert "IBM+Plex+Sans" in theme_text

    def test_uses_important_to_win_bootstrap_cascade(self, theme_text):
        # The whole point of loading this after bootstrap.min.css is that
        # these overrides must beat Bootstrap's specificity.
        assert theme_text.count("!important") > 10

    def test_html_parses_without_errors(self, theme_text):
        # Wrap in a minimal document since this is a <head> fragment.
        wrapped = f"<html><head>{theme_text}<body></body></html>"
        assert _parse_without_errors(wrapped) == []


class TestGeneratedIndex:
    def test_file_exists(self):
        assert INDEX_PATH.is_file()

    def test_is_valid_html_document(self, index_text):
        assert index_text.strip().startswith("<!DOCTYPE HTML>")
        assert "<html" in index_text
        assert "</html>" in index_text

    def test_html_parses_without_errors(self, index_text):
        assert _parse_without_errors(index_text) == []

    def test_has_exactly_one_head_closing_tag(self, index_text):
        assert index_text.count("</head>") == 1

    def test_title_reflects_configured_workflow_title(self, index_text):
        assert "AgentSON \u2014 Architecture Decision Records" in index_text

    def test_theme_css_variables_present(self, index_text):
        for var in EXPECTED_CSS_VARIABLES:
            assert f"{var}:" in index_text

    def test_amber_accent_applied(self, index_text):
        assert "#ffb000" in index_text

    def test_contains_panel_for_every_adr(self, index_text):
        # There are 12 ADR markdown files under docs/standards/adrs/.
        adr_dir = REPO_ROOT / "docs" / "standards" / "adrs"
        adr_files = sorted(adr_dir.glob("adr-*.md"))
        assert len(adr_files) > 0

        panel_count = index_text.count('class="panel panel-default"')
        assert panel_count == len(adr_files)

    def test_collapse_ids_are_sequential_and_unique(self, index_text):
        ids = re.findall(r'id="collapse(\d+)"', index_text)
        numeric_ids = sorted(int(i) for i in ids)
        assert numeric_ids == list(range(len(numeric_ids)))

    def test_every_panel_title_link_targets_its_collapse_id(self, index_text):
        hrefs = re.findall(r'href="#collapse(\d+)"', index_text)
        ids = re.findall(r'id="collapse(\d+)"', index_text)
        assert sorted(hrefs, key=int) == sorted(ids, key=int)

    def test_bootstrap_and_jquery_assets_still_referenced(self, index_text):
        # The theme only recolors/refonts; it must not remove the
        # underlying Bootstrap accordion behavior.
        assert "bootstrap.min.css" in index_text
        assert "bootstrap.min.js" in index_text
        assert "jquery" in index_text.lower()

    def test_footer_present(self, index_text):
        assert "Generated with" in index_text
        assert "ADR Viewer" in index_text