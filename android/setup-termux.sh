#!/usr/bin/env bash
# ==============================================================================
# Z-Truyen X3 — Script Cài Đặt Tự Động Cho Android Termux
# ==============================================================================
set -e

echo ""
echo "======================================================================"
echo "    CÀI ĐẶT Z-TRUYEN POCKET HOST SERVER TRÊN ANDROID TERMUX          "
echo "======================================================================"
echo ""

# 1. Cập nhật package manager và cài đặt các công cụ biên dịch native C/C++
echo "[1/4] Đang cập nhật gói Termux và cài đặt môi trường Python, C/C++..."
pkg update -y
pkg install -y python git clang make rust binutils libxml2 libxslt libjpeg-turbo libffi openssl termux-tools

# 2. Tạo môi trường ảo Python chuyên biệt
echo ""
echo "[2/4] Đang tạo môi trường ảo Python (~/.ztruyen-venv)..."
python -m venv ~/.ztruyen-venv
source ~/.ztruyen-venv/bin/activate
pip install --upgrade pip wheel setuptools

# 3. Cài đặt các thư viện Python của Z-Truyen
echo ""
echo "[3/4] Đang cài đặt các thư viện Z-Truyen Backend (FastAPI, EbookLib, Zeroconf)..."
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

cd "$PROJECT_ROOT/backend"
pip install -r "$DIR/requirements-termux.txt"

# Tắt kiểm tra filemode của git để chống xung đột quyền file
git config core.filemode false 2>/dev/null || true

# 4. Tạo alias 'ztruyen', 'ztruyen-update', và 'ztruyen-debug'
echo ""
echo "[4/4] Đang tạo phím tắt lệnh 'ztruyen', 'ztruyen-update', 'ztruyen-debug'..."
START_SCRIPT="$DIR/start-server.sh"
UPDATE_SCRIPT="$DIR/update.sh"
DEBUG_SCRIPT="$DIR/debug-network.sh"
MONITOR_SCRIPT="$DIR/monitor-hotspot.sh"
chmod +x "$DIR"/*.sh 2>/dev/null || true

# Xóa alias cũ nếu có và tạo alias mới chuẩn xác
sed -i '/alias ztruyen=/d' ~/.bashrc 2>/dev/null || true
sed -i '/alias ztruyen-update=/d' ~/.bashrc 2>/dev/null || true
sed -i '/alias ztruyen-debug=/d' ~/.bashrc 2>/dev/null || true
sed -i '/alias ztruyen-monitor=/d' ~/.bashrc 2>/dev/null || true

echo "alias ztruyen='bash $START_SCRIPT'" >> ~/.bashrc
echo "alias ztruyen-update='bash $UPDATE_SCRIPT'" >> ~/.bashrc
echo "alias ztruyen-debug='bash $DEBUG_SCRIPT'" >> ~/.bashrc
echo "alias ztruyen-monitor='bash $MONITOR_SCRIPT'" >> ~/.bashrc

# Tạo symlink vào $PREFIX/bin để gọi lệnh trực tiếp không phụ thuộc vào bashrc
if [ -n "$PREFIX" ] && [ -d "$PREFIX/bin" ]; then
    ln -sf "$START_SCRIPT" "$PREFIX/bin/ztruyen" 2>/dev/null || true
    ln -sf "$UPDATE_SCRIPT" "$PREFIX/bin/ztruyen-update" 2>/dev/null || true
    ln -sf "$DEBUG_SCRIPT" "$PREFIX/bin/ztruyen-debug" 2>/dev/null || true
    ln -sf "$MONITOR_SCRIPT" "$PREFIX/bin/ztruyen-monitor" 2>/dev/null || true
fi

echo ""
echo "======================================================================"
echo "🎉 CÀI ĐẶT HOÀN TẤT!"
echo "======================================================================"
echo "👉 Từ bây giờ, bất cứ khi nào bạn muốn mở Server cho X3 tải truyện,"
echo "   bạn chỉ cần mở app Termux và gõ:  ztruyen"
echo "======================================================================"
echo ""
