# Automated Environment Setup and Virtual Testing for Windows (PowerShell)
# Z-Truyen X3 Backend

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = "$ScriptDir\.."
$BackendDir = "$ProjectRoot\backend"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Z-Truyen X3 — Thiết Lập Môi Trường Ảo / Test trên Windows" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Kiểm tra Python
Write-Host "`n[1/4] Kiểm tra phiên bản Python..." -ForegroundColor Yellow
try {
    $pyVer = python --version 2>&1
    Write-Host "    Đã tìm thấy: $pyVer" -ForegroundColor Green
} catch {
    Write-Host "    ❌ Chưa cài đặt Python! Vui lòng cài đặt Python 3.12+ từ python.org." -ForegroundColor Red
    exit 1
}

# 2. Tạo Môi Trường Ảo (Virtualenv)
Set-Location $BackendDir
Write-Host "`n[2/4] Khởi tạo môi trường ảo Python (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "    Đã tạo thư mục .venv thành công." -ForegroundColor Green
} else {
    Write-Host "    Môi trường .venv đã tồn tại." -ForegroundColor Green
}

# 3. Kích hoạt và cài đặt gói
Write-Host "`n[3/4] Cài đặt dependencies và Playwright..." -ForegroundColor Yellow
& .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
python -m playwright install chromium

# 4. Kiểm tra Docker (Tùy chọn)
Write-Host "`n[4/4] Kiểm tra Docker Desktop / WSL2..." -ForegroundColor Yellow
try {
    $dockerVer = docker --version 2>&1
    Write-Host "    Docker khả dụng: $dockerVer" -ForegroundColor Green
    Write-Host "    (Bạn có thể chạy `docker compose up -d` trong thư mục backend/)" -ForegroundColor Gray
} catch {
    Write-Host "    (Docker không bắt buộc, bạn có thể chạy trực tiếp bằng Python .venv)" -ForegroundColor Gray
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "  MÔI TRƯỜNG ĐÃ SẴN SÀNG! CÁC CÁCH KIỂM THỬ TRÊN WINDOWS:" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "1. Chạy Backend trực tiếp:"
Write-Host "   Set-Location backend; uvicorn app.main:app --reload --port 8080`n"
Write-Host "2. Chạy Trình Giả Lập E-Reader X3 qua Terminal:"
Write-Host "   python scripts/opds_simulator.py`n"
Write-Host "3. Mở Web UI trên Trình duyệt:"
Write-Host "   http://localhost:8080/`n"
Write-Host "4. Giả lập máy X3 trên KOReader Desktop Windows:"
Write-Host "   Tải KOReader Windows tại: https://github.com/koreader/koreader/releases"
Write-Host "   Thêm OPDS URL: http://localhost:8080/opds"
Write-Host "==========================================================" -ForegroundColor Green
