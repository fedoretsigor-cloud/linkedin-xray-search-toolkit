param(
    [string]$Output = ".\output\batch_profiles.csv",
    [int]$Num = 10
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$scriptPath = Join-Path $projectRoot "src\google_xray_to_csv.py"
$titlesFile = Join-Path $projectRoot "examples\titles.txt"
$skillsFile = Join-Path $projectRoot "examples\skills.txt"
$locationsFile = Join-Path $projectRoot "examples\locations.txt"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python venv not found. Create it first with: python -m venv .venv"
}

& $pythonExe $scriptPath `
    --titles-file $titlesFile `
    --skills-file $skillsFile `
    --locations-file $locationsFile `
    --num $Num `
    --output $Output

