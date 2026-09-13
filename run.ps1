param(
    [int]$Port = 8000,
    [switch]$Reload
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw "Python 3.9 or newer is required. Install Python and ensure it is on PATH."
}

if (-not (Test-Path ".venv\\Scripts\\python.exe")) {
    python -m venv .venv
}
$Python = Join-Path $Root ".venv\\Scripts\\python.exe"
& $Python -m pip install --upgrade pip
& $Python -m pip install -r requirements.txt

$modelFiles = @(
    "team3-ml-simulation\\models\\chute_random_forest.joblib",
    "team3-ml-simulation\\models\\chute_isolation_forest.joblib",
    "team3-ml-simulation\\models\\scaler.joblib"
)
if (@($modelFiles | Where-Object { -not (Test-Path (Join-Path $Root $_)) }).Count -gt 0) {
    $env:ML_N_JOBS = "1"
    & $Python "team3-ml-simulation\\train_models.py"
}

$env:PYTHONPATH = "$Root\\team2-backend;$Root\\team3-ml-simulation"
$args = @("-m", "uvicorn", "main:app", "--app-dir", "team2-backend", "--host", "0.0.0.0", "--port", "$Port")
if ($Reload) { $args += "--reload" }
& $Python @args
