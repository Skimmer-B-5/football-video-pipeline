@echo off
chcp 65001 > nul
title 30 Football Plus - Autonomous Broadcast Engine Studio
color 0B

echo ===============================================================================
echo            30 FOOTBALL PLUS - AUTONOMOUS BROADCAST ENGINE STUDIO
echo      Late 90s TV Aesthetic ^| Groq Whisper Alignment ^| Expressive British VO
echo ===============================================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    color 0C
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe!
    echo Run setup_and_run.bat first to initialize dependencies.
    pause
    exit /b 1
)

if not exist ".env" (
    color 0E
    echo [WARNING] .env file not found. Ensure TELEGRAM_BOT_TOKEN and GROQ_API_KEY are configured.
)

echo [*] Workspace: %CD%
echo [*] Launching Primary V2 Broadcast Engine Daemon (@Football30secbot)...
echo [*] Features: 8-Scene Visual Director, Real Match Action Photos, Trinitron CRT, Multilang (EN/ES/PT)
echo [*] Use your phone in Telegram:
echo       /new    - Trigger news research and assemble a new 90s broadcast short
echo       /status - Inspect studio daemon status and active job queue
echo       /help   - Command reference
echo.
echo Press Ctrl+C in this terminal to stop the studio.
echo ===============================================================================
echo.

".venv\Scripts\python.exe" -u beta\run_telegram_broadcast_service.py

echo.
echo -------------------------------------------------------------------------------
echo [INFO] Studio service stopped.
pause
