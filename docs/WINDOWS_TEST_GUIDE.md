# Z-Truyen X3 - Windows Test Guide với Android

**Date:** 2026-08-18  
**Platform:** Windows + Android  
**Goal:** Test Z-Truyen backend trên Windows và kết nối với Android server

---

## Tổng Quan Kiến Trúc

```
┌─────────────────────────────────────────────────────────────────────┐
│                           WINDOWS PC                                │
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐ │
│  │   Python    │────►│   Android   │────►│   X3 Simulator      │ │
│  │  Backend    │     │  (WSL/Hot) │     │   (không có sẵn    │ │
│  │  localhost  │     │   hotspot   │     │   trên Windows)    │ │
│  └─────────────┘     └──────┬──────┘     └─────────────────────┘ │
│                              │                                     │
│                              │         ⚠️ Lưu ý quan trọng:        │
│                              │                                     │
│                              │         CrossVi/CrossPoint simulator │
│                              │         KHÔNG chạy được trên        │
│                              │         Windows trực tiếp.          │
│                              │         Cần macOS hoặc WSL + SDL2   │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                    Wi-Fi Hotspot
                               │
                               ▼
                    ┌─────────────────────┐
                    │   ANDROID PHONE      │
                    │                      │
                    │  Termux + Z-Truyen  │
                    │  Server running      │
                    │                      │
                    │  http://localhost   │
                    │       :8080          │
                    │                      │
                    └─────────────────────┘
                               │
                               │ http://ztruyen.local:8080/opds
                               │
                               ▼
                    ┌─────────────────────┐
                    │   X3 THỰC (CrossVi)  │
                    │                      │
                    │  OPDS Client        │
                    │  Browse + Download   │
                    │  EPUB Reader        │
                    └─────────────────────┘
```

---

## Phần 1: Test Backend Trên Windows (Không Cần X3)

### Bước 1.1: Cài Python

```powershell
# Kiểm tra Python đã cài chưa
python --version

# Nếu chưa, tải từ https://python.org
# Chọn "Add Python to PATH" khi cài đặt
```

### Bước 1.2: Clone/Copy Backend

```powershell
# Clone từ Git (nếu có repo)
git clone <repo-url>
cd ztruyen_backend

# Hoặc copy thư mục ztruyen_backend vào máy
```

### Bước 1.3: Tạo Virtual Environment

```powershell
# Tạo virtual environment
python -m venv venv

# Activate
.\venv\Scripts\activate

# Cài đặt dependencies
pip install fastapi uvicorn httpx lxml ebooklib Pillow pytest pytest-asyncio
```

### Bước 1.4: Chạy Backend

```powershell
# Di chuyển vào thư mục backend
cd ztruyen_backend

# Start server
uvicorn ztruyen_backend.main:app --host 127.0.0.1 --port 8080
```

### Bước 1.5: Test Endpoints

Mở PowerShell mới hoặc trình duyệt:

```powershell
# Test health
curl http://127.0.0.1:8080/healthz
# Expected: {"status":"ok","version":"1.0.0"}

# Test OPDS catalog
curl http://127.0.0.1:8080/opds
# Expected: OPDS XML

# Test search
curl "http://127.0.0.1:8080/opds/search?q=truyen"
# Expected: OPDS XML với search results
```

---

## Phần 2: Windows + Android Kết Nối (Thực Tế)

### Tình Huống Thực Tế

Vì X3 simulator không chạy trên Windows, bạn có 2 lựa chọn:

### Lựa Chọn A: Test Trực Tiếp Trên X3 Thật

Đây là cách test thực tế nhất:

```
┌─────────────────────────────────────┐
│         ANDROID PHONE               │
│                                     │
│  Termux + Z-Truyen Backend        │
│  http://ztruyen.local:8080/opds    │
│                                     │
└──────────────┬──────────────────────┘
               │
      Wi-Fi Hotspot
               │
               ▼
┌─────────────────────────────────────┐
│         X3 THỰC (CrossVi)          │
│                                     │
│  Settings > OPDS                    │
│  Server: http://ztruyen.local:8080 │
│                                     │
│  Browse > Search > Download > Read  │
└─────────────────────────────────────┘
```

### Lựa Chọn B: Dùng WSL2 (Nếu Muốn Simulator)

WSL2 có thể chạy CrossPoint simulator với Ubuntu:

```powershell
# Cài WSL2 (nếu chưa có)
wsl --install -d Ubuntu

# Trong Ubuntu (WSL):
sudo apt update
sudo apt install python3 python3-venv git libsdl2-dev

# Clone CrossPoint simulator
git clone https://github.com/crosspoint-reader/crosspoint-simulator.git
cd crosspoint-simulator

# Build và chạy
# (Tham khảo docs của crosspoint-simulator)
```

---

## Phần 3: Android + Termux Deployment Chi Tiết

### Bước 3.1: Cài Đặt Termux

```bash
# 1. Tải Termux từ F-Droid (KHÔNG phải Google Play)
# https://f-droid.org/packages/com.termux/

# 2. Cài đặt và mở Termux

# 3. Cấp quyền storage
termux-setup-storage
```

### Bước 3.2: Cài Đặt Packages

```bash
# Update
pkg update && pkg upgrade -y

# Cài Python và các tools cần thiết
pkg install python git avahi -y

# Kiểm tra
python --version
git --version
```

### Bước 3.3: Copy Backend Lên Điện Thoại

**Cách 1: Qua USB**
```powershell
# Kết nối điện thoại qua USB
# Bật USB debugging nếu cần
# Copy thư mục ztruyen_backend vào Internal Storage
```

**Cách 2: Qua Cloud (Google Drive, Dropbox)**
```bash
# Trên điện thoại, tải từ cloud
# Giải nén vào ~/storage/shared/
```

**Cách 3: Qua Termux**
```bash
# Clone từ Git
git clone https://github.com/your-repo/ztruyen_backend.git
cd ztruyen_backend
```

### Bước 3.4: Cài Đặt Backend

```bash
cd ztruyen_backend

# Tạo virtual environment (optional nhưng khuyến nghị)
python -m venv venv
source venv/bin/activate

# Cài dependencies
pip install fastapi uvicorn httpx lxml ebooklib Pillow

# Cài đặt package
pip install -e .
```

### Bước 3.5: Cấu Hình mDNS (Quan Trọng!)

```bash
# Cài avahi cho mDNS
pkg install avahi -y

# Kiểm tra avahi daemon
which avahi-daemon
avahi-daemon --version
```

### Bước 3.6: Start Server

```bash
cd ~/ztruyen_backend
source venv/bin/activate

# Start với thông báo IP
python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()
print('='*50)
print('Z-Truyen Server Starting...')
print(f'Local IP: {ip}')
print(f'OPDS URL: http://{ip}:8080/opds')
print(f'mDNS: http://ztruyen.local:8080/opds')
print('='*50)
"

# Start server
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### Bước 3.7: Verify Server

Mở terminal mới trong Termux:
```bash
curl http://localhost:8080/healthz
# Expected: {"status":"ok","version":"1.0.0"}

curl http://localhost:8080/opds | head -20
# Expected: OPDS XML
```

---

## Phần 4: Kết Nối X3

### Bước 4.1: Bật Hotspot Trên Android

```bash
# Trên Android:
# Settings > Mobile Hotspot > Bật
# Ghi nhớ tên network và password
```

### Bước 4.2: X3 Kết Nối Hotspot

```bash
# Trên X3:
# Settings > Wi-Fi > Chọn hotspot của Android > Nhập password
```

### Bước 4.3: Tìm IP Của Android

Trong Termux:
```bash
# Cách 1: Dùng hostname
# URL: http://ztruyen.local:8080/opds

# Cách 2: Dùng IP trực tiếp
# Trong Termux:
ip addr show wlan0 | grep inet
# Output: inet 192.168.43.1/24
# URL: http://192.168.43.1:8080/opds
```

### Bước 4.4: Cấu Hình OPDS Trên X3

1. **Trên X3:**
   - Settings → OPDS
   - Servers → Add Server

2. **Nhập thông tin:**
   - Name: `Z-Truyen`
   - URL: `http://ztruyen.local:8080/opds`
   - Hoặc: `http://192.168.43.1:8080/opds` (nếu hostname không hoạt động)

3. **Save**

### Bước 4.5: Browse Catalog

```bash
# Trên X3:
# Home > OPDS > Z-Truyen
# Should see:
# - Categories (Hot, Latest, Genres)
# - Book listings
# - Source indicators
```

---

## Phần 5: Troubleshooting

### Problem: X3 Không Tìm Thấy Server

**Nguyên nhân 1: Khác network**
```bash
# Kiểm tra cả hai cùng Wi-Fi/hotspot
# Thử ping từ X3 (nếu có ping command)
```

**Nguyên nhân 2: mDNS không hoạt động**
```bash
# Thử dùng IP trực tiếp thay vì hostname
# Trên X3, nhập: http://192.168.43.1:8080/opds
```

**Nguyên nhân 3: Firewall chặn**
```bash
# Trên Android, kiểm tra:
# Settings > Apps > Termux > Permissions > Network
```

### Problem: Server Không Start

```bash
# Kiểm tra port đã bị chiếm chưa
pkg install net-tools -y
netstat -tlnp | grep 8080

# Hoặc dùng port khác
uvicorn ... --port 8081
# Cập nhật X3 URL thành port 8081
```

### Problem: mDNS (ztruyen.local) Không Hoạt Động

```bash
# Kiểm tra avahi
pgrep avahi-daemon

# Restart avahi
avahi-daemon -k
avahi-daemon -D

# Hoặc dùng IP thay hostname
```

### Problem: Curl Command Không Hoạt Động

```bash
# Trong Termux, cài curl
pkg install curl -y

# Test lại
curl http://localhost:8080/healthz
```

---

## Phần 6: Script Tự Động

### Termux Quick Start Script

Lưu file này vào `~/ztruyen-start.sh` trên Android:

```bash
#!/bin/bash
echo "=========================================="
echo "  Z-Truyen X3 Server"
echo "=========================================="

cd ~/ztruyen_backend || {
    echo "Error: ztruyen_backend not found in ~/"
    exit 1
}

# Activate venv nếu có
[ -d venv ] && source venv/bin/activate

# Get IP
IP=$(ip addr show wlan0 2>/dev/null | grep inet | awk '{print $2}' | cut -d'/' -f1)

echo ""
echo "Server URL for X3:"
echo "  http://$IP:8080/opds"
echo ""
echo "Starting server..."
echo ""

# Start
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

Chạy script:
```bash
chmod +x ~/ztruyen-start.sh
bash ~/ztruyen-start.sh
```

---

## Phần 7: Test Checklist

### On Android (Termux)
- [ ] `curl http://localhost:8080/healthz` → OK
- [ ] `curl http://localhost:8080/opds` → OPDS XML
- [ ] `avahi-resolve -n ztruyen.local` → OK

### On X3
- [ ] Settings > Wi-Fi > Connected to hotspot
- [ ] Settings > OPDS > Server configured
- [ ] Browse catalog → See books
- [ ] Search → Works
- [ ] Select book → See chapters
- [ ] Download chapter → EPUB saved
- [ ] Open EPUB → Readable

### Full Flow Test
- [ ] Android: Open Termux → Run script → Server started
- [ ] X3: Connect to hotspot → Browse → Search "truyen"
- [ ] X3: Select book → View chapters
- [ ] X3: Download chapter 1 → EPUB to SD
- [ ] X3: Open EPUB → Read content

---

## Tóm Tắt Lệnh

```bash
# === TRÊN ANDROID (Termux) ===

# Cài đặt lần đầu
pkg update && pkg upgrade -y
pkg install python git avahi curl -y
python -m venv venv
source venv/bin/activate
pip install fastapi uvicorn httpx lxml ebooklib Pillow

# Copy và setup backend
cd ~/ztruyen_backend
pip install -e .

# Start server
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080

# Verify
curl http://localhost:8080/healthz

# === TRÊN X3 ===
# Settings > OPDS > Add Server
# URL: http://<android-ip>:8080/opds
```

---

## Tài Liệu Tham Khảo

- Termux Wiki: https://wiki.termux.com/wiki/Main_Page
- OPDS Spec: https://opds-spec.org/
- CrossVi: https://github.com/tvhdc/crossvi
