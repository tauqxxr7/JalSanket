$ErrorActionPreference = 'Stop'
$projectPath = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $projectPath
try {
    $env:SAM_CLI_TELEMETRY = '0'
    $env:AWS_EC2_METADATA_DISABLED = 'true'
    $samPath = Join-Path $projectPath '.sam-venv\Scripts\python.exe'
    if (-not (Test-Path $samPath)) { throw 'Install the pinned tools from requirements-sam.txt into .sam-venv first.' }
    & $samPath -m samcli --version
    & $samPath -m samcli validate --lint --template-file template.yaml --region ap-south-1
    if ($LASTEXITCODE -ne 0) { throw 'SAM validation failed' }
    $env:PATH = (Join-Path $projectPath '.venv\Scripts') + ';' + $env:PATH
    & $samPath -m samcli build --template-file template.yaml
    if ($LASTEXITCODE -ne 0) { throw 'SAM build failed' }
    & .\.venv\Scripts\python.exe -m infrastructure.build
    if ($LASTEXITCODE -ne 0) { throw 'Evidence export failed' }
    & .\.venv\Scripts\python.exe scripts/check_sam_artifact.py
    if ($LASTEXITCODE -ne 0) { throw 'Built artifact check failed' }
} finally { Pop-Location }
