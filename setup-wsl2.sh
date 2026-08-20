#!/bin/bash
# setup-wsl2.sh
# Automated setup script for CrossPoint Simulator & Z-Truyen on WSL2 Ubuntu

set -e

echo "======================================================"
echo "  Z-Truyen X3 - WSL2 CrossPoint Virtual Machine Setup "
echo "======================================================"
echo ""

# 1. Check if running in WSL
if ! grep -qEi "(microsoft|wsl)" /proc/version 2>/dev/null; then
    echo "Error: This script must be run inside WSL2 (Ubuntu)"
    echo "On Windows, run: wsl -d Ubuntu"
    exit 1
fi

echo "Running as user: $(whoami)"
echo ""

# 2. Update packages & install dependencies
echo "[1/5] Installing OS dependencies (SDL2, OpenSSL, GCC, Python, Git)..."
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
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
    g++ \
    net-tools \
    libx11-dev

echo "[OK] OS packages installed."
echo ""

# 3. Install PlatformIO
echo "[2/5] Installing PlatformIO Core..."
if ! command -v pio &> /dev/null; then
    pip install --break-system-packages platformio || pip install platformio
fi
echo "[OK] PlatformIO ready: $(pio --version)"
echo ""

# 4. Clone or update CrossPoint Reader firmware
echo "[3/5] Setting up CrossPoint Reader repository..."
TARGET_DIR="$HOME/crosspoint-reader"
if [ ! -d "$TARGET_DIR" ]; then
    git clone https://github.com/crosspoint-reader/crosspoint-reader.git "$TARGET_DIR"
fi

cd "$TARGET_DIR"

# 5. Build simulator
echo "[4/5] Building CrossPoint X3 Simulator binary..."
mkdir -p sdcard/.fonts sdcard/books fs_/.fonts fs_/books fs_/.crosspoint
cp lib/EpdFont/builtinFonts/source/Ubuntu/Ubuntu-Vietnamese-*.ttf fs_/.fonts/ 2>/dev/null || true
cp lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-*.ttf fs_/.fonts/ 2>/dev/null || true

pio run -e simulator_x3

# 6. Configure launcher script
echo "[5/5] Configuring startup script..."
cat > "$TARGET_DIR/run_simulator.sh" << 'EOF'
#!/usr/bin/env bash
set -e

export DISPLAY="${DISPLAY:-:0}"
export WAYLAND_DISPLAY="${WAYLAND_DISPLAY:-wayland-0}"
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/mnt/wslg/runtime-dir}"
export PULSE_SERVER="${PULSE_SERVER:-unix:/mnt/wslg/PulseServer}"

cd ~/crosspoint-reader

mkdir -p sdcard/.fonts sdcard/books fs_/.fonts fs_/books fs_/.crosspoint
cp lib/EpdFont/builtinFonts/source/Ubuntu/Ubuntu-Vietnamese-*.ttf fs_/.fonts/ 2>/dev/null || true
cp lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-*.ttf fs_/.fonts/ 2>/dev/null || true

HOST_IP=$(ip route show | grep default | awk '{print $3}' | head -n1)
[ -z "$HOST_IP" ] && HOST_IP="127.0.0.1"

cat > fs_/.crosspoint/opds.json << OPDS_EOF
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
OPDS_EOF

echo "======================================================"
echo "    CROSSPOINT READER - XTEINK X3 DESKTOP EMULATOR    "
echo "======================================================"
echo " [!] Device Profile: Xteink X3 (792x528 E-ink Framebuffer)"
echo " [!] Key Controls:"
echo "     - Arrow Keys: Navigate / Turn Pages"
echo "     - Enter / Space: Select / Open Book"
echo "     - ESC / Backspace: Back"
echo "     - Left Click: Touch / Swipe"
echo "     - P key: Power / Sleep"
echo " [!] Kết nối Termux Android:"
echo "     - http://192.168.1.15:8080/opds (Wi-Fi hiện tại)"
echo "     - http://192.168.1.16:8080/opds (Wi-Fi hiện tại)"
echo "     - http://192.168.43.1:8080/opds (Hotspot)"
echo "     - http://ztruyen.local:8080/opds (mDNS Zeroconf)"
echo "======================================================"
echo ""

exec ./.pio/build/simulator_x3/program
EOF

chmod +x "$TARGET_DIR/run_simulator.sh"

echo ""
echo "======================================================"
echo "  CROSSPOINT VIRTUAL MACHINE SETUP COMPLETE!"
echo "======================================================"
echo "  Run simulator via: ~/crosspoint-reader/run_simulator.sh"
echo "  Or from Windows: double-click run_crosspoint_x3.bat"
echo "======================================================"
