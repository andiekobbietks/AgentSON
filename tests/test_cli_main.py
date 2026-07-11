"""
Tests for cli/main.py — the AgentSON CLI entry point.

Covers the export/list/push/pull/search/render/import/finetune commands
and their pure-function helpers (render_markdown, render_html,
_search_session, get_default_db_paths).

`cmd_search` is defined twice in cli/main.py (a stub near the top of the
file, and the real glob-based implementation further down). Python keeps
only the last definition bound to the module-level name, so
`cli.main.cmd_search` and the `search` subcommand dispatch to the
glob-based version. `TestCmdSearchDuplicateDefinitionRegression` pins this
behavior — see CHANGELOG.md "Known issues" for the underlying report.

Reader/importer/exporter/Supabase dependencies are imported lazily inside
each `cmd_*` function body (`from readers.opencode import ...`), so tests
patch the underlying module attributes (e.g. ``readers.opencode.read``)
rather than attributes on ``cli.main`` itself.
"""
import argparse
import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import main as cli_main


def _ns(**kwargs):
    """Build an argparse.Namespace with sensible defaults for missing keys."""
    defaults = {
        "tool": None,
        "session": None,
        "all": False,
        "output": ".",
        "input": None,
        "limit": 50,
        "term": "",
        "dir": ".",
        "format": "md",
        "include_thoughts": True,
        "all_branches": False,
        "search": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


# ---------------------------------------------------------------------------
# get_default_db_paths
# ---------------------------------------------------------------------------

class TestGetDefaultDbPaths:
    def test_returns_all_expected_tools(self):
        paths = cli_main.get_default_db_paths()
        assert set(paths.keys()) == {"opencode", "minimax", "antigravity"}

    def test_paths_are_rooted_at_home(self):
        paths = cli_main.get_default_db_paths()
        home = Path.home()
        for p in paths.values():
            assert str(p).startswith(str(home))

    def test_opencode_path_suffix(self):
        paths = cli_main.get_default_db_paths()
        assert paths["opencode"].name == "opencode.db"


# ---------------------------------------------------------------------------
# cmd_export
# ---------------------------------------------------------------------------

class TestCmdExportOpencode:
    def test_missing_db_exits_1(self, tmp_path, capsys):
        args = _ns(tool="opencode", output=str(tmp_path))
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "opencode database not found" in capsys.readouterr().err

    def test_all_exports_every_session(self, tmp_path, capsys):
        args = _ns(tool="opencode", all=True, output=str(tmp_path))
        sessions = [{"id": "s1", "title": "First"}, {"id": "s2", "title": "Second"}]

        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.opencode.list_sessions", return_value=sessions), \
             patch("readers.opencode.read", return_value={"id": "s1", "entries": []}):
            cli_main.cmd_export(args)

        out = capsys.readouterr().out
        assert "Exported 2 sessions" in out
        assert (tmp_path / "opencode_s1.agentson").exists()
        assert (tmp_path / "opencode_s2.agentson").exists()

    def test_single_session_without_session_flag_exits_1(self, tmp_path, capsys):
        args = _ns(tool="opencode", all=False, session=None, output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=True):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "--session required" in capsys.readouterr().err

    def test_single_session_writes_expected_file(self, tmp_path, capsys):
        args = _ns(tool="opencode", all=False, session="ses_abc", output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.opencode.read", return_value={"id": "ses_abc", "entries": []}) as mock_read:
            cli_main.cmd_export(args)

        mock_read.assert_called_once()
        out_file = tmp_path / "opencode_ses_abc.agentson"
        assert out_file.exists()
        data = json.loads(out_file.read_text(encoding="utf-8"))
        assert data["id"] == "ses_abc"
        assert "Exported to" in capsys.readouterr().out


class TestCmdExportMinimax:
    def test_missing_db_exits_1(self, tmp_path, capsys):
        args = _ns(tool="minimax", output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "MiniMax database not found" in capsys.readouterr().err

    def test_single_session_writes_expected_file(self, tmp_path):
        args = _ns(tool="minimax", session="mm_1", output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.minimax.read", return_value={"id": "mm_1", "entries": []}):
            cli_main.cmd_export(args)
        assert (tmp_path / "minimax_mm_1.agentson").exists()


class TestCmdExportAntigravity:
    def test_missing_dir_exits_1(self, tmp_path, capsys):
        args = _ns(tool="antigravity", output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "Antigravity IDE directory not found" in capsys.readouterr().err

    def test_get_sessions_file_not_found_exits_1(self, tmp_path, capsys):
        args = _ns(tool="antigravity", output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions",
                   side_effect=FileNotFoundError("no trajectory db")):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "no trajectory db" in capsys.readouterr().err

    def test_all_exports_every_session(self, tmp_path, capsys):
        args = _ns(tool="antigravity", all=True, output=str(tmp_path))
        sessions = [{"session_id": "ag1"}, {"session_id": "ag2"}]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=sessions), \
             patch("readers.antigravity.read_antigravity_session", return_value={"id": "ag"}):
            cli_main.cmd_export(args)
        assert "Exported 2 sessions" in capsys.readouterr().out
        assert (tmp_path / "antigravity_ag1.agentson").exists()
        assert (tmp_path / "antigravity_ag2.agentson").exists()

    def test_no_session_flag_exports_first_session(self, tmp_path):
        args = _ns(tool="antigravity", session=None, output=str(tmp_path))
        sessions = [{"session_id": "first"}, {"session_id": "second"}]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=sessions), \
             patch("readers.antigravity.read_antigravity_session", return_value={"id": "first"}):
            cli_main.cmd_export(args)
        assert (tmp_path / "antigravity_first.agentson").exists()
        assert not (tmp_path / "antigravity_second.agentson").exists()

    def test_no_session_flag_and_no_sessions_exits_1(self, tmp_path, capsys):
        args = _ns(tool="antigravity", session=None, output=str(tmp_path))
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=[]):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "No sessions found" in capsys.readouterr().err

    def test_specific_session_id_not_found_exits_1(self, tmp_path, capsys):
        args = _ns(tool="antigravity", session="missing", output=str(tmp_path))
        sessions = [{"session_id": "present"}]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=sessions):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "Session missing not found" in capsys.readouterr().err

    def test_specific_session_id_found_writes_file(self, tmp_path):
        args = _ns(tool="antigravity", session="present", output=str(tmp_path))
        sessions = [{"session_id": "present"}, {"session_id": "other"}]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=sessions), \
             patch("readers.antigravity.read_antigravity_session", return_value={"id": "present"}):
            cli_main.cmd_export(args)
        assert (tmp_path / "antigravity_present.agentson").exists()


class TestCmdExportLibre:
    def test_missing_input_exits_1(self, tmp_path, capsys):
        args = _ns(tool="libre", input=None, output=str(tmp_path))
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "--input required" in capsys.readouterr().err

    def test_missing_csv_file_exits_1(self, tmp_path, capsys):
        missing_csv = tmp_path / "nope.csv"
        args = _ns(tool="libre", input=str(missing_csv), output=str(tmp_path))
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "CSV file not found" in capsys.readouterr().err

    def test_success_writes_expected_file(self, tmp_path, capsys):
        csv_path = tmp_path / "glucose.csv"
        csv_path.write_text("timestamp,value\n", encoding="utf-8")
        args = _ns(tool="libre", input=str(csv_path), output=str(tmp_path))

        with patch("readers.libre.read_libre_csv", return_value={"id": "libre1", "entries": []}) as mock_read:
            cli_main.cmd_export(args)

        mock_read.assert_called_once_with(str(csv_path))
        out_file = tmp_path / "libre_glucose.agentson"
        assert out_file.exists()
        assert "Exported to" in capsys.readouterr().out


class TestCmdExportUnknownTool:
    def test_unknown_tool_exits_1(self, tmp_path, capsys):
        args = _ns(tool="not-a-real-tool", output=str(tmp_path))
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_export(args)
        assert exc.value.code == 1
        assert "Unknown tool" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# cmd_list
# ---------------------------------------------------------------------------

class TestCmdList:
    def test_opencode_missing_db_exits_1(self, capsys):
        args = _ns(tool="opencode", limit=50)
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_list(args)
        assert exc.value.code == 1
        assert "opencode database not found" in capsys.readouterr().err

    def test_minimax_missing_db_exits_1(self, capsys):
        args = _ns(tool="minimax", limit=50)
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_list(args)
        assert exc.value.code == 1
        assert "MiniMax database not found" in capsys.readouterr().err

    def test_antigravity_missing_dir_exits_1(self, capsys):
        args = _ns(tool="antigravity", limit=50)
        with patch("pathlib.Path.exists", return_value=False):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_list(args)
        assert exc.value.code == 1
        assert "Antigravity IDE directory not found" in capsys.readouterr().err

    def test_antigravity_file_not_found_exits_1(self, capsys):
        args = _ns(tool="antigravity", limit=50)
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions",
                   side_effect=FileNotFoundError("bad path")):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_list(args)
        assert exc.value.code == 1
        assert "bad path" in capsys.readouterr().err

    def test_unknown_tool_exits_1(self, capsys):
        args = _ns(tool="unknown", limit=50)
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_list(args)
        assert exc.value.code == 1
        assert "Unknown tool" in capsys.readouterr().err

    def test_opencode_prints_session_fields(self, capsys):
        args = _ns(tool="opencode", limit=10)
        sessions = [{"id": "s1", "title": "Fix bug", "agent": "claude", "model": "opus", "updated": "now"}]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.opencode.list_sessions", return_value=sessions):
            cli_main.cmd_list(args)
        out = capsys.readouterr().out
        assert "ID:      s1" in out
        assert "Title:   Fix bug" in out
        assert "Agent:   claude" in out
        assert "Model:   opus" in out

    def test_antigravity_prints_trajectory_fields(self, capsys):
        args = _ns(tool="antigravity", limit=10)
        sessions = [{
            "session_id": "ag1",
            "cascade_id": "cas1",
            "trajectory_type": "code_edit",
            "total_steps": 4,
        }]
        with patch("pathlib.Path.exists", return_value=True), \
             patch("readers.antigravity.get_antigravity_sessions", return_value=sessions):
            cli_main.cmd_list(args)
        out = capsys.readouterr().out
        assert "ID:      ag1" in out
        assert "Cascade: cas1" in out
        assert "Type:    code_edit" in out
        assert "Steps:   4" in out


# ---------------------------------------------------------------------------
# cmd_push / cmd_pull
# ---------------------------------------------------------------------------

class TestCmdPush:
    def test_missing_credentials_exits_1(self, tmp_path, capsys):
        input_file = tmp_path / "session.agentson"
        input_file.write_text("{}", encoding="utf-8")
        args = _ns(input=str(input_file))
        with patch("cli.supabase_client.AgentSONSupabase", side_effect=ValueError("no creds")):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_push(args)
        assert exc.value.code == 1
        assert "no creds" in capsys.readouterr().err

    def test_success_prints_session_id(self, tmp_path, capsys):
        input_file = tmp_path / "session.agentson"
        input_file.write_text(json.dumps({"id": "sess-1"}), encoding="utf-8")
        args = _ns(input=str(input_file))

        with patch("cli.supabase_client.AgentSONSupabase") as mock_client_cls:
            mock_client_cls.return_value.push.return_value = {"id": "remote-123"}
            cli_main.cmd_push(args)

        out = capsys.readouterr().out
        assert "Pushed! Session ID: remote-123" in out


class TestCmdPull:
    def test_missing_credentials_exits_1(self, capsys):
        args = _ns(search=None, tool=None, limit=50, output=None)
        with patch("cli.supabase_client.AgentSONSupabase", side_effect=ValueError("no creds")):
            with pytest.raises(SystemExit) as exc:
                cli_main.cmd_pull(args)
        assert exc.value.code == 1
        assert "no creds" in capsys.readouterr().err

    def test_success_without_output_prints_summary(self, capsys):
        args = _ns(search="bug", tool="opencode", limit=50, output=None)
        sessions = [
            {"id": "s1", "tool": {"id": "opencode"}, "agent": {"name": "claude"}},
        ]

        with patch("cli.supabase_client.AgentSONSupabase") as mock_client_cls:
            mock_client_cls.return_value.pull.return_value = sessions
            cli_main.cmd_pull(args)

        out = capsys.readouterr().out
        assert "Found 1 session(s)" in out
        assert "ID:    s1" in out
        assert "Tool:  opencode" in out
        assert "Agent: claude" in out

    def test_success_with_output_writes_file(self, tmp_path):
        args = _ns(search=None, tool=None, limit=50, output=str(tmp_path))
        sessions = [{"id": "s1", "tool": {"id": "opencode"}, "agent": {"name": "claude"}}]

        with patch("cli.supabase_client.AgentSONSupabase") as mock_client_cls:
            mock_client_cls.return_value.pull.return_value = sessions
            cli_main.cmd_pull(args)

        assert (tmp_path / "opencode_s1.agentson").exists()


# ---------------------------------------------------------------------------
# cmd_search / _search_session — the surviving (glob-based) implementation
# ---------------------------------------------------------------------------

class TestCmdSearchDuplicateDefinitionRegression:
    """cmd_search is defined twice in cli/main.py: a stub near line 259
    and the real glob-based implementation near line 423. Only the second
    definition survives as the module attribute. This test pins that."""

    def test_module_level_cmd_search_is_glob_based_implementation(self):
        assert cli_main.cmd_search.__doc__ == "Search AgentSON files for a term."

    def test_module_level_cmd_search_is_not_the_stub(self):
        assert "not yet implemented" not in (cli_main.cmd_search.__doc__ or "")


class TestCmdSearch:
    def test_no_files_found_prints_message(self, tmp_path, capsys):
        args = _ns(term="anything", dir=str(tmp_path))
        cli_main.cmd_search(args)
        assert "No .agentson files found" in capsys.readouterr().out

    def test_finds_matching_file(self, tmp_path, capsys):
        session = {
            "id": "s1",
            "tool": {"name": "opencode"},
            "entries": [{"type": "user-query", "text": "please fix the nightscout bug"}],
        }
        (tmp_path / "session1.agentson").write_text(json.dumps(session), encoding="utf-8")
        args = _ns(term="nightscout", dir=str(tmp_path))

        cli_main.cmd_search(args)

        out = capsys.readouterr().out
        assert "Found 1 file(s) matching 'nightscout'" in out
        assert "Session: s1" in out
        assert "Tool: opencode" in out

    def test_case_insensitive_search(self, tmp_path, capsys):
        session = {"id": "s1", "entries": [{"type": "answer", "text": "Fixed NIGHTSCOUT alerting"}]}
        (tmp_path / "session1.agentson").write_text(json.dumps(session), encoding="utf-8")
        args = _ns(term="nightscout", dir=str(tmp_path))

        cli_main.cmd_search(args)

        assert "Found 1 file(s)" in capsys.readouterr().out

    def test_no_matches_for_term(self, tmp_path, capsys):
        session = {"id": "s1", "entries": [{"type": "answer", "text": "unrelated content"}]}
        (tmp_path / "session1.agentson").write_text(json.dumps(session), encoding="utf-8")
        args = _ns(term="zzz-nomatch", dir=str(tmp_path))

        cli_main.cmd_search(args)

        assert "No matches for 'zzz-nomatch'" in capsys.readouterr().out

    def test_more_than_three_matches_reports_remainder(self, tmp_path, capsys):
        entries = [{"type": "answer", "text": f"needle {i}"} for i in range(5)]
        session = {"id": "s1", "entries": entries}
        (tmp_path / "session1.agentson").write_text(json.dumps(session), encoding="utf-8")
        args = _ns(term="needle", dir=str(tmp_path))

        cli_main.cmd_search(args)

        out = capsys.readouterr().out
        assert "... and 2 more" in out

    def test_unreadable_file_emits_warning_and_continues(self, tmp_path, capsys):
        (tmp_path / "broken.agentson").write_text("{not valid json", encoding="utf-8")
        session = {"id": "s1", "entries": [{"type": "answer", "text": "needle here"}]}
        (tmp_path / "good.agentson").write_text(json.dumps(session), encoding="utf-8")
        args = _ns(term="needle", dir=str(tmp_path))

        cli_main.cmd_search(args)

        captured = capsys.readouterr()
        assert "Warning: Could not read" in captured.err
        assert "Found 1 file(s)" in captured.out


class TestSearchSessionHelper:
    def test_matches_on_text_field(self):
        data = {"entries": [{"type": "answer", "text": "hello nightscout world"}]}
        matches = cli_main._search_session(data, "nightscout")
        assert len(matches) == 1
        assert matches[0]["type"] == "answer"

    def test_matches_on_query_field_fallback(self):
        data = {"entries": [{"type": "user-query", "query": "nightscout setup"}]}
        matches = cli_main._search_session(data, "nightscout")
        assert len(matches) == 1

    def test_matches_on_code_field_fallback(self):
        data = {"entries": [{"type": "action", "code": "grep nightscout src/"}]}
        matches = cli_main._search_session(data, "nightscout")
        assert len(matches) == 1

    def test_title_match_is_inserted_first(self):
        data = {
            "title": "Nightscout integration",
            "entries": [{"type": "answer", "text": "some other unrelated text"}],
        }
        matches = cli_main._search_session(data, "nightscout")
        assert matches[0]["type"] == "title"

    def test_no_match_returns_empty_list(self):
        data = {"entries": [{"type": "answer", "text": "totally unrelated"}]}
        assert cli_main._search_session(data, "nightscout") == []

    def test_case_insensitive(self):
        data = {"entries": [{"type": "answer", "text": "NIGHTSCOUT in caps"}]}
        assert len(cli_main._search_session(data, "nightscout")) == 1

    def test_truncates_matched_text_to_200_chars(self):
        long_text = "needle " + ("x" * 300)
        data = {"entries": [{"type": "answer", "text": long_text}]}
        matches = cli_main._search_session(data, "needle")
        assert len(matches[0]["text"]) == 200


# ---------------------------------------------------------------------------
# render_markdown / render_html
# ---------------------------------------------------------------------------

class TestRenderMarkdown:
    FULL_SESSION = {
        "id": "sess-1",
        "tool": {"name": "opencode"},
        "agent": {"name": "claude"},
        "started_at": "2026-01-01T00:00:00Z",
        "ended_at": "2026-01-01T00:05:00Z",
        "entries": [
            {"type": "user-query", "text": "Fix the bug"},
            {"type": "thought", "text": "Looking at the code"},
            {"type": "action", "tool": "bash", "code": "ls -la", "output": "file1\nfile2"},
            {"type": "answer", "text": "Fixed it"},
            {"type": "side-effect", "action": "file_write", "path": "src/app.py"},
        ],
    }

    def test_includes_header_metadata(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "# Agent Session: sess-1" in md
        assert "**Tool:** opencode" in md
        assert "**Agent:** claude" in md
        assert "**Started:** 2026-01-01T00:00:00Z" in md
        assert "**Ended:** 2026-01-01T00:05:00Z" in md

    def test_renders_user_query_section(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "## User" in md
        assert "Fix the bug" in md

    def test_renders_thought_as_blockquote(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "### Thinking" in md
        assert "> Looking at the code" in md

    def test_renders_action_with_code_and_output(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "### Action" in md
        assert "**Tool:** bash" in md
        assert "ls -la" in md
        assert "file1\nfile2" in md

    def test_renders_answer_section(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "### Answer" in md
        assert "Fixed it" in md

    def test_renders_side_effect_with_path(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "### Side Effect" in md
        assert "**Action:** file_write" in md
        assert "**Path:** src/app.py" in md

    def test_includes_footer(self):
        md = cli_main.render_markdown(self.FULL_SESSION)
        assert "*Exported by AgentSON v1*" in md

    def test_missing_fields_default_to_unknown(self):
        md = cli_main.render_markdown({})
        assert "# Agent Session: Unknown" in md
        assert "**Tool:** Unknown" in md
        assert "**Agent:** Unknown" in md
        assert "**Started:** Unknown" in md

    def test_user_query_falls_back_to_query_field(self):
        data = {"entries": [{"type": "user-query", "query": "legacy field name"}]}
        md = cli_main.render_markdown(data)
        assert "legacy field name" in md

    def test_action_without_code_or_output_omits_those_blocks(self):
        data = {"entries": [{"type": "action", "tool": "noop"}]}
        md = cli_main.render_markdown(data)
        assert "**Tool:** noop" in md
        # No fenced code block should be emitted when there's no code/output.
        assert "```" not in md

    def test_side_effect_without_path_omits_path_line(self):
        data = {"entries": [{"type": "side-effect", "action": "state_change"}]}
        md = cli_main.render_markdown(data)
        assert "**Action:** state_change" in md
        assert "**Path:**" not in md

    def test_unknown_entry_type_is_ignored(self):
        data = {"entries": [{"type": "mystery-type", "text": "should not appear literally as a section"}]}
        md = cli_main.render_markdown(data)
        # No section header should be created for an unrecognized type.
        assert "### Mystery" not in md


class TestRenderHtml:
    def test_wraps_markdown_in_pre_tag(self):
        data = {"id": "sess-1", "entries": []}
        html = cli_main.render_html(data)
        assert "<pre>" in html
        assert "</pre>" in html
        assert "# Agent Session: sess-1" in html

    def test_includes_title_with_session_id(self):
        html = cli_main.render_html({"id": "sess-42", "entries": []})
        assert "<title>Agent Session: sess-42</title>" in html

    def test_is_a_complete_html_document(self):
        html = cli_main.render_html({"id": "sess-1", "entries": []})
        assert html.startswith("<!DOCTYPE html>")
        assert "<html>" in html
        assert "</html>" in html


# ---------------------------------------------------------------------------
# cmd_render
# ---------------------------------------------------------------------------

class TestCmdRender:
    def _write_session(self, tmp_path):
        session = {"id": "sess-1", "entries": [{"type": "answer", "text": "done"}]}
        path = tmp_path / "session.agentson"
        path.write_text(json.dumps(session), encoding="utf-8")
        return path

    def test_md_format_prints_to_stdout_without_output(self, tmp_path, capsys):
        input_path = self._write_session(tmp_path)
        args = _ns(input=str(input_path), format="md", output=None)
        cli_main.cmd_render(args)
        out = capsys.readouterr().out
        assert "# Agent Session: sess-1" in out

    def test_md_format_writes_to_output_file(self, tmp_path):
        input_path = self._write_session(tmp_path)
        output_path = tmp_path / "out.md"
        args = _ns(input=str(input_path), format="md", output=str(output_path))
        cli_main.cmd_render(args)
        assert output_path.exists()
        assert "# Agent Session: sess-1" in output_path.read_text(encoding="utf-8")

    def test_html_format_writes_html_document(self, tmp_path):
        input_path = self._write_session(tmp_path)
        output_path = tmp_path / "out.html"
        args = _ns(input=str(input_path), format="html", output=str(output_path))
        cli_main.cmd_render(args)
        assert "<html>" in output_path.read_text(encoding="utf-8")

    def test_unknown_format_exits_1(self, tmp_path, capsys):
        input_path = self._write_session(tmp_path)
        args = _ns(input=str(input_path), format="pdf", output=None)
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_render(args)
        assert exc.value.code == 1
        assert "Unknown format" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# cmd_import
# ---------------------------------------------------------------------------

class TestCmdImport:
    def test_chatgpt_format_success(self, tmp_path, capsys):
        input_path = tmp_path / "conversations.json"
        input_path.write_text("[]", encoding="utf-8")
        output_dir = tmp_path / "out"
        args = _ns(input=str(input_path), output=str(output_dir), format="chatgpt", all_branches=False)

        result = {"id": "chatgpt-1", "tool": {"name": "chatgpt"}, "entries": [{"type": "answer"}]}
        with patch("importers.chatgpt.import_chatgpt", return_value=result) as mock_import:
            cli_main.cmd_import(args)

        mock_import.assert_called_once()
        assert output_dir.is_dir()
        out = capsys.readouterr().out
        assert "Imported: chatgpt-1" in out
        assert "Entries: 1" in out

    def test_unknown_format_exits_1(self, tmp_path, capsys):
        args = _ns(input="whatever.json", output=str(tmp_path), format="unsupported-format")
        with pytest.raises(SystemExit) as exc:
            cli_main.cmd_import(args)
        assert exc.value.code == 1
        assert "Unknown import format" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# cmd_finetune
# ---------------------------------------------------------------------------

class TestCmdFinetune:
    def test_success_writes_to_expected_path_and_prints_summary(self, tmp_path, capsys):
        input_path = tmp_path / "session.agentson"
        input_path.write_text(json.dumps({"id": "sess-1", "entries": []}), encoding="utf-8")
        output_dir = tmp_path / "training"
        args = _ns(input=str(input_path), output=str(output_dir), format="unsloth", include_thoughts=True)

        with patch("exporters.finetune.export_training_data", return_value=[{"a": 1}, {"b": 2}]) as mock_export:
            cli_main.cmd_finetune(args)

        mock_export.assert_called_once()
        _, kwargs = mock_export.call_args
        assert kwargs["format"] == "unsloth"
        assert kwargs["include_thoughts"] is True

        out = capsys.readouterr().out
        assert "Exported 2 training examples" in out
        assert "Compatible with: Unsloth" in out

    def test_olive_format_prints_olive_compatibility_note(self, tmp_path, capsys):
        input_path = tmp_path / "session.agentson"
        input_path.write_text(json.dumps({"id": "sess-1", "entries": []}), encoding="utf-8")
        args = _ns(input=str(input_path), output=str(tmp_path), format="olive", include_thoughts=False)

        with patch("exporters.finetune.export_training_data", return_value=[]):
            cli_main.cmd_finetune(args)

        out = capsys.readouterr().out
        assert "Compatible with: Microsoft Olive, ONNX Runtime" in out


# ---------------------------------------------------------------------------
# main() dispatch
# ---------------------------------------------------------------------------

class TestMainDispatch:
    def test_no_command_prints_help(self, capsys, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["agentson"])
        cli_main.main()
        out = capsys.readouterr().out
        assert "usage" in out.lower()

    def test_search_command_dispatches_to_cmd_search(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["agentson", "search", "needle"])
        with patch.object(cli_main, "cmd_search") as mock_cmd:
            cli_main.main()
        mock_cmd.assert_called_once()
        called_args = mock_cmd.call_args[0][0]
        assert called_args.term == "needle"

    def test_render_command_dispatches_to_cmd_render(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["agentson", "render", "session.agentson", "--format", "html"])
        with patch.object(cli_main, "cmd_render") as mock_cmd:
            cli_main.main()
        mock_cmd.assert_called_once()
        called_args = mock_cmd.call_args[0][0]
        assert called_args.input == "session.agentson"
        assert called_args.format == "html"

    def test_export_command_requires_tool_argument(self, monkeypatch, capsys):
        monkeypatch.setattr(sys, "argv", ["agentson", "export"])
        with pytest.raises(SystemExit) as exc:
            cli_main.main()
        assert exc.value.code != 0
        assert "--tool" in capsys.readouterr().err

    def test_finetune_defaults_include_thoughts_true(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["agentson", "finetune", "session.agentson"])
        with patch.object(cli_main, "cmd_finetune") as mock_cmd:
            cli_main.main()
        called_args = mock_cmd.call_args[0][0]
        assert called_args.include_thoughts is True
        assert called_args.format == "unsloth"

    def test_finetune_no_thoughts_flag_sets_include_thoughts_false(self, monkeypatch):
        monkeypatch.setattr(sys, "argv", ["agentson", "finetune", "session.agentson", "--no-thoughts"])
        with patch.object(cli_main, "cmd_finetune") as mock_cmd:
            cli_main.main()
        called_args = mock_cmd.call_args[0][0]
        assert called_args.include_thoughts is False