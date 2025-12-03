#!/bin/bash
# DWTOOL Scheduler Service Startup Script (Linux/macOS)
# This script starts the scheduler service which handles:
#   - Scheduled job execution
#   - Report generation (Email/File destinations)
#   - Queue processing from DMS_PRCREQ

echo "============================================"
echo "  DWTOOL Scheduler Service"
echo "============================================"
echo ""

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to backend directory (script is already in backend)
cd "$SCRIPT_DIR" || {
    echo "ERROR: Could not change to script directory"
    exit 1
}

# Check if Python is available (try python3 first, then python)
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Check if .env file exists
if [ -f ".env" ]; then
    echo "Using .env from backend folder"
elif [ -f "../.env" ]; then
    echo "Using .env from project root"
else
    echo "WARNING: .env file not found in backend folder or project root"
    echo "Please ensure database configuration is set up"
    echo ""
    echo "Required environment variables:"
    echo "  - DB_TYPE, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME"
    echo "  - SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD (for email reports)"
    echo "  - REPORT_OUTPUT_DIR (for file reports, default: ./report_output)"
    echo ""
fi

# Create report output directory if it doesn't exist
if [ ! -d "report_output" ]; then
    mkdir -p report_output
    echo "Created report_output directory"
fi

# Start the scheduler service
echo ""
echo "Starting scheduler service..."
echo "  - Job scheduling and execution"
echo "  - Report queue processing (Email/File delivery)"
echo ""
echo "Press Ctrl+C to stop the service"
echo "============================================"
echo ""

$PYTHON_CMD -m modules.jobs.scheduler_service

EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo ""
    echo "ERROR: Scheduler service exited with code $EXIT_CODE"
    exit $EXIT_CODE
fi

