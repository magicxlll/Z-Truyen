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
      "name": "Android Termux (192.168.1.22)",
      "url": "http://192.168.1.22:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Android Termux (192.168.1.32)",
      "url": "http://192.168.1.32:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Android Termux (10.176.38.219)",
      "url": "http://10.176.38.219:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Android Hotspot (192.168.43.1)",
      "url": "http://192.168.43.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "PC Localhost (127.0.0.1)",
      "url": "http://127.0.0.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "PC WSL Gateway",
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
echo " [!] Kết nối Termux Android: http://192.168.1.22:8080/opds"
echo "======================================================"
echo ""

if [ ! -f .pio/build/simulator_x3/program ]; then
    echo "[*] Dang bien dich firmware X3 Simulator..."
    pio run -e simulator_x3
fi

exec ./.pio/build/simulator_x3/program
