# Khởi chạy Máy ảo Xteink X3 (CrossPoint Reader Virtual Machine)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "         KÍCH HOẠT MÁY ẢO XTEINK X3 (CROSSPOINT VIRTUAL MACHINE)      " -ForegroundColor Green
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

$RootPath = Split-Path -Parent $PSScriptRoot
$BackendPort = 8080

# 1. Tìm Python trên máy Windows
$PythonExe = $null
if (Test-Path "C:\miniconda3\python.exe") { $PythonExe = "C:\miniconda3\python.exe" }
if (-not $PythonExe -and (Test-Path (Join-Path $RootPath ".venv\Scripts\python.exe"))) { $PythonExe = Join-Path $RootPath ".venv\Scripts\python.exe" }
if (-not $PythonExe -and (Test-Path (Join-Path $RootPath "backend\.venv\Scripts\python.exe"))) { $PythonExe = Join-Path $RootPath "backend\.venv\Scripts\python.exe" }
if (-not $PythonExe) {
    $SysPython = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($SysPython) { $PythonExe = $SysPython }
}

# 2. Kiểm tra Backend Z-Truyen
Write-Host "[1/3] Kiểm tra Z-Truyen Backend Server (port $BackendPort)..." -ForegroundColor Yellow
$BackendRunning = Get-NetTCPConnection -LocalPort $BackendPort -State Listen -ErrorAction SilentlyContinue
if (-not $BackendRunning) {
    Write-Host "[*] Backend chưa chạy. Đang tự động khởi chạy Backend Z-Truyen..." -ForegroundColor Cyan
    $BackendDir = Join-Path $RootPath "backend"
    if ($PythonExe) {
        Start-Process -FilePath $PythonExe -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort" -WorkingDirectory $BackendDir -WindowStyle Minimized
    } else {
        Start-Process -FilePath "python" -ArgumentList "-m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort" -WorkingDirectory $BackendDir -WindowStyle Minimized
    }
    Start-Sleep -Seconds 2
    Write-Host "[OK] Backend Z-Truyen đã sẵn sàng tại http://localhost:8080/opds" -ForegroundColor Green
} else {
    Write-Host "[OK] Backend Z-Truyen đang hoạt động tại http://localhost:8080/opds" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/3] Kiểm tra Môi trường WSL Ubuntu & CrossPoint Firmware..." -ForegroundColor Yellow
wsl.exe -d Ubuntu -e bash -c "test -f /root/crosspoint-reader/.pio/build/simulator_x3/program"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Đang tiến hành biên dịch firmware..." -ForegroundColor Yellow
    wsl.exe -d Ubuntu -e bash -c "cd /root/crosspoint-reader && pio run -e simulator_x3"
}
Write-Host "[OK] Firmware X3 Simulator đã sẵn sàng!" -ForegroundColor Green

Write-Host ""
Write-Host "[3/3] Đang mở Cửa sổ Máy ảo Xteink X3..." -ForegroundColor Cyan
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host "  HƯỚNG DẪN ĐIỀU KHIỂN MÁY ẢO X3 (CROSSPOINT):" -ForegroundColor White
Write-Host "    - Các phím mũi tên: Di chuyển danh mục / Lật trang sách" -ForegroundColor Gray
Write-Host "    - Phím Enter / Space: Chọn / Mở mục (Select/OK)" -ForegroundColor Gray
Write-Host "    - Phím ESC / Backspace: Quay lại trang trước (Back)" -ForegroundColor Gray
Write-Host "    - Chuột trái: Chạm cảm ứng màn hình (Touch Screen)" -ForegroundColor Gray
Write-Host "    - Phím P: Tắt/mở nguồn ảo (Power / Sleep)" -ForegroundColor Gray
Write-Host "----------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""

wsl.exe -d Ubuntu -e /root/crosspoint-reader/run_simulator.sh
