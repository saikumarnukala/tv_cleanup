@echo off
setlocal
cd /d "%~dp0"
title Samsung Smart TV Wi-Fi Remote

if exist "tools\venv\Scripts\python.exe" (
    "tools\venv\Scripts\python.exe" tools\samsung_remote.py %*
) else (
    python tools\samsung_remote.py %*
)

echo.
pause
