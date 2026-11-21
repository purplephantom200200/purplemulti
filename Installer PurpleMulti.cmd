@echo off
rem Builds PurpleMulti.exe and installs it for this Windows user (Start Menu + Windows Search).
rem Run it again after an update. Options: --desktop, --no-build, --uninstall
cd /d "%~dp0"
uv sync --locked --quiet
if errorlevel 1 (
    echo Installation failed. Check that uv is installed: https://docs.astral.sh/uv/
    pause
    exit /b 1
)
".venv\Scripts\python.exe" scripts\install.py %*
pause
