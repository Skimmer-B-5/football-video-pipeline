@echo off
setlocal enabledelayedexpansion
title Football in 30 Seconds - Quick Setup & Studio Runner
color 0B

echo ===============================================================================
echo            FOOTBALL IN 30 SECONDS - 1-CLICK AUTONOMOUS STUDIO SETUP
echo        Cynical Tactician Narrative Engine ^| 90s TV Broadcast ^| Qwen3-TTS
echo ===============================================================================
echo.

:: 1. Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10 or 3.11 from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Check FFmpeg installation
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] FFmpeg was not found in your system PATH!
    echo Video assembly requires FFmpeg. You can install it via PowerShell:
    echo   winget install Gyan.FFmpeg
    echo or download it from https://www.gyan.dev/ffmpeg/builds/
    echo.
    set /p CONTINUE_NO_FFMPEG="Do you want to continue anyway? (y/n): "
    if /i "!CONTINUE_NO_FFMPEG!" neq "y" exit /b 1
)

:: 3. Setup Virtual Environment (.venv)
if not exist ".venv" (
    echo [1/4] Creating virtual environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [1/4] Virtual environment (.venv) found.
)

:: 4. Install / Verify Dependencies
echo [2/4] Checking and installing Python dependencies...
call .venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

:: Detect NVIDIA GPU for PyTorch CUDA
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo   -> NVIDIA GPU detected! Ensuring PyTorch CUDA (cu121) is installed...
    call .venv\Scripts\python.exe -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   -> Installing PyTorch with CUDA 12.1 acceleration...
        call .venv\Scripts\python.exe -m pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    )
) else (
    echo   -> No NVIDIA GPU detected. Installing standard CPU PyTorch...
    call .venv\Scripts\python.exe -m pip install torch torchaudio >nul 2>&1
)

echo   -> Installing pipeline packages from requirements.txt...
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

:: 5. Interactive Setup for Telegram & API Credentials (.env)
if not exist ".env" (
    echo.
    echo ===============================================================================
    echo                       TELEGRAM REMOTE CONTROL SETUP
    echo ===============================================================================
    echo To control your video studio from your phone, enter your credentials:
    echo.
    echo 1. Open Telegram and search for @BotFather
    echo    Type /newbot to create your bot and copy the API token.
    set /p TG_TOKEN="Enter your Telegram Bot Token: "
    echo.
    echo 2. Open Telegram and search for @userinfobot or @raw_data_bot
    echo    Start the bot and copy your numeric 'Id'.
    set /p TG_CHAT_ID="Enter your Telegram Chat ID: "
    echo.
    echo 3. Groq LPUs run the viral GPT-OSS 120B scriptwriter in under 2 seconds.
    echo    Get your free API key at: https://console.groq.com/keys
    set /p GROQ_KEY="Enter your Groq API Key: "
    echo.

    (
        echo # Football Video Pipeline - Local Secrets
        echo TELEGRAM_BOT_TOKEN="!TG_TOKEN!"
        echo TELEGRAM_CHAT_ID="!TG_CHAT_ID!"
        echo GROQ_API_KEY="!GROQ_KEY!"
        echo BING_API_KEY=""
    ) > .env
    echo [3/4] Successfully created .env configuration!
) else (
    echo [3/4] Existing .env configuration detected.
)

:: 6. Auto-download Qwen3-TTS weights if missing
if not exist "models\qwen3_tts_base\model.safetensors" (
    echo.
    echo [4/4] Local Qwen3-TTS Base model weights not found. Starting auto-download...
    call .venv\Scripts\python.exe -u stages\download_qwen3_base.py
    if %errorlevel% neq 0 (
        echo [WARNING] Qwen3-TTS download encountered an issue. Falling back to Edge-TTS / Kokoro.
    )
) else (
    echo [4/4] Local Qwen3-TTS Base neural weights ready (Martin Tyler cloned voice enabled).
)

:: 7. Launch Studio Daemon
echo.
echo ===============================================================================
echo                       LAUNCHING STUDIO SERVICE DAEMON
echo ===============================================================================
echo Your automated YouTube Shorts studio is now starting!
echo Open Telegram on your phone and message your bot:
echo    /new   - Scan live football news and generate a complete video
echo    /status - Check pipeline status and GPU health
echo    /help  - View command manual
echo.
echo Press Ctrl+C in this window to stop the service anytime.
echo ===============================================================================
echo.

call .venv\Scripts\python.exe -u run_pipeline_service.py
pause
