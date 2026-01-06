$ErrorActionPreference = "Stop"
$backendVenv = Join-Path $PSScriptRoot "..\backend\.venv"
$activate = Join-Path $backendVenv "Scripts\Activate.ps1"
. $activate

$env:PYTHONPATH = Join-Path $PSScriptRoot "..\backend"
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
