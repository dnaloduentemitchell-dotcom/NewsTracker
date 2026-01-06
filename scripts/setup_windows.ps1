$ErrorActionPreference = "Stop"

Write-Host "Checking Python..."
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "Python not found. Install Python 3.11+ from https://python.org" -ForegroundColor Red
  exit 1
}
Write-Host "Using $pythonVersion"

Write-Host "Setting up backend virtual environment..."
$backendVenv = Join-Path $PSScriptRoot "..\backend\.venv"
python -m venv $backendVenv

$activate = Join-Path $backendVenv "Scripts\Activate.ps1"
. $activate

pip install --upgrade pip
pip install -r (Join-Path $PSScriptRoot "..\backend\requirements.txt")

Write-Host "Installing frontend dependencies..."
Push-Location (Join-Path $PSScriptRoot "..\frontend")
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) {
  Write-Host "npm not found. Install Node.js LTS from https://nodejs.org" -ForegroundColor Red
  Pop-Location
  exit 1
}

npm install
Pop-Location

Write-Host "Optional: Install spaCy model (en_core_web_sm)" -ForegroundColor Yellow
Write-Host "Run: backend\.venv\Scripts\python -m spacy download en_core_web_sm"
