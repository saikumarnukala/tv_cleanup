@echo off
setlocal
cd /d "%~dp0"
title Clean Your TV - One-Click Cache Cleaner

if exist "tools\venv\Scripts\python.exe" (
    "tools\venv\Scripts\python.exe" tools\clean.py %*
) else (
    python tools\clean.py %*
)

echo.
echo ======================================================
pause
