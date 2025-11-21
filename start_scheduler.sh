#!/bin/bash
# DWTOOL Scheduler Service Startup Script (Linux/macOS)
# This script starts the scheduler service

echo "Starting DWTOOL Scheduler Service..."
echo ""

# Change to backend directory
cd backend || exit 1

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ and add it to your PATH"
    exit 1
fi

# Check if .env file exists
if [ ! -f "../.env" ]; then
    echo "WARNING: .env file not found in project root"
    echo "Please ensure database configuration is set up"
    echo ""
fi

# Start the scheduler service
echo "Starting scheduler service..."
echo "Press Ctrl+C to stop the service"
echo ""
python3 -m modules.jobs.scheduler_service

