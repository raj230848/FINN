$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed' }
}
& .\.venv\Scripts\python.exe -m pip install -r backend/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed' }
Push-Location -LiteralPath frontend
try {
    & npm.cmd ci --no-audit --no-fund
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed' }
} finally { Pop-Location }
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
if (-not (Test-Path -LiteralPath frontend/.env.local)) { Copy-Item -LiteralPath frontend/.env.example -Destination frontend/.env.local }
Write-Host 'Setup complete. Run scripts/start-backend.ps1 and scripts/start-frontend.ps1 in separate terminals.'
