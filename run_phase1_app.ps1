$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$appPath = Join-Path $projectRoot "app.py"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found. Create it first with: python -m venv .venv"
}

& $pythonExe $appPath

