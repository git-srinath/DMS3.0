@echo off
setlocal enabledelayedexpansion

REM Start FastAPI using a project-local virtual environment.
REM This avoids "installed but not found" issues when PATH points to a different Python.

set "VENV_DIR=%~dp0.venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
  echo [start_fastapi] Creating virtual environment at "%VENV_DIR%"...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 (
    echo [start_fastapi] Failed to create venv. Ensure Python is installed and on PATH.
    exit /b 1
  )
)

REM echo [start_fastapi] Upgrading pip...
REM "%PYTHON_EXE%" -m pip install --upgrade pip
REM 
REM echo [start_fastapi] Installing backend requirements...
REM "%PYTHON_EXE%" -m pip install -r "%~dp0backend\requirements.txt"
REM if errorlevel 1 (
REM   echo [start_fastapi] Failed to install requirements.
REM   exit /b 1
REM )

echo [start_fastapi] Starting uvicorn...
"%PYTHON_EXE%" -m uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8000