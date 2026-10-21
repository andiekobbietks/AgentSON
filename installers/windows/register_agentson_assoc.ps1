<#
.SYNOPSIS
    Registers the .agentson file type for the current Windows user.

.DESCRIPTION
    Creates a per-user ProgId (AgentSON.File) and associates it with the
    .agentson extension, so Explorer's "Open with" menu offers AgentSON and
    double-clicking a session opens it in the browser.

    The keys live under HKCU\Software\Classes, which Windows merges into
    HKEY_CLASSES_ROOT at logon. That means NO administrator rights are
    needed -- unlike writing to HKLM directly, which would. On a locked-down
    machine this is the only place a non-admin can register a file type.

    The handler is agentson-viewer.cmd beside this script. It renders the
    session to HTML with `agentson render` and opens it in the default
    browser. The absolute path to the CLI is recorded next to it so the
    handler still works when Explorer has not inherited the user PATH.

.PARAMETER Uninstall
    Remove the registration instead of creating it.

.PARAMETER Force
    Overwrite an existing registration that points at a different handler.

.EXAMPLE
    .\register_agentson_assoc.ps1
    Register the file type.

.EXAMPLE
    .\register_agentson_assoc.ps1 -Uninstall
    Remove it again.

.NOTES
    There is no icon. No .ico asset exists in the repository, and inventing
    a binary one here would be guessing. Add DefaultIcon under the ProgId
    if an asset is ever produced.
#>
[CmdletBinding()]
param(
    [switch]$Uninstall,
    [switch]$Force
)

$ErrorActionPreference = 'Stop'

$Extension = '.agentson'
$ProgId    = 'AgentSON.File'
$Description = 'AgentSON Session'

$ViewerPath = Join-Path $PSScriptRoot 'agentson-viewer.cmd'
$PathFile   = Join-Path $PSScriptRoot 'agentson-viewer.path'

# HKCU\Software\Classes is the per-user half of HKEY_CLASSES_ROOT.
$ExtKey    = "HKCU:\Software\Classes\$Extension"
$ProgIdKey = "HKCU:\Software\Classes\$ProgId"
$CommandKey = "$ProgIdKey\shell\open\command"


function Find-AgentsonExe {
    <# Prefer whatever PATH resolves to, then the known pipx location. #>
    $cmd = Get-Command agentson -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }

    $known = Join-Path $env:USERPROFILE '.local\bin\agentson.exe'
    if (Test-Path $known) { return $known }

    return $null
}


function Invoke-ShellNotify {
    <# Tell Explorer the file associations changed, so the menu updates
       without a logoff or a reboot. SHCNE_ASSOCCHANGED = 0x08000000. #>
    try {
        if (-not ('AgentSON.ShellNotify' -as [type])) {
            Add-Type -Namespace AgentSON -Name ShellNotify -MemberDefinition @'
[DllImport("shell32.dll", CharSet = CharSet.Auto, SetLastError = false)]
public static extern void SHChangeNotify(uint wEventId, uint uFlags, IntPtr dwItem1, IntPtr dwItem2);
'@
        }
        [AgentSON.ShellNotify]::SHChangeNotify(0x08000000, 0x0000, [IntPtr]::Zero, [IntPtr]::Zero)
    } catch {
        Write-Warning "Could not notify Explorer; the change will appear after a logoff or reboot."
    }
}


function Test-HandlerIsOurs {
    <# True when the ProgId already points at this repo's viewer. #>
    if (-not (Test-Path $CommandKey)) { return $false }
    $existing = (Get-ItemProperty -Path $CommandKey -Name '(default)' -ErrorAction SilentlyContinue).'(default)'
    return ($existing -and $existing -like "*$([System.IO.Path]::GetFileName($ViewerPath))*")
}


if ($Uninstall) {
    Write-Host "Removing the $Extension registration..."

    foreach ($key in @($CommandKey, "$ProgIdKey\shell\open", "$ProgIdKey\shell", $ProgIdKey, $ExtKey)) {
        if (Test-Path $key) {
            Remove-Item -Path $key -Recurse -Force
            Write-Host "  removed $key"
        }
    }

    if (Test-Path $PathFile) {
        Remove-Item -Path $PathFile -Force
        Write-Host "  removed $PathFile"
    }

    Invoke-ShellNotify
    Write-Host ""
    Write-Host "$Extension is no longer associated. Explorer may need a moment to catch up."
    exit 0
}


# ---- install ---------------------------------------------------------------

if (-not (Test-Path $ViewerPath)) {
    Write-Error "Expected the handler beside this script: $ViewerPath"
    exit 1
}

$agentsonExe = Find-AgentsonExe
if (-not $agentsonExe) {
    Write-Error @"
The agentson CLI was not found, so the handler could not be verified.
Install it first, then re-run this script:

    pipx install -e <path-to-AgentSON>

(Or run this script from a terminal where 'agentson' resolves.)
"@
    exit 1
}

if ((Test-HandlerIsOurs) -and -not $Force) {
    Write-Host "$Extension is already registered to this handler:"
    Write-Host "  $ViewerPath"
    Write-Host ""
    Write-Host "Nothing to do. Use -Force to rewrite it anyway."
    exit 0
}

Write-Host "Registering $Extension -> $ProgId"
Write-Host "  CLI     : $agentsonExe"
Write-Host "  handler : $ViewerPath"
Write-Host ""

New-Item -Path $ExtKey -Force | Out-Null
Set-ItemProperty -Path $ExtKey -Name '(default)' -Value $ProgId
Set-ItemProperty -Path $ExtKey -Name 'Content Type' -Value 'application/json'
Set-ItemProperty -Path $ExtKey -Name 'PerceivedType' -Value 'text'

New-Item -Path $ProgIdKey -Force | Out-Null
Set-ItemProperty -Path $ProgIdKey -Name '(default)' -Value $Description

# The command Windows runs. %1 is the clicked file, quoted because paths
# routinely contain spaces.
New-Item -Path $CommandKey -Force | Out-Null
Set-ItemProperty -Path $CommandKey -Name '(default)' -Value "`"$ViewerPath`" `"%1`""

# Recorded so the handler can find the CLI even when Explorer has not
# inherited the user PATH.
Set-Content -Path $PathFile -Value $agentsonExe -Encoding ascii -NoNewline

Invoke-ShellNotify

Write-Host "Done. Right-click any .agentson file -> Open with -> AgentSON Session."
Write-Host ""
Write-Host "To undo: .\register_agentson_assoc.ps1 -Uninstall"
Write-Host ""
Write-Host "Note: this is per-user only (HKCU). No administrator rights were needed"
Write-Host "and nothing was written to HKEY_LOCAL_MACHINE."
