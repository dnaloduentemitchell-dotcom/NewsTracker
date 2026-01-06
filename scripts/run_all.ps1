$ErrorActionPreference = "Stop"

$backendScript = Join-Path $PSScriptRoot "run_backend.ps1"
$frontendScript = Join-Path $PSScriptRoot "run_frontend.ps1"

Start-Process powershell -ArgumentList "-NoExit", "-File", $backendScript
Start-Process powershell -ArgumentList "-NoExit", "-File", $frontendScript
