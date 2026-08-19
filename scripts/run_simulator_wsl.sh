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

# Write OPDS servers config for CrossPoint
cat > fs_/.crosspoint/opds.json << EOF
{
  "servers": [
    {
      "name": "Z-Truyen (Localhost)",
      "url": "http://127.0.0.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Z-Truyen (WSL Gateway)",
      "url": "http://${HOST_IP}:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Z-Truyen (Android Hotspot)",
      "url": "http://192.168.43.1:8080/opds",
      "username": "",
      "password_obf": ""
    }
  ]
}
EOF

echo "======================================================"
echo "    CROSSPOINT READER - XTEINK X3 DESKTOP EMULATOR    "
echo "======================================================"
echo " [!] Device Profile: Xteink X3 (792x528 E-ink Framebuffer)"
echo " [!] Phim dieu khien (Controls):"
echo "     - Phim Mui ten: Dieu huong / Lat trang sach"
echo "     - Enter / Space: Chon / Mo sach / Xac nhan (OK)"
echo "     - ESC / Backspace: Quay lai (Back)"
echo "     - Chuot trai: Cam ung man hinh (Touch/Click)"
echo "     - Phim P: Nut Nguon / Khoa may (Power / Sleep)"
echo " [!] OPDS Server: http://127.0.0.1:8080/opds (Z-Truyen)"
echo "======================================================"
echo ""

if [ ! -f .pio/build/simulator_x3/program ]; then
    echo "[*] Dang bien dich firmware X3 Simulator lan dau..."
    pio run -e simulator_x3
fi

exec ./.pio/build/simulator_x3/program
