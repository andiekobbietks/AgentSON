# Windows file association for `.agentson`

Makes Windows offer **AgentSON Session** when you right-click a `.agentson`
file, and opens it in the browser when you double-click one.

Before this, `.agentson` was registered nowhere — Explorer showed no
"Open with AgentSON" entry, because no ProgId existed.

## Use

### Double-click (no terminal, no administrator rights)

Run **`Install AgentSON files.cmd`**. It opens the graphical installer, which
shows the AgentSON wordmark and has two buttons:

- **Register .agentson files**
- **Remove the association**

The `.cmd` is a `.cmd` rather than a `.ps1` on purpose: PowerShell's execution
policy refuses to run unsigned `.ps1` files, so a double-clicked `.ps1` does
nothing and the user is given no explanation. A `.cmd` is not subject to that
policy.

If Python is not on the machine, the `.cmd` falls back to the console
installer automatically.

### From a terminal

```powershell
cd installers\windows
.\register_agentson_assoc.ps1
```

Then right-click any `.agentson` file → **Open with** → **AgentSON Session**.

Undo it:

```powershell
.\register_agentson_assoc.ps1 -Uninstall
```

### The GUI directly

```powershell
pythonw.exe installers\windows\agentson_installer_gui.py
```

Use `pythonw.exe`, not `python.exe` — `pythonw` opens no console window behind
the GUI.

## Files

| File | Role |
|---|---|
| `Install AgentSON files.cmd` | Double-click launcher. Picks the GUI, falls back to the console installer. |
| `agentson_installer_gui.py` | The window. A thin front end — it runs the `.ps1` and shows its output. |
| `register_agentson_assoc.ps1` | The engine. Every registry decision lives here. |
| `agentson-viewer.cmd` | The handler Windows runs on double-click. |
| `agentson-viewer.path` | Generated, machine-specific, gitignored. Never committed. |

## What it does

| Step | Where |
|---|---|
| `HKCU\Software\Classes\.agentson` | extension → ProgId |
| `HKCU\Software\Classes\AgentSON.File` | ProgId, described as "AgentSON Session" |
| `…\AgentSON.File\shell\open\command` | the command Windows runs |
| `agentson-viewer.path` | the CLI's absolute path, as a fallback |

The handler is `agentson-viewer.cmd`, which runs
`agentson render --format html` into a temp file and opens it in the default
browser.

## Design notes

**The GUI is a front end, not a second implementation.** Every registry
decision stays in `register_agentson_assoc.ps1`; `agentson_installer_gui.py`
runs it as a subprocess and shows its output. Copying the registry logic into
Python would create two implementations that drift the first time either
changes.

**The GUI imports the wordmark instead of copying it.** The art comes from
`cli.help_system.WORDMARK`, so if the art is ever regenerated the window
follows it. `WORDMARK_SON_START` is the split column: everything from that
column right is tagged bold, which is where **SON** begins.

**Amber on a dark ground, never on white.** Measured WCAG contrast: amber
`#ffb000` on `#0d1117` is 10.33:1 (AAA); on white it is 1.83:1, which fails.
The GUI therefore uses a dark ground. Amber is never used as ink on a light
background — that rule holds on screen and in print.

**Per-user, not machine-wide.** Everything is written under `HKCU`, which
Windows merges into `HKEY_CLASSES_ROOT` at logon. No administrator rights are
needed, and nothing touches `HKEY_LOCAL_MACHINE` — which matters on a
locked-down machine where `HKLM` writes would fail.

**No admin rights, no reboot.** The script calls `SHChangeNotify` so Explorer
picks the change up immediately.

**The CLI path is recorded, not assumed.** `agentson-viewer.cmd` tries the
PATH first, then falls back to `agentson-viewer.path`. Explorer does not
always inherit the user PATH that a terminal has, so a handler that relies on
PATH alone silently fails to find the CLI.

**No icon.** The repository has no `.ico` asset, and this script will not
invent a binary one. Add a `DefaultIcon` value under the ProgId if an asset is
ever produced.

**Changing what double-click does.** Edit the `(default)` value of
`HKCU\Software\Classes\AgentSON.File\shell\open\command`. For example, to
validate instead of view:

```
"C:\Python312\python.exe" "C:\path\to\AgentSON\cli\main.py" validate "%1"
```

## Verifying it worked

```powershell
Get-ItemProperty 'HKCU:\Software\Classes\.agentson' -Name '(default)'
# AgentSON.File
```

Then double-click a `.agentson` file and confirm a rendered page opens.
