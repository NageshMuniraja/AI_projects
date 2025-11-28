@echo off
REM Setup Script for AI Video Automation

echo ================================================
echo   AI Video Automation - Windows Setup
echo ================================================
echo.

REM Check Python
echo [1/5] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.9+ from https://www.python.org/
    pause
    exit /b 1
)
python --version
echo.

REM Create virtual environment
echo [2/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo Virtual environment created
) else (
    echo Virtual environment already exists
)
echo.

REM Activate and install dependencies
echo [3/5] Installing Python packages...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt
echo.

REM Copy .env template
echo [4/5] Setting up configuration...
if not exist ".env" (
    copy .env.example .env
    echo Created .env file - PLEASE EDIT IT WITH YOUR API KEYS!
) else (
    echo .env file already exists
)
echo.

REM Check FFmpeg
echo [5/5] Checking FFmpeg...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: FFmpeg not found!
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo Add it to your system PATH
) else (
    echo FFmpeg is installed
)
echo.

echo ================================================
echo   Setup Complete!
echo ================================================
echo.
echo NEXT STEPS:
echo 1. Edit .env file with your API keys
echo 2. Download YouTube credentials to youtube_credentials.json
echo 3. Run setup check: python setup_check.py
echo 4. Test system: python main.py
echo.
echo For detailed instructions, see README.md
echo.
pause
