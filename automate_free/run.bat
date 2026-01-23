@echo off
REM Quick Run Script for AI Video Automation

echo ================================================
echo   Running AI Video Automation
echo ================================================
echo.

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo WARNING: Virtual environment not found!
    echo Run setup.bat first
    pause
    exit /b 1
)

REM Run the automation
echo.
echo Starting video generation...
echo This will take 30-45 minutes to complete
echo.
python main.py

echo.
echo ================================================
echo   Run Complete! Check logs/ folder for details
echo ================================================
echo.
pause
