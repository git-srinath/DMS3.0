@echo off
setlocal enabledelayedexpansion

REM Start scheduler using project-local virtual environment.
set "VENV_DIR=%~dp0.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
	echo [start_scheduler] Creating virtual environment at "%VENV_DIR%"...
	python -m venv "%VENV_DIR%"
	if errorlevel 1 (
		echo [start_scheduler] Failed to create venv. Ensure Python is installed and on PATH.
		exit /b 1
	)
)

echo [start_scheduler] Starting scheduler service...
"%PYTHON_EXE%" -m backend.modules.jobs.scheduler_service