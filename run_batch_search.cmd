@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "SCRIPT_PATH=%PROJECT_ROOT%src\google_xray_to_csv.py"
set "TITLES_FILE=%PROJECT_ROOT%examples\titles.txt"
set "SKILLS_FILE=%PROJECT_ROOT%examples\skills.txt"
set "LOCATIONS_FILE=%PROJECT_ROOT%examples\locations.txt"

if not exist "%PYTHON_EXE%" (
  echo Python venv not found. Create it first with: python -m venv .venv
  exit /b 1
)

"%PYTHON_EXE%" "%SCRIPT_PATH%" ^
  --titles-file "%TITLES_FILE%" ^
  --skills-file "%SKILLS_FILE%" ^
  --locations-file "%LOCATIONS_FILE%" ^
  --num 10 ^
  --output "%PROJECT_ROOT%output\batch_profiles.csv"

