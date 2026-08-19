# Z-Truyen X3 - Windows WSL2 + CrossPoint Simulator Setup

**Date:** 2026-08-18  
**Platform:** Windows 11 + WSL2 Ubuntu  
**Goal:** Chạy CrossPoint/CrossVi Simulator trên Windows

---

## ⚠️ Quan Trọng: Native Windows KHÔNG Hỗ Trợ Simulator

Theo CrossPoint Simulator documentation:
> "Native Windows is not supported. Use WSL2."

**Chỉ có WSL2 Ubuntu mới chạy được.**

---

## Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│                         WINDOWS 11                                   │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │                   WSL2 UBUNTU                           │      │
│   │                                                          │      │
│   │   ┌─────────────────┐      ┌─────────────────────────┐  │      │
│   │   │  CrossPoint     │      │   Z-Truyen Backend      │  │      │
│   │   │  Simulator      │      │   (Python + FastAPI)    │  │      │
│   │   │                 │      │   http://localhost:8080  │  │      │
│   │   │  SDL2 Window    │      │                         │  │      │
│   │   │  (E-Ink UI)    │◄─────│   OPDS Catalog        │  │      │
│   │   └─────────────────┘      └───────────┬─────────────┘  │      │
│   │                                        │                 │      │
│   └────────────────────────────────────────┼─────────────────┘      │
│                                              │                       │
│                              localhost:8080 │                       │
└────────────────────────────────────────────┼───────────────────────┘
                                               │
                                               │ Wi-Fi (hoặc Hotspot)
                                               ▼
                                    ┌─────────────────────┐
                                    │   ANDROID PHONE     │
                                    │                    │
                                    │  Termux Backend    │
                                    │  (Alternative)    │
                                    │                    │
                                    └─────────────────────┘
```

---

## Phần 1: Cài Đặt WSL2 Ubuntu

### Bước 1.1: Kiểm Tra Yêu Cầu

```powershell
# Windows 11 đã hỗ trợ WSL2 mặc định
# Kiểm tra version Windows
winver
# Phải là Windows 11 21H2 trở lên
```

### Bước 1.2: Cài WSL2 (Nếu Chưa Có)

Mở **PowerShell as Administrator**:

```powershell
# Cài WSL2 + Ubuntu 22.04
wsl --install -d Ubuntu-22.04

# Restart máy khi được yêu cầu
```

### Bước 1.3: Khởi Động Ubuntu

```powershell
# Mở Ubuntu từ Start Menu
# Hoặc chạy:
wsl -d Ubuntu-22.04
```

### Bước 1.4: Setup Ubuntu Lần Đầu

```bash
# Tạo username và password khi được yêu cầu
# Cập nhật packages
sudo apt update && sudo apt upgrade -y
```

---

## Phần 2: Cài Đặt Dependencies

### Bước 2.1: Cài Python và Build Tools

```bash
# Cài các package cần thiết
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    pkg-config \
    libsdl2-dev \
    libssl-dev \
    ca-certificates \
    cmake \
    g++
```

### Bước 2.2: Cài PlatformIO

```bash
# Tạo virtual environment
python3 -m venv ~/.venvs/pio
source ~/.venvs/pio/bin/activate

# Cài PlatformIO
pip install platformio

# Verify
pio --version
```

### Bước 2.3: Cài SDL2

```bash
# SDL2 đã được cài ở bước 2.1
# Verify
sdl2-config --version
```

---

## Phần 3: Clone CrossPoint Simulator

### Bước 3.1: Clone Repository

```bash
# Tạo thư mục workspace
mkdir -p ~/workspace
cd ~/workspace

# Clone CrossPoint simulator
git clone https://github.com/crosspoint-reader/crosspoint-simulator.git
cd crosspoint-simulator

# Clone submodule (nếu có)
git submodule update --init --recursive
```

### Bước 3.2: Build Simulator

```bash
cd ~/workspace/crosspoint-simulator

# Build cho X3
pio run -e simulator_x3

# Hoặc build tất cả
pio run
```

### Bước 3.3: Run Simulator

```bash
# Sau khi build xong
pio run -e simulator_x3 -t upload

# Hoặc chạy trực tiếp (nếu có executable)
./.pio/build/simulator_x3/firmware.elf
```

---

## Phần 4: Clone CrossVi (Alternative)

CrossVi có X3-specific launcher:

```bash
cd ~/workspace

# Clone CrossVi
git clone --recursive https://github.com/tvhdc/crossvi.git
cd crossvi

# Build X3 simulator
python3 scripts/run_simulator.py x3
```

---

## Phần 5: Setup Z-Truyen Backend Trên WSL2

### Bước 5.1: Clone Backend

```bash
cd ~/workspace

# Clone backend (hoặc copy từ Windows)
git clone <ztruyen-backend-repo> ztruyen-backend
cd ztruyen-backend
```

### Bước 5.2: Cài Python Dependencies

```bash
# Tạo venv
python3 -m venv venv
source venv/bin/activate

# Cài dependencies
pip install fastapi uvicorn httpx lxml ebooklib Pillow

# Cài package
pip install -e .
```

### Bước 5.3: Start Backend

```bash
# Start server
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### Bước 5.4: Verify

```bash
# Test từ WSL2
curl http://localhost:8080/healthz
```

---

## Phần 6: Kết Nối Simulator Với Backend

### Bước 6.1: Tìm IP Của WSL2

```bash
# Trong WSL2 terminal
hostname -I
# Output: 172.x.x.x

# Hoặc dùng:
ip addr show eth0 | grep inet
```

### Bước 6.2: Configure OPDS Trong Simulator

Trong CrossPoint/CrossVi Simulator:
1. Settings → OPDS
2. Add Server:
   - URL: `http://172.x.x.x:8080/opds`
   - (Thay 172.x.x.x bằng IP thực tế)

### Bước 6.3: Test Connection

1. Browse → OPDS
2. Should see Z-Truyen catalog
3. Test download flow

---

## Phần 7: One-Click Startup Script

### Tạo Script Trên Windows

Tạo file `start-ztruyen.ps1` trên Desktop:

```powershell
# start-ztruyen.ps1
# Run as Administrator hoặc user thường

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Z-Truyen X3 - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Start WSL2 Ubuntu
Write-Host "[1/4] Starting WSL2 Ubuntu..." -ForegroundColor Yellow

# Check if WSL is running
$wslStatus = wsl -d Ubuntu-22.04 -e true 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "WSL2 not found. Please install WSL2 first." -ForegroundColor Red
    Write-Host "Run: wsl --install -d Ubuntu-22.04" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

# Start backend in WSL
Write-Host "[2/4] Starting Z-Truyen Backend..." -ForegroundColor Yellow
Start-Process -FilePath "wsl" -ArgumentList "-d", "Ubuntu-22.04", "-e", "bash", "-c", "cd ~/workspace/ztruyen-backend && source venv/bin/activate && uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080" -NoNewWindow -PassThru

# Get WSL IP
Write-Host "[3/4] Getting WSL IP..." -ForegroundColor Yellow
$wslIP = wsl -d Ubuntu-22.04 -e bash -c "hostname -I | awk '{print $1}'" 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Server Running!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend URL: http://localhost:8080/opds" -ForegroundColor Cyan
Write-Host "WSL IP:      http://$wslIP`:8080/opds" -ForegroundColor Cyan
Write-Host ""
Write-Host "For CrossPoint/CrossVi Simulator:" -ForegroundColor Yellow
Write-Host "  Settings > OPDS > Add: http://$wslIP`:8080/opds" -ForegroundColor White
Write-Host ""
Write-Host "Press Ctrl+C in WSL window to stop server" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan

# Keep script running
Write-Host ""
Read-Host "Press Enter to exit"
```

### Cách Sử Dụng

1. Double-click `start-ztruyen.ps1`
2. Hoặc click chuột phải → "Run with PowerShell"

---

## Phần 8: Hướng Dẫn Chi Tiết Từng Bước

### Ngày 1: Setup Môi Trường (30-60 phút)

#### Step 1: Cài WSL2
```powershell
# Mở PowerShell as Admin
wsl --install -d Ubuntu-22.04
# Restart máy
```

#### Step 2: Setup Ubuntu
```bash
# Username: ztruyen
# Password: (tùy chọn)
sudo apt update && sudo apt upgrade -y
```

#### Step 3: Cài Dependencies
```bash
sudo apt install -y python3 python3-pip python3-venv git libsdl2-dev libssl-dev cmake g++
pip install platformio
```

#### Step 4: Clone Repos
```bash
mkdir -p ~/workspace
cd ~/workspace

# Clone backend
git clone <backend-repo> ztruyen-backend

# Clone simulator
git clone https://github.com/crosspoint-reader/crosspoint-simulator.git
```

#### Step 5: Setup Backend
```bash
cd ~/workspace/ztruyen-backend
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx lxml ebooklib Pillow
pip install -e .
```

#### Step 6: Build Simulator
```bash
cd ~/workspace/crosspoint-simulator
pio run -e simulator_x3
```

### Ngày 2: Test End-to-End (15-30 phút)

#### Step 1: Start Backend
```bash
cd ~/workspace/ztruyen-backend
source venv/bin/activate
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

#### Step 2: Start Simulator
```bash
cd ~/workspace/crosspoint-simulator
pio run -e simulator_x3 -t upload
```

#### Step 3: Configure OPDS
1. Trong simulator: Settings → OPDS
2. Add: `http://172.x.x.x:8080/opds`
3. Save

#### Step 4: Test Flow
1. Browse catalog
2. Search
3. Download EPUB
4. Read

---

## Phần 9: Troubleshooting

### Problem: WSL2 Không Cài Được

```powershell
# Enable WSL feature
dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart

# Enable Virtual Machine Platform
dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart

# Restart và thử lại
wsl --install -d Ubuntu-22.04
```

### Problem: SDL2 Not Found

```bash
# Cài lại SDL2
sudo apt install libsdl2-dev libsdl2-image-dev libsdl2-ttf-dev libsdl2-mixer-dev
```

### Problem: PlatformIO Build Failed

```bash
# Update PlatformIO
pip install --upgrade platformio

# Clear cache
pio run --target clean
pio run
```

### Problem: Simulator Không Hiển Thị

```bash
# Kiểm tra SDL2
sdl2-config --version

# Verify display
echo $DISPLAY
# Phải có giá trị (vd: :0)
```

### Problem: Backend Không Kết Nối Được

```bash
# Check port
netstat -tlnp | grep 8080

# Check firewall
sudo ufw allow 8080
```

---

## Phần 10: Windows + Android Dual Setup

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         WINDOWS 11                               │
│                                                                      │
│   ┌────────────────────────────────────────────────────────┐       │
│   │               WSL2 UBUNTU                               │       │
│   │   ┌──────────────────────────────────────────────┐  │       │
│   │   │         CrossPoint/CrossVi Simulator          │  │       │
│   │   │                                              │  │       │
│   │   │         SDL2 E-Ink Display                   │  │       │
│   │   └──────────────────────────────────────────────┘  │       │
│   │                                                      │       │
│   │   ┌──────────────────────────────────────────────┐  │       │
│   │   │         Z-Truyen Backend                      │  │       │
│   │   │         http://localhost:8080                │  │       │
│   │   └──────────────────────────────────────────────┘  │       │
│   └────────────────────────────────────────────────────────┘       │
│                                                                      │
│   WSL IP: 172.x.x.x                                             │
└──────────────────────────────────────────────────────────────────────┘
                               │
                               │ OR
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       ANDROID PHONE                                   │
│                                                                      │
│   ┌──────────────────────────────────────────────────────────┐      │
│   │                    Termux                                  │      │
│   │                                                          │      │
│   │   ┌──────────────────────────────────────────────────┐  │      │
│   │   │         Z-Truyen Backend                          │  │      │
│   │   │         http://ztruyen.local:8080               │  │      │
│   │   └──────────────────────────────────────────────────┘  │      │
│   │                                                          │      │
│   └──────────────────────────────────────────────────────────┘      │
│                                                                      │
│   Wi-Fi Hotspot ←─────────── X3 connects here                     │
└──────────────────────────────────────────────────────────────────────┘
```

### Chọn Backend Nào?

| Backend | Location | Best For |
|---------|----------|----------|
| WSL2 | Windows PC | Development, Simulator testing |
| Android | Phone | Portable, Real device testing |

### Running Both

```bash
# WSL2 Backend
cd ~/workspace/ztruyen-backend
source venv/bin/activate
uvicorn ... --port 8080

# Android Backend
# Termux: uvicorn ... --port 8081  # Different port!
```

---

## Phần 11: Quick Reference

### Essential Commands

```bash
# === WSL2 ===
wsl --list                    # List distributions
wsl -d Ubuntu-22.04          # Start specific distro
wsl --shutdown                # Stop all WSL

# === Backend ===
cd ~/workspace/ztruyen-backend
source venv/bin/activate
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080

# === Simulator ===
cd ~/workspace/crosspoint-simulator
pio run -e simulator_x3

# === Network ===
hostname -I                    # Get WSL IP
netstat -tlnp | grep 8080     # Check port
```

### URLs

| Service | URL |
|---------|-----|
| Backend (WSL) | http://localhost:8080 |
| Backend (External) | http://172.x.x.x:8080 |
| OPDS Catalog | http://172.x.x.x:8080/opds |
| Android Backend | http://ztruyen.local:8080 |

---

## Checklist Trước Khi Test

- [ ] WSL2 Ubuntu installed
- [ ] Python + PlatformIO + SDL2 installed
- [ ] CrossPoint Simulator cloned và built
- [ ] Z-Truyen Backend cloned và installed
- [ ] Backend running on port 8080
- [ ] `curl http://localhost:8080/healthz` returns OK
- [ ] CrossPoint Simulator running
- [ ] OPDS server configured in simulator
- [ ] Can browse catalog in simulator
