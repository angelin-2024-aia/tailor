@echo off
REM TailorPro Startup Script for Windows

echo.
echo ========================================
echo   TailorPro - Tailor Shop Management
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Install requirements if needed
echo Checking dependencies...
pip install -r requirements.txt >nul 2>&1

REM Start the app
echo.
echo Starting TailorPro...
echo.
echo Open your browser and go to: http://127.0.0.1:5000
echo.
python app.py

pause
