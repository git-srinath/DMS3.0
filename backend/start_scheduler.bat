@echo off
REM DWTOOL Scheduler Service Startup Script (Windows)
REM This script starts the scheduler service which handles:
REM   - Scheduled job execution
REM   - Report generation (Email/File destinations)
REM   - Queue processing from DMS_PRCREQ

echo ============================================
echo   DWTOOL Scheduler Service
echo ============================================
echo.

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0

REM Change to backend directory
cd /d "%SCRIPT_DIR%"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and add it to your PATH
    pause
    exit /b 1
)

REM Check if .env file exists (in backend folder or project root)
if exist ".env" (
    echo Using .env from backend folder
) else if exist "..\.env" (
    echo Using .env from project root
) else (
    echo WARNING: .env file not found in backend folder or project root
    echo Please ensure database configuration is set up
    echo.
    echo Required environment variables:
    echo   - DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME
    echo   - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (for email reports)
    echo   - REPORT_OUTPUT_DIR (for file reports, default: ./report_output)
    echo.
)

REM Create report output directory if it doesn't exist
if not exist "report_output" (
    mkdir report_output
    echo Created report_output directory
)

REM Start the scheduler service
echo.
echo Starting scheduler service...
echo   - Job scheduling and execution
echo   - Report queue processing (Email/File delivery)
echo.
echo Press Ctrl+C to stop the service
echo ============================================
echo.

python -m modules.jobs.scheduler_service

if errorlevel 1 (
    echo.
    echo ERROR: Scheduler service exited with an error
    pause
)

