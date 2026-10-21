# Windows file association for `.agentson`

Makes Windows offer **AgentSON Session** when you right-click a `.agentson`
file, and opens it in the browser when you double-click one.

Before this, `.agentson` was registered nowhere — Explorer showed no
"Open with AgentSON" entry, because no ProgId existed.

## Use

```powershell
cd installers\windows
.\register_agentson_assoc.ps1
```

Then right-click any `.agentson` file → **Open with** → **AgentSON Session**.

Undo it:

```powershell
.\register_agentson_assoc.ps1 -Uninstall
```

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
