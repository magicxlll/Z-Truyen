#!/usr/bin/env bash
# ==============================================================================
#  Z-Truyen X3 — CrossVi Xteink X3 Desktop Simulator 1-Click Launcher for macOS
# ==============================================================================

set -e

# Resolve directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CROSSVI_DIR="$HOME/crossvi"
SIM_SD="$CROSSVI_DIR/.simulator-data/x3"

echo "========================================================================"
echo "    CROSSVI XTEINK X3 DESKTOP SIMULATOR (macOS Apple Silicon / Intel)   "
echo "========================================================================"
echo ""

# 1. Check Homebrew
if ! command -v brew &>/dev/null; then
    if [ -f "/opt/homebrew/bin/brew" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -f "/usr/local/bin/brew" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    else
        echo "[ERROR] Không tìm thấy Homebrew! Vui lòng cài đặt Homebrew tại https://brew.sh/"
        echo "Nhấn phím bất kỳ để thoát..."
        read -n 1
        exit 1
    fi
fi

# Ensure Homebrew path in current session
eval "$($(which brew) shellenv)"

# 2. Check SDL2 & Build Tools
echo "[1/4] Kiểm tra thư viện đồ họa SDL2 & PlatformIO..."
MISSING_PKGS=""
if ! command -v sdl2-config &>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS sdl2 sdl2_image sdl2_ttf"
fi
if ! command -v pkg-config &>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS pkg-config"
fi
if ! command -v cmake &>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS cmake"
fi
if ! command -v pio &>/dev/null; then
    MISSING_PKGS="$MISSING_PKGS platformio"
fi

if [ -n "$MISSING_PKGS" ]; then
    echo "[*] Đang tự động cài đặt các gói còn thiếu:$MISSING_PKGS..."
    brew install $MISSING_PKGS
fi

# 3. Check CrossVi source & Apply 64-bit simulator compatibility patches
echo "[2/4] Kiểm tra mã nguồn CrossVi & Áp dụng vá lỗi tương thích macOS..."
if [ ! -d "$CROSSVI_DIR" ] || [ ! -f "$CROSSVI_DIR/platformio.ini" ]; then
    echo "[*] Đang tải mã nguồn CrossVi cùng các submodules..."
    git clone --recursive https://github.com/tvhdc/crossvi.git "$CROSSVI_DIR"
fi
python3 "$SCRIPT_DIR/scripts/patch_crossvi.py" "$CROSSVI_DIR"

# 4. Prepare SD Card & Pre-configure OPDS + Wi-Fi
echo "[3/4] Cấu hình thẻ nhớ ảo (Virtual SD) và thông số OPDS..."
mkdir -p "$SIM_SD/.crosspoint" "$SIM_SD/.fonts" "$SIM_SD/fonts" "$SIM_SD/books"

# Copy Vietnamese & Unicode Fonts
cp "$CROSSVI_DIR"/lib/EpdFont/builtinFonts/source/Ubuntu/Ubuntu-Vietnamese-*.ttf "$SIM_SD/.fonts/" 2>/dev/null || true
cp "$CROSSVI_DIR"/lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-*.ttf "$SIM_SD/.fonts/" 2>/dev/null || true
cp "$CROSSVI_DIR"/lib/EpdFont/builtinFonts/source/Ubuntu/Ubuntu-Vietnamese-*.ttf "$SIM_SD/fonts/" 2>/dev/null || true
cp "$CROSSVI_DIR"/lib/EpdFont/builtinFonts/source/NotoSans/NotoSans-*.ttf "$SIM_SD/fonts/" 2>/dev/null || true

# Pre-configure OPDS Servers (Termux Phone IPs & Localhost)
cat > "$SIM_SD/.crosspoint/opds.json" << 'EOF'
{
  "servers": [
    {
      "name": "Termux Phone (192.168.1.15)",
      "url": "http://192.168.1.15:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Termux Phone (192.168.1.14)",
      "url": "http://192.168.1.14:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Termux Hotspot (192.168.43.1)",
      "url": "http://192.168.43.1:8080/opds",
      "username": "",
      "password_obf": ""
    },
    {
      "name": "Mac Localhost (127.0.0.1)",
      "url": "http://127.0.0.1:8080/opds",
      "username": "",
      "password_obf": ""
    }
  ]
}
EOF

# Pre-save Wi-Fi credentials for auto-connection
cat > "$SIM_SD/.crosspoint/wifi.json" << 'EOF'
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

# Settings
if [ ! -f "$SIM_SD/.crosspoint/settings.json" ]; then
    cat > "$SIM_SD/.crosspoint/settings.json" << 'EOF'
{
  "opdsDownloadFolder": "/books",
  "opdsFilenameFormat": 0,
  "fontSize": 14,
  "language": "VI"
}
EOF
fi

# 5. Build simulator if needed
cd "$CROSSVI_DIR"
if [ ! -f ".pio/build/simulator_x3/program" ]; then
    echo "[*] Đang biên dịch máy ảo CrossVi X3 lần đầu (quá trình này mất khoảng 1 phút)..."
    pio run -e simulator_x3
fi

# 6. Launch Simulator
echo "[4/4] Khởi chạy máy ảo Xteink X3..."
echo ""
echo "========================================================================"
echo "  🎮 HƯỚNG DẪN ĐIỀU KHIỂN MÁY ẢO X3 (CONTROLS):"
echo "  - Phím Mũi tên Lên / Xuống : Cuộn danh sách / Di chuyển menu"
echo "  - Phím Mũi tên Trái / Phải : Lật trang sách trước / sau"
echo "  - Enter / Phím Cách (Space): Chọn / Mở sách / Xác nhận (OK)"
echo "  - ESC / Backspace          : Quay lại màn hình trước (Back)"
echo "  - Chuột Trái (Left Click)  : Cảm ứng chạm màn hình / Vuốt"
echo "  - Phím P                   : Khóa màn hình / Sleep"
echo ""
echo "  🌐 THÔNG SỐ OPDS ĐÃ NẠP SẴN:"
echo "  1. Termux Phone  : http://192.168.1.15:8080/opds"
echo "  2. Termux Phone  : http://192.168.1.14:8080/opds"
echo "  3. Termux Hotspot: http://192.168.43.1:8080/opds"
echo "  4. Mac Localhost : http://127.0.0.1:8080/opds"
echo "========================================================================"
echo ""
echo "🔍 Đang kiểm tra kết nối tới server..."
if curl -s -m 1 http://192.168.1.15:8080/healthz >/dev/null 2>&1; then
    echo "  ✅ Đã kết nối thành công tới Termux Phone (192.168.1.15:8080)!"
elif curl -s -m 1 http://192.168.1.14:8080/healthz >/dev/null 2>&1; then
    echo "  ✅ Đã kết nối thành công tới Termux Phone (192.168.1.14:8080)!"
elif curl -s -m 1 http://192.168.43.1:8080/healthz >/dev/null 2>&1; then
    echo "  ✅ Đã kết nối thành công tới Termux Hotspot (192.168.43.1:8080)!"
elif curl -s -m 1 http://127.0.0.1:8080/healthz >/dev/null 2>&1; then
    echo "  ✅ Đã kết nối thành công tới Mac Localhost (127.0.0.1:8080)!"
else
    echo "  ⚠️  Chưa thấy server nào đang mở. Hãy đảm bảo bạn đã mở Termux và chạy lệnh 'ztruyen' trên điện thoại!"
fi
echo ""

export CROSSVI_SIM_SD="$SIM_SD"
exec ./.pio/build/simulator_x3/program
