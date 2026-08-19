# start-ztruyen.ps1
# Z-Truyen X3 - One-Click Startup Script
# Run on Windows 11 with WSL2

param(
    [switch]$NoBrowser,
    [switch]$SkipBuild,
    [int]$Port = 8080
)

$ErrorActionPreference = "Continue"

function Get-WslIP {
    try {
        $ip = wsl -d Ubuntu-22.04 -e bash -c "hostname -I 2>/dev/null | awk '{print \$1}'" 2>$null
        return $ip.Trim()
    } catch {
        return "localhost"
    }
}

function Test-WslRunning {
    try {
        $result = wsl -d Ubuntu-22.04 -e true 2>&1
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    }
}

# Banner
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Z-Truyen X3 - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check WSL2
Write-Host "[1/5] Checking WSL2..." -ForegroundColor Yellow
if (-not (Test-WslRunning)) {
    Write-Host "  WSL2 Ubuntu not found!" -ForegroundColor Red
    Write-Host "  Run: wsl --install -d Ubuntu-22.04" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host "  WSL2 Ubuntu: OK" -ForegroundColor Green

# Check Backend Files
Write-Host "[2/5] Checking Z-Truyen Backend..." -ForegroundColor Yellow
$backendCheck = wsl -d Ubuntu-22.04 -e bash -c "test -d ~/workspace/ztruyen-backend && echo 'EXISTS'" 2>$null
if ($backendCheck -ne "EXISTS") {
    Write-Host "  Backend not found in ~/workspace/ztruyen-backend" -ForegroundColor Red
    Write-Host "  Please clone the backend first:" -ForegroundColor Yellow
    Write-Host "    cd ~/workspace" -ForegroundColor Gray
    Write-Host "    git clone <repo-url> ztruyen-backend" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Press any key to exit..." -ForegroundColor Gray
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}
Write-Host "  Backend directory: OK" -ForegroundColor Green

# Stop existing server on port
Write-Host "[3/5] Stopping existing servers..." -ForegroundColor Yellow
wsl -d Ubuntu-22.04 -e bash -c "pkill -f 'uvicorn.*8080' 2>/dev/null || true" 2>$null
Start-Sleep -Milliseconds 500

# Start Backend
Write-Host "[4/5] Starting Z-Truyen Backend on port $Port..." -ForegroundColor Yellow
$backendCmd = "cd ~/workspace/ztruyen-backend && source venv/bin/activate > /dev/null 2>&1 && uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port $Port"
$wslProcess = Start-Process -FilePath "wsl" -ArgumentList "-d", "Ubuntu-22.04", "-e", "bash", "-c", $backendCmd -PassThru -WindowStyle Hidden

# Wait for server to start
Start-Sleep -Seconds 3

# Check if server is running
$serverCheck = Invoke-WebRequest -Uri "http://localhost:$Port/healthz" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
if ($serverCheck.StatusCode -eq 200) {
    Write-Host "  Backend: OK" -ForegroundColor Green
} else {
    Write-Host "  Backend: Warning - Health check failed" -ForegroundColor Yellow
}

# Get WSL IP
Write-Host "[5/5] Getting network info..." -ForegroundColor Yellow
$wslIP = Get-WslIP
Write-Host ""

# Success Banner
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Server Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Backend:  http://localhost:$Port/opds" -ForegroundColor Cyan
Write-Host "  Health:   http://localhost:$Port/healthz" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Network:" -ForegroundColor Yellow
Write-Host "    WSL IP: http://$wslIP`:$Port/opds" -ForegroundColor White
Write-Host ""
Write-Host "  For CrossPoint/CrossVi Simulator:" -ForegroundColor Yellow
Write-Host "    Settings > OPDS > Add Server" -ForegroundColor White
Write-Host "    URL: http://$wslIP`:$Port/opds" -ForegroundColor White
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C in this window to stop server" -ForegroundColor Gray
Write-Host "Or close this window to keep running" -ForegroundColor Gray
Write-Host ""

# Keep script running and monitor
try {
    while ($true) {
        Start-Sleep -Seconds 10
        # Check if server is still running
        $check = Invoke-WebRequest -Uri "http://localhost:$Port/healthz" -UseBasicParsing -TimeoutSec 5 -ErrorAction SilentlyContinue
        if ($check.StatusCode -ne 200) {
            Write-Host "[!] Server stopped unexpectedly" -ForegroundColor Red
            break
        }
    }
} catch {
    Write-Host ""
    Write-Host "[*] Stopping server..." -ForegroundColor Yellow
}

# Cleanup
wsl -d Ubuntu-22.04 -e bash -c "pkill -f 'uvicorn.*$Port' 2>/dev/null || true" 2>$null
Write-Host "[*] Server stopped" -ForegroundColor Green
