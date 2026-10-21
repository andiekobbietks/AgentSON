"""
AgentSON file-association installer -- graphical front end.

Registers the .agentson file type so Explorer offers "Open with AgentSON
Session" and double-clicking a session renders it in the browser.

This is a THIN front end. Every registry decision lives in
register_agentson_assoc.ps1; this file only shows a window and runs it as a
subprocess. Duplicating the registry logic here would create a second
implementation that drifts the first time either changes.

Run with pythonw.exe so no console window appears behind the GUI:

    pythonw.exe agentson_installer_gui.py

The wordmark art is imported from cli.help_system rather than copied, so if
the art is ever regenerated this window follows it.

Colour notes, from measured WCAG contrast:
  amber #ffb000 on #0d1117  -> 10.33:1  (AAA)
  amber #ffb000 on #ffffff  ->  1.83:1  (FAILS)
So the ground is dark. Amber is never used as ink on a light background.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tkinter as tk
from pathlib import Path
from tkinter import font as tkfont, messagebox, scrolledtext

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
PS1 = HERE / "register_agentson_assoc.ps1"

sys.path.insert(0, str(REPO))

# Brand palette.
AMBER = "#ffb000"
GROUND = "#0d1117"
PANEL = "#161b22"
MUTED = "#9aa4b0"
TEXT = "#e6edf3"
OK = "#3fb950"
BAD = "#f85149"
BUTTON_BG = "#21262d"
BUTTON_EDGE = "#30363d"

MONO = "Consolas"      # present on every Windows install; keeps the art aligned
MONO_FALLBACK = "Courier New"


def _mono(root: tk.Tk, size: int, bold: bool = False) -> tkfont.Font:
    """A monospace font that exists on this machine.

    The ASCII art depends on every glyph being the same width. A proportional
    font would shred the glyph grid, so the family is not left to chance.
    """
    available = set(tkfont.families(root))
    for family in (MONO, MONO_FALLBACK, "Lucida Console", "Courier"):
        if family in available:
            return tkfont.Font(family=family, size=size, weight="bold" if bold else "normal")
    return tkfont.Font(family="TkFixedFont", size=size, weight="bold" if bold else "normal")


def load_wordmark():
    """The art, from its single owner in the CLI.

    Returns (rows, son_start, tagline, error). On failure the GUI still opens
    and says why, rather than dying with a traceback nobody can read.
    """
    try:
        from cli.help_system import (
            WORDMARK,
            WORDMARK_SON_START,
            WORDMARK_TAGLINE,
        )

        return WORDMARK, WORDMARK_SON_START, WORDMARK_TAGLINE, None
    except Exception as exc:  # surfaced in the window, never swallowed
        return (), 0, "", "%s: %s" % (type(exc).__name__, exc)


class Installer(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AgentSON file association")
        self.configure(bg=GROUND)

        self.rows, self.son_start, self.tagline, self.wordmark_error = load_wordmark()

        self.mono = _mono(self, 11)
        self.mono_bold = _mono(self, 11, bold=True)

        self._build()

        # Size the window to the art rather than guessing: 66 columns at the
        # chosen font, measured, plus padding.
        char_w = self.mono.measure("M")
        width = max(char_w * 66 + 48, 460)
        self.minsize(width, 560)
        self.geometry("%dx640" % width)

    # ---------------------------------------------------------------- build

    def _build(self) -> None:
        outer = tk.Frame(self, bg=GROUND, padx=20, pady=18)
        outer.pack(fill="both", expand=True)

        # ---- wordmark -------------------------------------------------
        art = tk.Text(
            outer,
            height=len(self.rows) or 1,
            width=66,
            bg=PANEL,
            fg=AMBER,
            font=self.mono,
            relief="flat",
            wrap="none",
            padx=14,
            pady=12,
            insertwidth=0,
            highlightthickness=0,
        )
        art.tag_configure("agent", foreground=AMBER)
        art.tag_configure("son", foreground=AMBER, font=self.mono_bold)
        if self.rows:
            for i, row in enumerate(self.rows):
                if i:
                    art.insert("end", "\n")
                # Split by fixed column, not by searching for text: the two
                # halves share rows in the glyph grid.
                art.insert("end", row[: self.son_start], "agent")
                art.insert("end", row[self.son_start :], "son")
        elif self.wordmark_error:
            art.insert("end", "(wordmark unavailable)\n" + self.wordmark_error, "agent")
        art.configure(state="disabled")
        art.pack(fill="x")

        tag = tk.Label(
            outer,
            text=self.tagline or "",
            bg=GROUND,
            fg=MUTED,
            font=("Segoe UI", 9),
            justify="left",
        )
        tag.pack(fill="x", pady=(10, 14), anchor="w")

        # ---- buttons --------------------------------------------------
        buttons = tk.Frame(outer, bg=GROUND)
        buttons.pack(fill="x")

        self.btn_register = self._button(
            buttons, "Register .agentson files", self.register
        )
        self.btn_remove = self._button(
            buttons, "Remove the association", self.unregister
        )
        self.btn_register.pack(side="left", padx=(0, 10))
        self.btn_remove.pack(side="left")

        # ---- status ---------------------------------------------------
        self.status = tk.Label(
            outer,
            text="Ready.",
            bg=GROUND,
            fg=MUTED,
            font=("Segoe UI", 9),
            anchor="w",
            justify="left",
        )
        self.status.pack(fill="x", pady=(14, 6))

        # ---- output ---------------------------------------------------
        self.output = scrolledtext.ScrolledText(
            outer,
            height=10,
            bg=PANEL,
            fg=TEXT,
            font=("Consolas", 9),
            relief="flat",
            wrap="word",
            padx=10,
            pady=8,
            insertwidth=0,
            highlightthickness=0,
        )
        self.output.configure(state="disabled")
        self.output.pack(fill="both", expand=True)

    def _button(self, parent, label, command) -> tk.Button:
        btn = tk.Button(
            parent,
            text=label,
            command=command,
            bg=BUTTON_BG,
            fg=TEXT,
            activebackground="#30363d",
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=BUTTON_EDGE,
            font=("Segoe UI", 9),
            padx=16,
            pady=7,
            cursor="hand2",
        )
        return btn

    # ------------------------------------------------------------- actions

    def _set_status(self, message: str, colour: str = MUTED) -> None:
        self.status.configure(text=message, fg=colour)
        self.update_idletasks()

    def _append(self, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")
        self.update_idletasks()

    def _clear(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def _run(self, *args: str) -> None:
        if not PS1.exists():
            messagebox.showerror(
                "Installer missing",
                "Expected the PowerShell installer beside this file:\n\n%s" % PS1,
            )
            return

        powershell = shutil.which("powershell") or "powershell.exe"
        command = [
            powershell,
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(PS1),
            *args,
        ]

        self._clear()
        self._set_status("Running...", MUTED)
        self._append("$ %s\n\n" % " ".join(command))

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=120,
            )
        except Exception as exc:
            self._append("\n%s: %s\n" % (type(exc).__name__, exc))
            self._set_status("Failed to run the installer.", BAD)
            return

        for line in (result.stdout or "").splitlines():
            self._append(line + "\n")
        if result.stderr:
            self._append("\n-- stderr --\n")
            for line in result.stderr.splitlines():
                self._append(line + "\n")

        if result.returncode == 0:
            self._set_status("Done (exit 0).", OK)
        else:
            self._set_status("Finished with exit code %d." % result.returncode, BAD)

    def register(self) -> None:
        self._run()

    def unregister(self) -> None:
        self._run("-Uninstall")


def main() -> int:
    try:
        app = Installer()
    except Exception as exc:
        # A GUI that cannot open must still say why. messagebox works without
        # a root window.
        messagebox.showerror(
            "AgentSON installer",
            "Could not start the installer window.\n\n%s: %s" % (type(exc).__name__, exc),
        )
        return 1
    app.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
