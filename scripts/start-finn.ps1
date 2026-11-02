$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDirectory = Join-Path $projectRoot 'backend'
$frontendDirectory = Join-Path $projectRoot 'frontend'
$pythonExecutable = Join-Path $projectRoot '.venv\Scripts\python.exe'
$logDirectory = Join-Path $projectRoot 'artifacts\runtime'

if (-not (Test-Path -LiteralPath $pythonExecutable)) {
    throw 'Run scripts/setup.ps1 first to install FINN dependencies.'
}

function Get-FinnResponse([string] $Address) {
    try { return Invoke-WebRequest -Uri $Address -UseBasicParsing -TimeoutSec 3 }
    catch { return $null }
}

function Wait-FinnService([string] $Address, [string] $Name) {
    # First startup indexes bundled primary reports; keep the wait bounded but
    # allow a slower disk to finish before reporting failure.
    $finnWaitTimer = [Diagnostics.Stopwatch]::StartNew()
    while ($finnWaitTimer.Elapsed.TotalSeconds -lt 180) {
        $response = Get-FinnResponse $Address
        if ($response -and $response.StatusCode -eq 200) { return $response }
        Start-Sleep -Milliseconds 750
    }
    throw "$Name did not become ready. Inspect the logs in $logDirectory."
}

New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$backendResponse = Get-FinnResponse 'http://127.0.0.1:8000/api/health'
if ($backendResponse) {
    $health = $backendResponse.Content | ConvertFrom-Json
    if ($health.status -ne 'ok' -or -not $health.version) {
        throw 'Port 8000 is occupied by another application. No process was stopped.'
    }
    Write-Host 'FINN backend is already running.'
} else {
    Start-Process -FilePath $pythonExecutable `
        -ArgumentList @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000') `
        -WorkingDirectory $backendDirectory -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDirectory 'backend.log') `
        -RedirectStandardError (Join-Path $logDirectory 'backend-error.log') | Out-Null
    Wait-FinnService 'http://127.0.0.1:8000/api/health' 'Backend' | Out-Null
    Write-Host 'FINN backend started.'
}

$frontendResponse = Get-FinnResponse 'http://127.0.0.1:3000/'
if ($frontendResponse) {
    if ($frontendResponse.Content -notmatch '<title>FINN') {
        throw 'Port 3000 is occupied by another application. No process was stopped.'
    }
    Write-Host 'FINN frontend is already running.'
} else {
    if (-not (Test-Path -LiteralPath (Join-Path $frontendDirectory '.next\BUILD_ID'))) {
        Push-Location -LiteralPath $frontendDirectory
        try {
            & npm.cmd run build
            if ($LASTEXITCODE -ne 0) { throw 'Frontend build failed.' }
        } finally { Pop-Location }
    }
    $nodeExecutable = (Get-Command node.exe -ErrorAction Stop).Source
    Start-Process -FilePath $nodeExecutable -ArgumentList @('scripts/start-production.mjs') `
        -WorkingDirectory $frontendDirectory -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logDirectory 'frontend.log') `
        -RedirectStandardError (Join-Path $logDirectory 'frontend-error.log') | Out-Null
    Wait-FinnService 'http://127.0.0.1:3000/' 'Frontend' | Out-Null
    Write-Host 'FINN frontend started.'
}

Write-Host ''
Write-Host 'FINN is ready: http://127.0.0.1:3000'
Write-Host "Logs: $logDirectory"
