@echo off
rem ===============================================================
rem  Vein Launcher - source build launcher (ASCII only on purpose:
rem  cmd.exe reads .cmd in the OEM code page, so keep it ASCII)
rem
rem  Dependencies already installed next to this file:
rem    .deps                                PySide6 6.12 + aiohttp + pydantic
rem    vein_launcher\presentation\webui\dist  built frontend (app.js, css, icons)
rem ===============================================================
setlocal
cd /d "%~dp0"

set "VPY=C:\Users\CMAI\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe"
if not exist "%VPY%" set "VPY=python"

set "PYTHONPATH=%~dp0.deps;%~dp0"
set "PYTHONUTF8=1"

rem QtWebEngine renderer aborts (exit_code=18) under restricted tokens or
rem stripped-down sessions; disabling Chromium's own sandbox fixes rendering.
rem The page is a local file:// UI, no remote web content is loaded.
set "QTWEBENGINE_DISABLE_SANDBOX=1"

rem Uncomment to keep the console and see logs:
rem set "VEIN_SHOW_CONSOLE=1"

"%VPY%" -m vein_launcher.presentation.main %*
endlocal
