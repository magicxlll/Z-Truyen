# Z-Truyen X3 — Smartphone Deployment Guide

**Version:** 1.0.0  
**Date:** 2026-08-13  
**Platform:** Android + Termux  
**Host:** X3 CrossVi OPDS Client  

---

## Overview

Deploy Z-Truyen backend on Android smartphone using Termux, enabling X3 to discover and connect via mDNS/Bonjour.

```
Android (Termux)                    X3 (CrossVi)
     │                                   │
     │──── mDNS (ztruyen.local) ─────────►│
     │                                   │
     │◄──── OPDS Catalog Request ─────────│
     │                                   │
     │──── OPDS XML ─────────────────────►│
     │                                   │
     │◄──── EPUB Download Request ────────│
     │                                   │
     │──── EPUB File ─────────────────────►│ (saved to SD)
     │                                   │
```

---

## Prerequisites

1. **Android Phone** with Termux installed
2. **Xteink X3** with CrossVi/CrossPoint firmware
3. **Both devices on same network** (Wi-Fi LAN or phone hotspot)

---

## Step 1: Install Termux on Android

### Install F-Droid (recommended)
```bash
# Download F-Droid from https://f-droid.org/
# Install Termux from F-Droid (not Google Play - outdated)
```

### Grant Storage Permission
```bash
# In Termux:
termux-setup-storage
```

---

## Step 2: Install Python và Dependencies

```bash
# Update packages
pkg update && pkg upgrade -y

# Install Python
pkg install python -y

# Install required packages
pip install fastapi uvicorn httpx lxml ebooklib Pillow

# Install OpenSSL for HTTPS (optional but recommended)
pkg install openssl -y
```

---

## Step 3: Setup mDNS (avahi)

```bash
# Install avahi
pkg install avahi -y

# The service should auto-start, but verify:
ls /data/data/com.termux/files/usr/var/run/avahi-daemon/
```

### Troubleshooting mDNS
```bash
# If avahi doesn't start:
export AVAHI_DAEMON_DETECT_LOCAL=0
avahi-daemon &
```

---

## Step 4: Deploy Z-Truyen Backend

### Option A: Copy from existing setup
```bash
# Copy ztruyen_backend/ folder to phone
# Via USB, cloud storage, or git clone

cd ztruyen_backend
pip install -e .
```

### Option B: Clone from Git
```bash
# If you have the code on Git
pkg install git -y
git clone <your-repo-url>
cd ztruyen_backend
pip install -e .
```

---

## Step 5: Configure mDNS Hostname

Edit `/data/data/com.termux/files/usr/etc/avahi/avahi-daemon.conf`:
```ini
[server]
host-name=ztruyen
domain-name=local

[publish]
publish-addresses=yes
publish-dns-addresses=yes
```

Restart avahi:
```bash
avahi-daemon -k && avahi-daemon &
```

Verify:
```bash
avahi-resolve -n ztruyen.local
```

---

## Step 6: Start Server

```bash
cd ztruyen_backend

# Start with auto-detected IP
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 &

# Or start and log IP
python -c "
import socket
import subprocess
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(('8.8.8.8', 80))
ip = s.getsockname()[0]
s.close()
print(f'Z-Truyen server starting...')
print(f'OPDS URL: http://{ip}:8080/opds')
print(f'mDNS: http://ztruyen.local:8080/opds')
"
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

---

## Step 7: Verify Server

From another terminal on the phone:
```bash
curl http://localhost:8080/healthz
# Expected: {"status":"ok","version":"1.0.0"}

curl http://localhost:8080/opds | head -20
# Expected: OPDS XML catalog
```

---

## Step 8: Configure X3

### On X3 with CrossVi:
1. Settings → OPDS
2. Add Server:
   - **URL:** `http://ztruyen.local:8080/opds`
   - Hoặc dùng IP: `http://<phone-ip>:8080/opds`
3. Save

### Verify Connection:
1. Browse → OPDS → Z-Truyen
2. Should see book catalog

---

## Network Scenarios

### Scenario 1: Phone Hotspot
```
Phone (Hotspot ON) ←──── Wi-Fi ────→ X3
     │
     └── Z-Truyen server running
```
- Phone creates Wi-Fi network
- X3 connects to phone's hotspot
- mDNS works within the hotspot LAN

### Scenario 2: Home Wi-Fi
```
Router ←──── Wi-Fi ────→ Phone
                        │
Router ←──── Wi-Fi ────→ X3
```
- Both on same router
- mDNS broadcast works across LAN
- No special router config needed

---

## Troubleshooting

### mDNS Not Working

1. **Check avahi is running:**
   ```bash
   ps aux | grep avahi
   ```

2. **Test from another device:**
   ```bash
   # On Linux/Mac:
   ping ztruyen.local
   
   # On Windows:
   # Install iTunes/Bonjour or Avahi for Windows
   ```

3. **Use IP fallback:**
   - Open Termux, run `ifconfig`
   - Note IP (e.g., 192.168.43.1)
   - Enter `http://192.168.43.1:8080/opds` manually on X3

### Port Already in Use

```bash
# Find and kill process using port 8080
fuser -k 8080/tcp

# Or use different port:
uvicorn ... --port 8081
```

### X3 Can't Connect

1. Check both devices on same network
2. Try IP instead of hostname
3. Check firewall on phone allows connections
4. Restart avahi: `avahi-daemon -k && avahi-daemon &`

---

## Power Optimization

### For On-Demand Usage:

1. **Close other apps** to reduce background drain
2. **Keep phone plugged in** when actively using
3. **Consider battery saver mode** - server still runs but throttles

### Estimated Battery Impact:
- Idle (screen off): ~2-5% per hour
- Active serving: ~10-15% per hour
- With screen on: ~20-30% per hour

---

## Security Notes

### For Personal Use (No Auth):
- No authentication - anyone on network can access
- Data stays local

### If Concerned:
- Use on-demand only (start server when reading)
- Turn off hotspot when not using
- No sensitive data stored

---

## Quick Start Checklist

- [ ] Install Termux from F-Droid
- [ ] `pkg update && pkg upgrade -y`
- [ ] `pkg install python git avahi -y`
- [ ] Copy/clone ztruyen_backend
- [ ] `pip install -e .`
- [ ] `avahi-daemon &`
- [ ] `uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 &`
- [ ] Verify: `curl http://localhost:8080/healthz`
- [ ] Configure X3 OPDS with `http://ztruyen.local:8080/opds`
- [ ] Browse and download EPUBs!

---

## Alternatives Considered

| Option | Rejected Because |
|--------|-----------------|
| Termux + Linux container | Overkill, more battery drain |
| Dedicated Android app | More work, Python in Termux sufficient |
| Cloud server | Costs money, defeats portability |
| Always-on server | Battery concerns (answered C to Q2) |

---

## Next Steps

After basic setup works:

1. Create Termux shortcut/script for one-click start
2. Consider battery optimization
3. Test all source adapters
4. Verify EPUB reading on X3
