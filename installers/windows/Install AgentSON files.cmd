@echo off
rem ===========================================================================
rem AgentSON file-association installer -- double-click launcher
rem
rem This is a .cmd rather than a .ps1 on purpose. On a default Windows
rem install, PowerShell's execution policy refuses to run unsigned .ps1
rem files, so a double-clicked .ps1 silently does nothing and the user is
rem given no explanation. A .cmd is not subject to that policy.
rem
rem Preference order:
rem   1. the GUI  -- pythonw.exe + agentson_installer_gui.py, no console
rem   2. the console installer -- register_agentson_assoc.ps1
rem
rem Every registry decision lives in register_agentson_assoc.ps1. Nothing
rem here duplicates it; this file only chooses how to start it.
rem ===========================================================================
setlocal

set "HERE=%~dp0"
set "GUI=%HERE%agentson_installer_gui.py"
set "SCRIPT=%HERE%register_agentson_assoc.ps1"

if not exist "%SCRIPT%" (
    echo.
    echo   Installer not found:
    echo     %SCRIPT%
    echo.
    echo   Keep this .cmd in the same folder as the other installer files.
    echo.
    pause
    exit /b 1
)

rem ---- 1. try the GUI ------------------------------------------------------
set "PYW="
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python313\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\pythonw.exe"
) do if not defined PYW if exist "%%~P" set "PYW=%%~P"

if not defined PYW for /f "delims=" %%I in ('where pythonw.exe 2^>nul') do if not defined PYW set "PYW=%%~I"

if defined PYW (
    echo Starting the AgentSON installer...
    start "" "%PYW%" "%GUI%"
    exit /b 0
)

rem ---- 2. fall back to the console installer --------------------------------
echo Python was not found, so the graphical installer cannot start.
echo Falling back to the console installer.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT%" %*

rem Ensure the agentson command is available in future PowerShell sessions
rem by adding .local\bin to the user's PowerShell profile (uses current username).
set "U=%USERNAME%"
powershell -NoProfile -Command "Add-Content $PROFILE '$env:PATH += \";C:\Users\%U%\.local\bin\"' " >nul 2>&1

set "RC=%ERRORLEVEL%"

echo.
if "%RC%"=="0" (echo Finished.) else (echo Finished with exit code %RC%.
echo.
pause
endlocal