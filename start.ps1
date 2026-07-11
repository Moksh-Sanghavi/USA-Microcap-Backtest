<#
.SYNOPSIS
    Starts both the backend (FastAPI/uvicorn) and frontend (Vite/React) for
    the Micro-Cap Quant Engine, as detached background processes.

.DESCRIPTION
    - Backend:  uvicorn on http://127.0.0.1:8050
    - Frontend: Vite dev server on http://127.0.0.1:3050
    Both PIDs are written to .pids/ next to this script so stop.ps1 can find
    and cleanly terminate them (including any child processes they spawn).

.USAGE
    powershell -ExecutionPolicy Bypass -File start.ps1
#>

$ErrorActionPreference = "Stop"

$Root       = $PSScriptRoot
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$PidDir     = Join-Path $Root ".pids"
$LogDir     = Join-Path $Root ".logs"

New-Item -ItemType Directory -Force -Path $PidDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Test-PortInUse($Port) {
    return [bool](Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue)
}

if (Test-PortInUse 8050) {
    Write-Host "Port 8050 is already in use -- backend may already be running. Run stop.ps1 first if you want a clean restart." -ForegroundColor Yellow
}
if (Test-PortInUse 3050) {
    Write-Host "Port 3050 is already in use -- frontend may already be running. Run stop.ps1 first if you want a clean restart." -ForegroundColor Yellow
}

Write-Host "Starting backend (uvicorn) on http://127.0.0.1:8050 ..." -ForegroundColor Cyan
$backend = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8050" `
    -WorkingDirectory $BackendDir `
    -RedirectStandardOutput (Join-Path $LogDir "backend.out.log") `
    -RedirectStandardError  (Join-Path $LogDir "backend.err.log") `
    -WindowStyle Hidden -PassThru
$backend.Id | Out-File (Join-Path $PidDir "backend.pid") -Encoding ascii

Write-Host "Starting frontend (Vite) on http://127.0.0.1:3050 ..." -ForegroundColor Cyan
$frontend = Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run", "dev" `
    -WorkingDirectory $FrontendDir `
    -RedirectStandardOutput (Join-Path $LogDir "frontend.out.log") `
    -RedirectStandardError  (Join-Path $LogDir "frontend.err.log") `
    -WindowStyle Hidden -PassThru
$frontend.Id | Out-File (Join-Path $PidDir "frontend.pid") -Encoding ascii

Write-Host ""
Write-Host "Backend  (PID $($backend.Id)):  http://127.0.0.1:8050  (docs at /docs)" -ForegroundColor Green
Write-Host "Frontend (PID $($frontend.Id)): http://127.0.0.1:3050" -ForegroundColor Green
Write-Host ""
Write-Host "Logs: $LogDir"
Write-Host "Run stop.ps1 to shut both down."
