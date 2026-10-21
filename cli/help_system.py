"""
AgentSON Encyclopedia — rich TUI help system.

Serves as:
- Instructional manual (Britannica-style)
- First-run onboarding wizard
- Deep-dive help for every adapter, protocol, and command
"""

import sys
import json
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.markdown import Markdown
    from rich.columns import Columns
    from rich.prompt import Confirm, Prompt
    from rich.text import Text
    from rich.box import DOUBLE, HEAVY, ROUNDED, MINIMAL
    from rich.style import Style
    from rich.syntax import Syntax
    from rich.layout import Layout
    from rich.live import Live
    from rich.align import Align
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


_console = Console(force_terminal=True, legacy_windows=False)

# ── Wordmark ────────────────────────────────────────────────────────────
# Generated with figlet's "larry3d" face. Every row is padded to a fixed 65
# columns so the glyph grid stays intact; the SON half begins at column 40.
# Regenerate with: pyfiglet -f larry3d AgentSON
#
# Correction, 2026-10-21: an earlier revision of this comment claimed the
# "banner" face at 59 columns with SON at 35. Measured: 9 rows x exactly 65
# columns, and the split at 40 is the one that yields Agent | SON.

WORDMARK = (
    ' ______                         __    ____    _____   __  __     ',
    '/\\  _  \\                       /\\ \\__/\\  _`\\ /\\  __`\\/\\ \\/\\ \\    ',
    '\\ \\ \\L\\ \\     __      __    ___\\ \\ ,_\\ \\,\\L\\_\\ \\ \\/\\ \\ \\ `\\\\ \\   ',
    " \\ \\  __ \\  /'_ `\\  /'__`\\/' _ `\\ \\ \\/\\/_\\__ \\\\ \\ \\ \\ \\ \\ , ` \\  ",
    '  \\ \\ \\/\\ \\/\\ \\L\\ \\/\\  __//\\ \\/\\ \\ \\ \\_ /\\ \\L\\ \\ \\ \\_\\ \\ \\ \\`\\ \\ ',
    '   \\ \\_\\ \\_\\ \\____ \\ \\____\\ \\_\\ \\_\\ \\__\\\\ `\\____\\ \\_____\\ \\_\\ \\_\\',
    '    \\/_/\\/_/\\/___L\\ \\/____/\\/_/\\/_/\\/__/ \\/_____/\\/_____/\\/_/\\/_/',
    '              /\\____/                                            ',
    '              \\_/__/                                             ',
)
WORDMARK_SON_START = 40
WORDMARK_TAGLINE = "AgentSON Platform — Enterprise Compliance & Audit"

# PLATFORM in the same larry3d face, generated once with pyfiglet and baked
# in as a constant so pyfiglet is never a runtime dependency.
WORDMARK_PLATFORM = (
    ' ____    __       ______  ______  ____    _____   ____                ',
    "/\\  _`\\ /\\ \\     /\\  _  \\/\\__  _\\/\\  _`\\ /\\  __`\\/\\  _`\\   /'\\_/`\\    ",
    '\\ \\ \\L\\ \\ \\ \\    \\ \\ \\L\\ \\/_/\\ \\/\\ \\ \\L\\_\\ \\ \\/\\ \\ \\ \\L\\ \\/\\      \\   ',
    ' \\ \\ ,__/\\ \\ \\  __\\ \\  __ \\ \\ \\ \\ \\ \\  _\\/\\ \\ \\ \\ \\ \\ ,  /\\ \\ \\__\\ \\  ',
    '  \\ \\ \\/  \\ \\ \\L\\ \\\\ \\ \\/\\ \\ \\ \\ \\ \\ \\ \\/  \\ \\ \\_\\ \\ \\ \\\\ \\ \\\\ \\ \\_/\\ \\ ',
    '   \\ \\_\\   \\ \\____/ \\ \\_\\ \\_\\ \\ \\_\\ \\ \\_\\   \\ \\_____\\ \\_\\ \\_\\ \\_\\\\ \\_\\',
    '    \\/_/    \\/___/   \\/_/\\/_/  \\/_/  \\/_/    \\/_____/\\/_/\\/ /\\/_/ \\/_/',
)


def wordmark_text(tagline: str = WORDMARK_TAGLINE) -> Text:
    """The wordmark as one renderable: Agent in brand amber, SON bold.

    The split is by fixed column, not by string search, because the two halves
    share rows in the glyph grid.
    """
    t = Text()
    for i, row in enumerate(WORDMARK):
        if i:
            t.append("\n")
        t.append(row[:WORDMARK_SON_START], style="#ffb000")
        t.append(row[WORDMARK_SON_START:], style="bold #ffb000")
    if tagline:
        t.append("\n\n")
        t.append(f"  {tagline}", style="dim")
    return t


def show_wordmark(tagline: str = WORDMARK_TAGLINE) -> None:
    """Print the logo + tagline above the Encyclopedia.

    Panel width follows the art, not the other way round: the larry3d face is
    65 columns against banner's 59, and a fixed width would clip the 3D
    outline mid-glyph. The tagline sets a floor so it never wraps, and the
    console width caps it so a narrow terminal degrades instead of shredding
    the grid.
    """
    art_w = max(len(r) for r in WORDMARK)
    tag_w = (len(tagline) + 4) if tagline else 0
    width = max(art_w + 4, tag_w + 4, 40)
    width = min(width, max(_console.width - 2, 40))
    _console.print(Panel(
        wordmark_text(tagline),
        box=box.MINIMAL,
        border_style="bold #ffb000",
        width=width,
        padding=(0, 1),
    ))
    _console.print()


# ── Onboarding ──────────────────────────────────────────────────────────

ONBOARDING_FLAG = Path.home() / ".agentson_onboarded"


def needs_onboarding() -> bool:
    return not ONBOARDING_FLAG.exists()


def mark_onboarded():
    ONBOARDING_FLAG.touch()


def show_onboarding():
    """First-run welcome wizard."""
    c = _console

    c.clear()
    c.print()
    c.print(Panel(
        "[bold #ffb000]Welcome to AgentSON[/]\n\n"
        "The universal provenance format for agent sessions.\n"
        "Think of it as the [i]PDF of what agents do[/] — a portable,\n"
        "vendor-neutral record of every action, thought, and observation.",
        title="[bold]First Run[/]",
        box=box.DOUBLE,
        border_style="bold #ffb000",
        width=60,
    ))
    c.print()
    c.print("  [dim]AgentSON canonicalises agent traces from every major protocol[/]")
    c.print("  [dim]into one portable JSONL format. Export to any tool.[/]")
    c.print("  [dim]Distribute via Docker Hub or LXD Hub.[/]")
    c.print()

    if Confirm.ask("  Would you like a quick tour?", default=True):
        show_tour()

    c.print("\n  [dim]Run [bold]agentson help[/] any time to explore further.[/]")
    c.print()

    if Confirm.ask("  Show this on future runs?", default=False):
        c.print("  [dim]You can re-enable onboarding with: agentson help --onboard[/]")
    else:
        mark_onboarded()


def show_tour():
    """5-step quick tour."""
    c = _console
    steps = [
        ("[bold #5b9ef6]What is AgentSON?[/]",
         "A [i]provenance format[/] — like JSON Lines, but with 12 semantic\n"
         "primitives that capture everything an agent does:\n"
         "  [blue]coordination[/] · [green]execution[/] · [amber]input[/]"),
        ("[bold #a0d060]Protocol Adapters[/]",
         "MCP · A2A · AGNTCY · ChatGPT\n"
         "Each adapter canonicalises a protocol's traces into AgentSON's\n"
         "12 primitives. No silent data loss — every unmapped field\n"
         "is recorded in a [i]_loss[/] array."),
        ("[bold #ffb000]Export & Read[/]",
         "OpenCode · MiniMax · Antigravity IDE · Chrome DevTools\n"
         "Claude Code · FreeStyle Libre 2\n"
         "Export from any supported tool with: [bold]agentson export[/]"),
        ("[bold #e05040]Validation & Redaction[/]",
         "Validate against the canonical v1.2 schema:\n"
         "  [bold]agentson validate[/]\n"
         "Redact PII before sharing:\n"
         "  [bold]agentson redact[/]"),
        ("[bold #a070d0]Distribution[/]",
         "Publish sessions as OCI artifacts to Docker Hub or as\n"
         "system containers to LXD Hub. Cross-registry compatible.\n"
         "  [bold]agentson publish --registry docker[/]"),
    ]
    for i, (title, body) in enumerate(steps, 1):
        c.clear()
        c.print()
        c.print(Panel(
            f"[dim]Step {i} of {len(steps)}[/]\n\n{body}",
            title=title,
            box=box.ROUNDED,
            border_style="bold #ffb000",
            width=64,
        ))
        c.print()
        if i < len(steps):
            c.input("  [dim]Press Enter to continue...[/]")
    c.clear()
    c.print()
    c.print(Panel(
        "[bold]That's the gist.[/]\n\n"
        "Run [bold]agentson help[/] for the full encyclopedia.\n"
        "Run [bold]agentson help <topic>[/] for deep dives.\n"
        "Run [bold]agentson help --adapter mcp[/] for protocol stories.",
        box=box.ROUNDED,
        border_style="bold #a0d060",
        width=60,
    ))
    c.input("\n  [dim]Press Enter to return...[/]")


# ── Knowledge Base ─────────────────────────────────────────────────────

TOPICS = {
    "agentson": lambda c: Panel(
        "[bold #ffb000]AgentSON[/] — The universal provenance format.\n\n"
        "A portable, vendor-neutral JSONL format that records what agents did:\n"
        "every action, thought, observation, tool call, and system event.\n\n"
        "Twelve semantic primitives in three categories:\n"
        "  [blue]Coordination[/]  — stream-meta, handoff, presence, capabilities\n"
        "  [green]Execution[/]     — action, observation, thought, side-effect, answer\n"
        "  [amber]Input[/]         — user-query, user-feedback, system-event\n\n"
        "Every adapter records losses transparently. No silent data loss.",
        title="[bold]AgentSON[/]",
        box=box.DOUBLE,
        border_style="bold #ffb000",
    ),

    "mcp": lambda c: Panel(
        "[bold #5b9ef6]Model Context Protocol[/]\n"
        "[dim]Created by Anthropic · 2024[/]\n\n"
        "MCP standardises how AI agents discover and invoke tools, access\n"
        "resources, and interact with prompts — over stdio or HTTP.\n\n"
        "[bold]Background[/]\n"
        "Before MCP, every agent needed bespoke integrations for every tool.\n"
        "MCP gave agents a universal protocol: like USB for peripherals, but\n"
        "for agent capabilities. It was released as open source in late 2024\n"
        "and quickly became the de facto standard for tool-enabled agents.\n\n"
        "[bold]Why it matters[/]\n"
        "MCP is the most widely deployed agent protocol. If your agent calls\n"
        "tools, it almost certainly speaks MCP. AgentSON canonicalises MCP's\n"
        "tool_call/tool_result pattern into action/observation primitives,\n"
        "capturing the provenance MCP itself doesn't store.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  tool_call   ->  action\n"
        "  tool_result ->  observation\n"
        "  error       ->  system-event\n"
        "  resources   ->  capabilities\n\n"
        "[dim]Code: importers/mcp.py[/]",
        title="[bold]MCP Adapter[/]",
        box=box.HEAVY,
        border_style="bold #5b9ef6",
    ),

    "a2a": lambda c: Panel(
        "[bold #a0d060]Agent-to-Agent[/]\n"
        "[dim]Created by Google · 2025[/]\n\n"
        "A2A defines how agents talk to each other — task delegation, handoff,\n"
        "and multi-agent coordination over HTTP.\n\n"
        "[bold]Background[/]\n"
        "As the agent ecosystem grew, a single-agent architecture hit its limits.\n"
        "Google designed A2A for the multi-agent world: one agent delegates a\n"
        "task to another, monitors progress, and collects results. A2A is\n"
        "asymmetric — agents can be running different models, on different stacks.\n\n"
        "[bold]Why it matters[/]\n"
        "A2A is the closest thing to an inter-agent lingua franca. AgentSON\n"
        "captures the handoff and delegation patterns that A2A enables, recording\n"
        "the full multi-agent session as provenance.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  task.send   ->  action\n"
        "  task.result ->  observation\n"
        "  handoff     ->  handoff\n"
        "  error       ->  system-event\n\n"
        "[dim]Code: importers/a2a.py[/]",
        title="[bold]A2A Adapter[/]",
        box=box.HEAVY,
        border_style="bold #a0d060",
    ),

    "agntcy": lambda c: Panel(
        "[bold #ffb000]AGNTCY[/]\n"
        "[dim]Community standard · 2025[/]\n\n"
        "A standardised agent runtime protocol with task lifecycle, step\n"
        "execution, and artifact production.\n\n"
        "[bold]Background[/]\n"
        "AGNTCY emerged from the agent open-source community as a lightweight\n"
        "alternative to heavier orchestration frameworks. It focuses on the\n"
        "atomic unit of agent work: a task with steps, each step producing\n"
        "artifacts. Think of it as a standardised way to run and observe agents.\n\n"
        "[bold]Why it matters[/]\n"
        "AGNTCY bridges the gap between ad-hoc agent scripts and production\n"
        "workflows. AgentSON captures AGNTCY's task/step/artifact model as\n"
        "action/observation/thought primitives, preserving execution order.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  task.start  ->  system-event\n"
        "  step        ->  action\n"
        "  artifact    ->  observation\n"
        "  thought     ->  thought\n\n"
        "[dim]Code: importers/agntcy.py[/]",
        title="[bold]AGNTCY Adapter[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "chatgpt": lambda c: Panel(
        "[bold #a070d0]ChatGPT[/]\n"
        "[dim]Created by OpenAI · 2022[/]\n\n"
        "Import conversation exports from ChatGPT's native JSON format into\n"
        "AgentSON sessions.\n\n"
        "[bold]Background[/]\n"
        "ChatGPT popularised the conversational AI interface. Its export format\n"
        "(a JSON array of messages with roles, timestamps, and content) was one\n"
        "of the earliest widely-available agent session dumps. AgentSON imports\n"
        "these exports to give them provenance structure.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  user message     ->  user-query\n"
        "  assistant reply  ->  answer\n"
        "  feedback         ->  user-feedback\n"
        "  system message   ->  system-event\n\n"
        "[dim]Code: importers/chatgpt.py[/]",
        title="[bold]ChatGPT Adapter[/]",
        box=box.HEAVY,
        border_style="bold #a070d0",
    ),

    "opencode": lambda c: Panel(
        "[bold #5b9ef6]OpenCode[/]\n"
        "[dim]Created by Anomaly · 2024[/]\n\n"
        "Read agent sessions from OpenCode's SQLite database.\n\n"
        "[bold]Background[/]\n"
        "OpenCode is the open-source CLI for AI-assisted coding. It stores\n"
        "session history in a local SQLite database. AgentSON reads this\n"
        "database directly, turning every coding session into portable provenance.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  SQLite rows -> AgentSON primitives\n\n"
        "[dim]Code: readers/opencode.py[/]",
        title="[bold]OpenCode Reader[/]",
        box=box.HEAVY,
        border_style="bold #5b9ef6",
    ),

    "chrome-devtools": lambda c: Panel(
        "[bold #e05040]Chrome DevTools Protocol[/]\n"
        "[dim]Created by Google · 2011[/]\n\n"
        "Capture browser automation and DevTools interactions as provenance.\n\n"
        "[bold]Background[/]\n"
        "CDP is the wire protocol behind Chrome DevTools — every inspector\n"
        "panel, every debugger breakpoint, every network request flows through\n"
        "it. AgentSON wraps CDP traffic in session structure, turning browser\n"
        "automation into auditable provenance.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "  CDP commands   ->  action\n"
        "  CDP events     ->  observation\n"
        "  breakpoints    ->  system-event\n\n"
        "[dim]Code: readers/chrome_devtools.py[/]",
        title="[bold]Chrome DevTools Reader[/]",
        box=box.HEAVY,
        border_style="bold #e05040",
    ),

    "claude-code": lambda c: Panel(
        "[bold #a070d0]Claude Code[/]\n"
        "[dim]Created by Anthropic · 2025[/]\n\n"
        "Export sessions from Claude Code's SQLite log database.\n\n"
        "[bold]Background[/]\n"
        "Claude Code is Anthropic's terminal-based AI coding agent. It stores\n"
        "conversation history in a local SQLite database. AgentSON reads this\n"
        "and maps it to the 12-primitive ontology.\n\n"
        "[bold]AgentSON mapping[/]\n"
        "    user messages   ->  user-query\n"
        "  assistant messages ->  answer / thought\n"
        "  tool calls         ->  action\n"
        "  tool results       ->  observation\n\n"
        "[dim]Code: readers/claude_code.py[/]",
        title="[bold]Claude Code Reader[/]",
        box=box.HEAVY,
        border_style="bold #a070d0",
    ),

    "libre": lambda c: Panel(
        "[bold #a0d060]FreeStyle Libre 2[/]\n"
        "[dim]Created by Abbott Laboratories · 2014[/]\n\n"
        "Convert continuous glucose monitor CSV exports into AgentSON format.\n\n"
        "[bold]Background[/]\n"
        "The FreeStyle Libre 2 is a continuous glucose monitor used by people\n"
        "with diabetes. It exports readings as CSV files. AgentSON imports\n"
        "these as time-series observations, enabling integration with AI-driven\n"
        "health monitoring and alerting systems.\n\n"
        "[bold]Why it matters[/]\n"
        "AgentSON wasn't designed for health data — but its temporal provenance\n"
        "model maps naturally to time-series sensor readings. This demonstrates\n"
        "the format's generality beyond AI agents.\n\n"
        "[dim]Code: readers/libre.py[/]",
        title="[bold]FreeStyle Libre 2 Reader[/]",
        box=box.HEAVY,
        border_style="bold #a0d060",
    ),

    "validate": lambda c: Panel(
        "[bold #a0d060]agentson validate[/]\n\n"
        "Validate .agentson files against the canonical v1.2 JSON Schema.\n\n"
        "Usage:\n"
        "  agentson validate <file_or_directory>\n\n"
        "Validates every .agentson file against spec/v1.2.json's discriminated\n"
        "union schema. Returns pass/fail per file with detailed error messages.\n\n"
        "[dim]70+ schema tests in tests/test_schema.py[/]",
        title="[bold]Validate Command[/]",
        box=box.HEAVY,
        border_style="bold #a0d060",
    ),

    "redact": lambda c: Panel(
        "[bold #e05040]agentson redact[/]\n\n"
        "Redact PII (emails, API keys, phone numbers) from AgentSON files\n"
        "before sharing or publishing.\n\n"
        "Usage:\n"
        "  agentson redact <input> --output <output> --all\n\n"
        "Scans every text field in every entry for regex-matched PII patterns\n"
        "and replaces them with placeholder tokens. Original values are\n"
        "irreversibly hashed — no way to recover them from the redacted file.\n\n"
        "[dim]Code: tools/pii_redactor.py[/]",
        title="[bold]Redact Command[/]",
        box=box.HEAVY,
        border_style="bold #e05040",
    ),

    "publish": lambda c: Panel(
        "[bold #a070d0]agentson publish[/]\n\n"
        "Publish AgentSON sessions to Docker Hub or LXD Hub.\n\n"
        "Usage:\n"
        "  agentson publish <file> --registry docker --tag my-session:v1 --push\n\n"
        "Packs the .agentson file as an OCI artifact (Docker) or system\n"
        "container image (LXD). Cross-registry compatible — publish to Docker,\n"
        "pull from LXD.\n\n"
        "[dim]Code: tools/distribute.py[/]",
        title="[bold]Publish Command[/]",
        box=box.HEAVY,
        border_style="bold #a070d0",
    ),

    "runbook": lambda c: Panel(
        "[bold #ffb000]agentson runbook (planned)[/]\n\n"
        "Replay an AgentSON session as a runbook — execute every action\n"
        "step-by-step, pipe outputs, record the replay as new provenance.\n\n"
        "Usage:\n"
        "  agentson runbook <file> [--from <id>] [--to <id>]\n\n"
        "Turns any session into an executable, auditable workflow.\n"
        "Provenance of provenance.",
        title="[bold]Runbook Command[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "gemini": lambda c: Panel(
        "[bold #ffb000]agentson export --tool gemini[/]\n\n"
        "Reads Google AI Studio / Gemini conversation exports — the JSON\n"
        "files Chrome saves as [i]Google-Search_<topic>_<stamp>.json[/].\n"
        "Each message carries id, chatGroupId, role, model, displayModel,\n"
        "contents, created_at, updated_at.\n\n"
        "Usage:\n"
        "  agentson list --tool gemini --limit 5\n"
        "  agentson export --tool gemini --all --input <file.json> --output .\n\n"
        "[dim]Code: readers/gemini.py[/]",
        title="[bold]Gemini Reader[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "platform": lambda c: Panel(
        "[bold #ffb000]agentson platform <subcommand>[/]\n\n"
        "[bold]scan[/]     detect tools, crawl sessions, classify, write report\n"
        "[bold]detect[/]   list installed AI tools and their data locations\n"
        "[bold]serve[/]    local preview server (add --watch for npm-dev reload)\n"
        "[bold]license[/]  --dev writes a local dev licence (testing only)\n"
        "[bold]structure[/] premium data pipeline — graph / CSV / training export\n"
        "[bold]doctor[/]   network troubleshooting probes (see [i]doctor[/])\n\n"
        "Usage:\n"
        "  agentson platform serve --port 8090 --watch\n\n"
        "[dim]Code: agentson_platform/[/]",
        title="[bold]Platform Commands[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "grc-export": lambda c: Panel(
        "[bold #ffb000]agentson grc-export --secure --post <url>[/]\n\n"
        "Premium. Builds a vendor-neutral GRC evidence package from a scan\n"
        "digest, optionally signs it, and can POST it to an ingestion\n"
        "endpoint. Signing is ECDSA P-256 with a local key; the public key\n"
        "travels with the package so the receiver verifies without the\n"
        "private key.\n\n"
        "Usage:\n"
        "  agentson grc-export --digest report.json --secure --output e.json\n"
        "  agentson grc-export --digest report.json --secure \\\n"
        "      --post http://localhost:8090/api/evidence\n\n"
        "[dim]Code: cli/grc_export.py, cli/signing.py[/]",
        title="[bold]GRC Export (premium)[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "structure": lambda c: Panel(
        "[bold #ffb000]agentson platform structure[/] (premium)\n\n"
        "The data pipeline. Reads .agentson JSONL streams and emits:\n"
        "  graph.json         entities + relations (agent, session, tool)\n"
        "  entities.csv       tabular for Excel / GRC import\n"
        "  relations.csv      relation table\n"
        "  training_module.jsonl  entry stream for fine-tuning\n\n"
        "Only relations present in the stream are emitted — nothing inferred.\n\n"
        "Usage:\n"
        "  agentson platform structure --input . --output ./structure/",
        title="[bold]Structure Pipeline (premium)[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "doctor": lambda c: Panel(
        "[bold #ffb000]agentson platform doctor[/]\n\n"
        "Read-only network probes for enterprise troubleshooting. No\n"
        "telemetry; each probe reports ok/error plus elapsed_ms.\n\n"
        "  --dns HOST        resolve a hostname\n"
        "  --tcp HOST:PORT   TCP connectivity\n"
        "  --tls HOST:PORT   TLS handshake + certificate details\n"
        "  --http URL        HTTP status + body preview\n"
        "  --proxy           show proxy environment variables\n"
        "  --offline         confirm the core makes no DNS / TCP call\n\n"
        "[dim]Code: agentson_platform/netdoctor.py[/]",
        title="[bold]Network Doctor[/]",
        box=box.HEAVY,
        border_style="bold #ffb000",
    ),

    "telemetry": lambda c: Panel(
        "[bold #ffb000]Telemetry — exposed, not shipped[/]\n\n"
        "AgentSON ships no telemetry. The core licence check reads a local\n"
        "file only; the free core performs 0 DNS lookups and 0 TCP\n"
        "connects (measured under socket instrumentation).\n\n"
        "A telemetry module may be mounted by a developer for their own\n"
        "deployments. It is documented, not bundled.\n\n"
        "  Docs: /internal/security mkdocs (telemetry mount page)",
        title="[bold]Telemetry[/]",
        box=box.MINIMAL,
        border_style="dim",
    ),

    "capi": lambda c: Panel(
        "[dim]capi — Cognitive Agent Protocol Interface[/]\n"
        "[dim]by kevin-dp · conceptual reference[/]\n\n"
        "A capability advertising protocol with performance tokens and\n"
        "capability manifests. AgentSON's [i]presence[/] and [i]capabilities[/]\n"
        "primitives draw inspiration from capi's model.\n\n"
        "[bold]Status:[/] [red]Conceptual reference[/] — no adapter code.\n"
        "Listed here because capi informed the ontology design, not because\n"
        "AgentSON integrates with it today.",
        title="[bold]capi (Reference)[/]",
        box=box.MINIMAL,
        border_style="dim",
    ),

    "toast": lambda c: Panel(
        "[dim]TOAST — Test Oracle Assertion Spec Technology[/]\n"
        "[dim]by bivalve-ai · conceptual reference[/]\n\n"
        "A format for verifiable assertions and hierarchical test oracles.\n"
        "AgentSON's [i]side-effect[/] primitive draws inspiration from TOAST's\n"
        "assertion model.\n\n"
        "[bold]Status:[/] [red]Conceptual reference[/] — no adapter code.\n"
        "Listed here because TOAST informed the ontology design, not because\n"
        "AgentSON integrates with it today.",
        title="[bold]TOAST (Reference)[/]",
        box=box.MINIMAL,
        border_style="dim",
    ),
}


# ── Encyclopedia Pages ────────────────────────────────────────────────


def show_help_page(topic: str):
    """Show a single topic's help page."""
    if not RICH_AVAILABLE:
        print(f"Help: {topic} — install 'rich' for the full TUI experience")
        return

    c = _console
    c.clear()

    if topic in TOPICS:
        c.print()
        c.print(TOPICS[topic](c))
        c.print()
    else:
        c.print(f"\n  [red]Unknown topic:[/] {topic}")
        c.print("  Run [bold]agentson help[/] for available topics.\n")


def show_encyclopedia():
    """Show the full table of contents."""
    if not RICH_AVAILABLE:
        print("AgentSON Encyclopedia — install 'rich' for the full TUI")
        return

    c = _console
    c.clear()
    show_wordmark()

    # Header
    c.print(Panel(
        "[bold #ffb000]AgentSON Encyclopedia[/]\n"
        "[dim]AgentSON Platform — Enterprise Compliance & Audit — explained[/]\n\n"
        "[dim]Select a topic below or run:[/]\n"
        "[bold]  agentson help <topic>[/]",
        box=box.DOUBLE,
        border_style="bold #ffb000",
        width=60,
    ))
    c.print()

    # Table of contents
    toc = Table(
        box=box.MINIMAL,
        show_header=True,
        header_style="bold #ffb000",
        border_style="dim",
        padding=(0, 2),
    )
    toc.add_column("Topic", width=20)
    toc.add_column("Description", width=50)

    toc.add_row("[bold]agentson[/]", "The format itself — 12 primitives explained")
    toc.add_row("", "")
    toc.add_row("[bold #5b9ef6]Protocol Adapters[/]", "")
    toc.add_row("  mcp", "Model Context Protocol — Anthropic")
    toc.add_row("  a2a", "Agent-to-Agent — Google")
    toc.add_row("  agntcy", "Community agent runtime protocol")
    toc.add_row("  chatgpt", "ChatGPT conversation export importer")
    toc.add_row("", "")
    toc.add_row("[bold #a0d060]Readers (Export Sources)[/]", "")
    toc.add_row("  opencode", "OpenCode SQLite reader")
    toc.add_row("  claude-code", "Claude Code SQLite reader")
    toc.add_row("  chrome-devtools", "Chrome DevTools Protocol reader")
    toc.add_row("  libre", "FreeStyle Libre 2 CSV reader")
    toc.add_row("", "")
    toc.add_row("[bold #ffb000]CLI Commands[/]", "")
    toc.add_row("  validate", "Validate against v1.2 schema")
    toc.add_row("  redact", "Redact PII before sharing")
    toc.add_row("  publish", "Publish to Docker Hub / LXD Hub")
    toc.add_row("  runbook", "Replay session as runbook (planned)")
    toc.add_row("  telemetry", "Telemetry mount docs — see /internal/security mkdocs (dev only; not shipped)")
    toc.add_row("", "")
    toc.add_row("[dim]Conceptual References[/]", "")
    toc.add_row("  capi", "kevin-dp session protocol (conceptual)")
    toc.add_row("  toast", "bivalve-ai assertion format (conceptual)")
    toc.add_row("  gemini", "Google AI Studio export reader")
    toc.add_row("  platform", "Scan / detect / serve / license / structure / doctor")
    toc.add_row("  grc-export", "Premium evidence package (signed)")
    toc.add_row("  structure", "Premium graph / CSV / training pipeline")
    toc.add_row("  doctor", "Network troubleshooting probes")
    toc.add_row("  telemetry", "Mount (dev only) — see /internal/security mkdocs")

    c.print(toc)
    c.print()

    # Prompt for interactive browsing
    if needs_onboarding():
        return

    topic = Prompt.ask(
        "  [dim]Enter a topic to explore (or Enter to exit)[/]",
        default="",
    )
    if topic.strip():
        topic = topic.strip().lower()
        if topic in TOPICS:
            show_help_page(topic)
            c.input("\n  [dim]Press Enter to return to TOC...[/]")
            show_encyclopedia()
        else:
            c.print(f"  [red]Unknown topic:[/] {topic}")
            c.input("  [dim]Press Enter to continue...[/]")
            show_encyclopedia()


# ── Rich --help Decorator ──────────────────────────────────────────────


def build_rich_help(parser, command: str | None = None) -> str:
    """Return a rich-formatted help string for argparse."""
    if not RICH_AVAILABLE:
        return parser.format_help()

    c = Console(force_terminal=True)
    with c.capture() as capture:
        c.print()
        c.print(Panel(
            "[bold #ffb000]AgentSON CLI[/]\n"
            "[dim]Universal provenance for agent sessions[/]",
            box=box.DOUBLE,
            border_style="bold #ffb000",
        ))
        c.print()
        if command:
            c.print(f"  [bold]{command}[/] — {parser.description or ''}")
        else:
            c.print("  [bold]Usage:[/] agentson <command> [options]")
            c.print("  Run [bold]agentson help <topic>[/] for the encyclopedia.\n")
    return capture.get()


# ── Entry ──────────────────────────────────────────────────────────────


def init_help_system():
    """Call at CLI startup to check for onboarding."""
    if RICH_AVAILABLE and needs_onboarding():
        try:
            show_onboarding()
        except (EOFError, KeyboardInterrupt):
            mark_onboarded()
            _console.print()

