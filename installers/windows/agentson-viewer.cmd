@echo off
rem ===========================================================================
rem AgentSON file handler
rem
rem Windows runs this from the ProgId's shell\open\command, passing the
rem clicked file as %1. It renders the session to HTML and opens it in the
rem default browser.
rem
rem This file lives in the AgentSON repository and is referenced by an
rem absolute path written into the registry by register_agentson_assoc.ps1.
rem It is deliberately ASCII-only: .cmd files are read under the OEM
rem codepage, and a UTF-8 BOM here would break the first line.
rem ===========================================================================
setlocal

set "IN=%~1"
if "%IN%"=="" (
    echo agentson-viewer: no file given 1>&2
    exit /b 1
)

rem Prefer the CLI on PATH. Fall back to the absolute path recorded at
rem install time, because Explorer does not always inherit the user PATH
rem that a terminal session has.
set "AGENTSON_CMD="
where agentson >nul 2>&1
if not errorlevel 1 (
    set "AGENTSON_CMD=agentson"
) else if exist "%~dp0agentson-viewer.path" (
    set /p AGENTSON_CMD=<"%~dp0agentson-viewer.path"
)

if not defined AGENTSON_CMD (
    echo agentson-viewer: the agentson CLI was not found. 1>&2
    echo   Install it with:  pipx install -e ^<repo^> 1>&2
    echo   Or re-run register_agentson_assoc.ps1 from the AgentSON repo. 1>&2
    exit /b 1
)

rem A unique temp file per open, so two sessions can be viewed at once and
rem neither clobbers the other.
set "TMP=%TEMP%\agentson-view-%RANDOM%%RANDOM%.html"

"%AGENTSON_CMD%" render --format html --output "%TMP%" "%IN%"
if errorlevel 1 (
    echo agentson-viewer: render failed for "%IN%" 1>&2
    exit /b 1
)

start "" "%TMP%"
endlocal
exit /b 0
