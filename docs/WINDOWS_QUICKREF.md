# Z-Truyen X3 - Windows Quick Reference

## One-Click Startup

### 1. Setup (First Time Only)
```powershell
# Mở PowerShell as Administrator
# Cài WSL2
wsl --install -d Ubuntu-22.04

# Restart máy, sau đó:
wsl -d Ubuntu-22.04

# Trong Ubuntu, chạy:
bash < đường_dẫn/setup-wsl2.sh
```

### 2. Start (Every Time)
```powershell
# Double-click: start-ztruyen.ps1
# Hoặc:
.\start-ztruyen.ps1
```

---

## Commands

### Windows Side
```powershell
wsl --list                     # List WSL distros
wsl -d Ubuntu-22.04          # Start Ubuntu
wsl --shutdown                 # Stop all WSL
```

### WSL2 Side
```bash
~/start-backend.sh           # Start backend only
~/start-simulator.sh        # Start simulator only
~/start-ztruyen.sh          # Start both

# Manual commands:
cd ~/workspace/ztruyen-backend
source venv/bin/activate
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### Network
```bash
hostname -I                   # Get WSL IP
curl http://localhost:8080/healthz   # Test backend
```

---

## URLs

| Service | URL |
|---------|-----|
| Backend (local) | http://localhost:8080 |
| Backend (network) | http://172.x.x.x:8080 |
| OPDS Catalog | http://172.x.x.x:8080/opds |
| Health Check | http://172.x.x.x:8080/healthz |

---

## File Locations

| Purpose | Path |
|---------|------|
| Backend | ~/workspace/ztruyen-backend |
| Simulator | ~/workspace/crosspoint-simulator |
| Backend Start | ~/start-backend.sh |
| Simulator Start | ~/start-simulator.sh |
| Both Start | ~/start-ztruyen.sh |
| Windows Script | C:\...\start-ztruyen.ps1 |

---

## Test Checklist

- [ ] `start-ztruyen.ps1` chạy thành công
- [ ] Backend URL accessible
- [ ] CrossPoint Simulator khởi động được
- [ ] OPDS server configured
- [ ] Browse catalog → See books
- [ ] Download EPUB → Save to SD
- [ ] Open EPUB → Read content

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| WSL2 not found | `wsl --install -d Ubuntu-22.04` |
| Backend won't start | `cd ~/workspace/ztruyen-backend && source venv/bin/activate` |
| Port 8080 in use | `pkill -f uvicorn; ~/start-backend.sh` |
| Can't connect | Check firewall: `sudo ufw allow 8080` |
| Simulator won't build | `pio upgrade && pio run -e simulator_x3` |

---

## Android Alternative

```bash
# Trên Android (Termux):
pkg install python git avahi -y
pip install fastapi uvicorn httpx lxml ebooklib Pillow
cd ~/ztruyen-backend && pip install -e .
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080

# X3 kết nối:
# http://ztruyen.local:8080/opds
# hoặc
# http://<android-ip>:8080/opds
```

---

## Contact / Info

- Backend repo: (your repo URL)
- CrossPoint: https://github.com/crosspoint-reader/crosspoint-simulator
- CrossVi: https://github.com/tvhdc/crossvi
