<#
.SYNOPSIS
    Stops the backend and frontend processes started by start.ps1.

.DESCRIPTION
    Reads PIDs from .pids/backend.pid and .pids/frontend.pid and terminates
    each process TREE (taskkill /T), since npm/vite spawn child node
    processes that a plain Stop-Process would leave orphaned. Falls back to
    killing whatever is listening on ports 8050/3050 if the PID files are
    missing or stale, so a crashed/manually-started server can still be
    cleaned up.

.USAGE
    powershell -ExecutionPolicy Bypass -File stop.ps1
#>

$Root   = $PSScriptRoot
$PidDir = Join-Path $Root ".pids"

function Stop-ProcessTree($ProcId) {
    if ($ProcId -and (Get-Process -Id $ProcId -ErrorAction SilentlyContinue)) {
        taskkill /PID $ProcId /T /F *> $null
        return $true
    }
    return $false
}

function Stop-ByPidFile($Name) {
    $file = Join-Path $PidDir "$Name.pid"
    if (Test-Path $file) {
        $procId = (Get-Content $file | Select-Object -First 1) -as [int]
        if (Stop-ProcessTree $procId) {
            Write-Host "Stopped $Name (PID $procId)." -ForegroundColor Green
        } else {
            Write-Host "$Name PID file present but process wasn't running (stale)." -ForegroundColor Yellow
        }
        Remove-Item $file -Force -ErrorAction SilentlyContinue
    } else {
        Write-Host "No PID file for $Name." -ForegroundColor Yellow
    }
}

function Stop-ByPort($Port, $Label) {
    $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    foreach ($conn in $conns) {
        Write-Host "Killing leftover $Label process on port $Port (PID $($conn.OwningProcess))." -ForegroundColor Yellow
        taskkill /PID $conn.OwningProcess /T /F *> $null
    }
}

Stop-ByPidFile "backend"
Stop-ByPidFile "frontend"

# Safety net: catch anything still bound to the app's ports even if the
# PID files were missing/stale (e.g. a server started outside start.ps1).
Stop-ByPort 8050 "backend"
Stop-ByPort 3050 "frontend"

Write-Host "Done."
