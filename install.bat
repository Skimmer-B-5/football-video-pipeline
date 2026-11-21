@echo off
setlocal enabledelayedexpansion
title Football in 30 Seconds - 1-Click Studio Installer
color 0B

echo ===============================================================================
echo            FOOTBALL IN 30 SECONDS (FS30) - 1-CLICK STUDIO INSTALLER
echo     Historical Documentary Engine ^| MrBeast Kinetic Captions ^| Qwen3-TTS
echo ===============================================================================
echo.

:: 1. Verify Python
echo [*] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)
python --version

:: 2. Verify FFmpeg
echo [*] Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo [WARNING] FFmpeg is not found in system PATH.
    echo Attempting automatic installation via Windows Package Manager (winget)...
    winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [NOTICE] Please install FFmpeg manually from https://www.gyan.dev/ffmpeg/builds/
        echo and add the bin directory to your system PATH.
    )
) else (
    echo [OK] FFmpeg is installed and accessible.
)

:: 3. Setup Virtual Environment
echo.
echo [*] Initializing virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    python -m venv .venv
    if %errorlevel% neq 0 (
        color 0C
        echo [ERROR] Failed to create virtual environment (.venv).
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created.
) else (
    echo [OK] Existing virtual environment found.
)

:: 4. Upgrade pip
echo [*] Upgrading pip...
call .venv\Scripts\python.exe -m pip install --upgrade pip >nul 2>&1

:: 5. Install PyTorch with CUDA 12.1 detection
echo.
echo [*] Detecting GPU acceleration...
nvidia-smi >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] NVIDIA GPU detected! Ensuring PyTorch CUDA (cu121) is installed...
    call .venv\Scripts\python.exe -c "import torch; assert torch.cuda.is_available()" >nul 2>&1
    if %errorlevel% neq 0 (
        echo   -> Installing PyTorch with CUDA 12.1 acceleration...
        call .venv\Scripts\python.exe -m pip install torch torchaudio torchvision --index-url https://download.pytorch.org/whl/cu121
    ) else (
        echo [OK] PyTorch CUDA acceleration is active.
    )
) else (
    echo [NOTICE] No NVIDIA GPU detected. Installing standard CPU PyTorch...
    call .venv\Scripts\python.exe -m pip install torch torchaudio torchvision >nul 2>&1
)

:: 6. Install Core Requirements
echo.
echo [*] Installing studio dependencies...
call .venv\Scripts\python.exe -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install packages from requirements.txt.
    pause
    exit /b 1
)

:: 7. Ensure Vault & Cache Directories
echo.
echo [*] Creating directory structure...
if not exist "final_masters_vault" mkdir final_masters_vault
if not exist "runs" mkdir runs
if not exist "models" mkdir models

:: 8. Run Health Check
echo.
echo ===============================================================================
echo                             RUNNING HEALTH CHECK
echo ===============================================================================
call .venv\Scripts\python.exe -c "import torch, PIL, transformers, soundfile; print('  ✓ PyTorch CUDA:', torch.cuda.is_available(), '| GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'); print('  ✓ Pillow (PIL):', PIL.__version__); print('  ✓ Transformers:', transformers.__version__); print('  ✓ SoundFile:', soundfile.__version__)"

echo.
echo ===============================================================================
echo                INSTALLATION COMPLETE - STUDIO READY TO RUN!
echo                  Launch start.bat to open the Studio Menu.
echo ===============================================================================
echo.
pause
