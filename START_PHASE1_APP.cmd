@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "APP_PATH=%PROJECT_ROOT%app.py"

if not exist "%PYTHON_EXE%" (
  echo Python venv not found. Create it first with: python -m venv .venv
  exit /b 1
)

"%PYTHON_EXE%" "%APP_PATH%"

