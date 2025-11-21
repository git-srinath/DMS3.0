@echo off
REM DWTOOL Scheduler Service Startup Script (Windows)
REM This script starts the scheduler service as a background process

echo Starting DWTOOL Scheduler Service...
echo.

REM Change to backend directory
REM cd backend

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if .env file exists (in backend folder or project root)
if not exist ".env" (
    if not exist "..\.env" (
        echo WARNING: .env file not found in backend folder or project root
        echo Please ensure database configuration is set up
        echo.
    )
)

REM Start the scheduler service
echo Starting scheduler service...
echo Press Ctrl+C to stop the service
echo.
python -m modules.jobs.scheduler_service

pause

