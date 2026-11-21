@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title Football in 30 Seconds - Studio Control Center
color 0B

cd /d "%~dp0"

:MENU
cls
echo ===============================================================================
echo            FOOTBALL IN 30 SECONDS (FS30) - STUDIO CONTROL CENTER
echo   1990s TV & Collage Aesthetic ^| MrBeast Kinetic Captions ^| Qwen3-TTS Engine
echo ===============================================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    color 0C
    echo [ERROR] Virtual environment not found at .venv\Scripts\python.exe!
    echo Please run install.bat first to set up all dependencies.
    echo.
    pause
    exit /b 1
)

echo [STATUS] Environment: OK | Python: .venv | GPU Acceleration: Enabled
echo.
echo Choose an action:
echo.
echo   [1] Launch Studio Daemon & Telegram Bot (@Football30secbot)
echo   [2] Produce Historical Documentary Video (Zidane, Cantona, Suarez)
echo   [3] View Final Masters Vault & Open Catalog CSV
echo   [4] Run Studio QA Diagnostic & Verify Dependencies
echo   [5] Exit
echo.
set /p CHOICE="Enter option [1-5]: "

if "%CHOICE%"=="1" goto DAEMON
if "%CHOICE%"=="2" goto HISTORICAL
if "%CHOICE%"=="3" goto VAULT
if "%CHOICE%"=="4" goto HEALTH
if "%CHOICE%"=="5" goto EXIT

echo Invalid option. Please try again.
timeout /t 2 >nul
goto MENU

:DAEMON
cls
echo ===============================================================================
echo             LAUNCHING STUDIO DAEMON & TELEGRAM REMOTE CONTROL
echo ===============================================================================
echo [*] Service running. Control via Telegram:
echo       /new    - Trigger breaking story research & assembly
echo       /status - Inspect job queue & render pipeline
echo.
echo Press Ctrl+C to stop.
echo.
".venv\Scripts\python.exe" -u run_pipeline_service.py
pause
goto MENU

:HISTORICAL
cls
echo ===============================================================================
echo                  PRODUCE HISTORICAL DOCUMENTARY STORY (FS30)
echo ===============================================================================
echo.
echo Select story to generate:
echo   [1] Zinedine Zidane - 2006 World Cup Final Headbutt (Autonomous Master)
echo   [2] Eric Cantona - 1995 Selhurst Park Kung-Fu Kick (Master)
echo   [3] Generate New Historical Documentary via Story Director
echo   [4] Back to main menu
echo.
set /p HIST_CHOICE="Enter choice [1-4]: "

if "%HIST_CHOICE%"=="1" (
    echo.
    echo [*] Launching Autonomous Zidane 2006 Documentary Pipeline...
    ".venv\Scripts\python.exe" -u runs\zidane_headbutt_story\run_zidane_pipeline.py
    pause
    goto MENU
)
if "%HIST_CHOICE%"=="2" (
    echo.
    echo [*] Rendering Eric Cantona 1995 Master...
    ".venv\Scripts\python.exe" -u runs\cantona_kungfu_kick_story\render_cantona_60s.py
    pause
    goto MENU
)
if "%HIST_CHOICE%"=="3" (
    echo.
    echo [*] Launching FS30 Story Director...
    ".venv\Scripts\python.exe" -u fs30\story_pipeline\runner.py
    pause
    goto MENU
)
goto MENU

:VAULT
cls
echo ===============================================================================
echo                       FINAL MASTERS VAULT & CATALOG
echo ===============================================================================
echo.
echo Directory: %CD%\final_masters_vault
echo.
if exist "final_masters_vault\masters_catalog.csv" (
    type "final_masters_vault\masters_catalog.csv"
    echo.
    echo Opening master vault folder in Windows Explorer...
    start "" "final_masters_vault"
) else (
    echo [NOTICE] No masters catalog found yet in final_masters_vault.
)
echo.
pause
goto MENU

:HEALTH
cls
echo ===============================================================================
echo                     STUDIO DIAGNOSTIC & DEPENDENCY CHECK
echo ===============================================================================
echo.
".venv\Scripts\python.exe" -c "import torch, PIL, transformers, soundfile, fs30; print('✓ PyTorch CUDA:', torch.cuda.is_available()); print('✓ Pillow Version:', PIL.__version__); print('✓ Transformers:', transformers.__version__); print('✓ SoundFile:', soundfile.__version__); print('✓ FS30 Story Pipeline: READY')"
echo.
ffmpeg -version | findstr /i "ffmpeg version"
echo.
pause
goto MENU

:EXIT
cls
echo Thank you for using Football in 30 Seconds Studio.
timeout /t 1 >nul
exit /b 0
