# SOP-004: Export AI-Agent Sessions

**Status:** Maintained example procedure; reader coverage varies by source version.  
**Last reviewed:** 25 November 2026

## Purpose

Export sessions from supported local AI-agent tools into AgentSON for local search, backup, inspection and context-packet creation. This procedure does not provide universal cross-tool hydration or runtime restoration.

## Prerequisites

- AgentSON installed in a local Python environment.
- A supported source application and an accessible local session store/export.
- Permission to access and process the selected session data.
- A secure output directory.

## Check current reader support

The installed CLI help and the repository's reader conformance matrix are authoritative. Reader selectors and source versions can change:

~~~powershell
python -m cli.main --help
python -m cli.main export --help
~~~

Examples below use OpenCode and MiniMax. Other reader selectors may be available in the installed version.

## List sessions

~~~powershell
python -m cli.main list --tool opencode
python -m cli.main list --tool minimax
~~~

## Export a specific session

~~~powershell
python -m cli.main export --tool opencode --session SESSION_ID --output "$HOME\Downloads"
python -m cli.main export --tool minimax --session SESSION_ID --output "$HOME\Downloads"
~~~

Replace SESSION_ID with an identifier returned by the list command.

## Export all sessions

~~~powershell
python -m cli.main export --tool opencode --all --output "$HOME\Downloads"
python -m cli.main export --tool minimax --all --output "$HOME\Downloads"
~~~

Exporting all sessions may collect sensitive prompts, tool outputs, paths, source code and personal data. Prefer a selected session and review the output.

## Validate and inspect

~~~powershell
python -m cli.main validate "$HOME\Downloads\SESSION_FILE.agentson"
python -m cli.main render "$HOME\Downloads\SESSION_FILE.agentson" --format md --output "$HOME\Downloads\SESSION_FILE.md"
~~~

Use the actual filename produced by the export command.

## Context continuation

A reviewed Markdown context packet can be created with the resume workflow. It is not a runtime checkpoint and does not restore hidden prompts, credentials, permissions, live processes, editor buffers or provider-private state. The experimental OpenCode destination consumer is a limited, separate adapter; it does not provide general cross-harness hydration or automatic tool replay.

## Privacy

Treat exported archives as sensitive. Pattern-based redaction is best-effort, and the OpenCode consumer may store the complete original archive alongside the screened packet. Inspect and redact before sharing or importing. Use localhost and disposable sessions only for the current experimental OpenCode consumer.
