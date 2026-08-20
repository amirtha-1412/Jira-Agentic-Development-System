@echo off
echo ========================================
echo  JIRA AGENTIC DEV SYSTEM - SETUP
echo ========================================
echo.

REM Navigate to project directory
cd /d D:\Jira-Agentic-Development-System

echo [1/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please create it first: python -m venv venv
    pause
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

echo [2/5] Installing pytest...
pip install pytest --quiet
if errorlevel 1 (
    echo ERROR: Failed to install pytest
    pause
    exit /b 1
)
echo ✅ Pytest installed
echo.

echo [3/5] Verifying pytest installation...
python -m pytest --version
if errorlevel 1 (
    echo ERROR: Pytest not working
    pause
    exit /b 1
)
echo ✅ Pytest verified
echo.

echo [4/5] Setting environment variables...
set PYTHONPATH=D:\Jira-Agentic-Development-System
echo ✅ PYTHONPATH set
echo.

echo [5/5] Starting backend server...
echo.
echo ========================================
echo  BACKEND STARTING...
echo ========================================
echo.
echo Backend will run on: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

python backend/main.py
