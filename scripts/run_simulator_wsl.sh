#!/usr/bin/env bash
set -e

# WSLg / Display environment setup
export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}"
export PULSE_SERVER="${PULSE_SERVER:-unix:/mnt/wslg/PulseServer}"

cd /root/crosspoint-reader

# Ensure directories exist
mkdir -p sdcard/.fonts sdcard/books fs_/.fonts fs_/books fs_/.crosspoint

# Copy Vietnamese & Unicode fonts to simulated storage
if [ ! -f fs_/.fonts/Ubuntu-Vietnamese-Regular.ttf ]; then
    cp lib/EpdFont/builtinFonts/source/Ubuntu/Ubuntu-Vietnamese-*.ttf fs_/.fonts/ 2>/dev/null || true
    cp lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-*.ttf fs_/.fonts/ 2>/dev/null || true
fi

# Detect Host Gateway IP dynamically
HOST_IP=$(ip route show | grep default | awk '{print $3}' | head -n1)
if [ -z "$HOST_IP" ]; then
    HOST_IP="127.0.0.1"
fi

# Write OPDS servers config for CrossPoint (including Android Phone IPs & PC Localhost)
cat > fs_/.crosspoint/opds.json << EOF
{
  "servers": [
    {
      "name": "1. Android Wi-Fi (192.168.1.15)",
      "url": "http://192.168.1.15:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "2. Android Wi-Fi (192.168.1.16)",
      "url": "http://192.168.1.16:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "3. Android Hotspot (192.168.43.1)",
      "url": "http://192.168.43.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "4. mDNS Auto (ztruyen.local)",
      "url": "http://ztruyen.local:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "5. Android Wi-Fi (10.168.133.80)",
      "url": "http://10.168.133.80:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "6. PC Localhost (127.0.0.1)",
      "url": "http://127.0.0.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "7. PC WSL Gateway",
      "url": "http://${HOST_IP}:8080/opds",
      "username": "",
      "password_obf": ""
    }
  ]
}
EOF

# Pre-save Wi-Fi credentials so simulator is always auto-connected
cat > fs_/.crosspoint/wifi.json << EOF
{
  "lastConnectedSsid": "Simulator WiFi (fake)",
  "credentials": [
    {
      "ssid": "Simulator WiFi (fake)",
      "password_obf": "",
      "password_len": 0,
      "password_crc32": 0
    }
  ]
}
EOF

# Ensure download folder is set to books in settings.json
if [ -f fs_/.crosspoint/settings.json ]; then
    python3 -c "
import json
try:
    with open('fs_/.crosspoint/settings.json', 'r') as f:
        d = json.load(f)
    d['opdsDownloadFolder'] = 'books'
    with open('fs_/.crosspoint/settings.json', 'w') as f:
        json.dump(d, f)
except Exception:
    pass
" 2>/dev/null || true
else
    cat > fs_/.crosspoint/settings.json << EOF
{
  "opdsDownloadFolder": "books",
  "opdsFilenameFormat": 0,
  "fontSize": 14,
  "language": "EN"
}
EOF
fi

echo "======================================================"
echo "    CROSSPOINT READER - XTEINK X3 DESKTOP EMULATOR    "
echo "======================================================"
echo " [!] Device Profile: Xteink X3 (792x528 E-ink Framebuffer)"
echo " [!] Wi-Fi ảo: Tự động kết nối LAN (Auto-Connected)"
echo " [!] Phím điều khiển (Controls):"
echo "     - Phím Mũi tên: Điều hướng / Lật trang sách"
echo "     - Enter / Space: Chọn / Mở sách / Xác nhận (OK)"
echo "     - ESC / Backspace: Quay lại (Back)"
echo "     - Chuột trái: Cảm ứng màn hình (Touch/Click)"
echo "     - Phím P: Nút Nguồn / Khóa máy (Power / Sleep)"
echo " [!] Kết nối Termux Android:"
echo "     - http://192.168.1.15:8080/opds (Wi-Fi hiện tại)"
echo "     - http://192.168.1.16:8080/opds (Wi-Fi hiện tại)"
echo "     - http://192.168.43.1:8080/opds (Hotspot)"
echo "     - http://ztruyen.local:8080/opds (mDNS Zeroconf)"
echo "======================================================"
echo ""

if [ ! -f .pio/build/simulator_x3/program ]; then
    echo "[*] Dang bien dich firmware X3 Simulator..."
    pio run -e simulator_x3
fi

exec ./.pio/build/simulator_x3/program
