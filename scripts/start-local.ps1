param([ValidateRange(1024,65535)][int]$Port = 8766)
$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
$pythonPath = Join-Path $projectPath '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { throw 'Create the documented Python virtual environment first.' }
if (-not (Test-Path -LiteralPath (Join-Path $projectPath 'data\raw\official.csv'))) { throw 'Run scripts/acquire.py to retrieve the official snapshot first.' }
Push-Location -LiteralPath $projectPath
try {
    Write-Host "JalSanket frontend and API: http://127.0.0.1:$Port/ — keep this terminal open."
    & $pythonPath -u -m uvicorn backend.api:app --host 127.0.0.1 --port $Port
    if ($LASTEXITCODE -ne 0) { throw "Server exited with code $LASTEXITCODE" }
} finally { Pop-Location }
