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

# 4. Tạo alias 'ztruyen' và 'ztruyen-update' để khởi động và cập nhật nhanh
echo ""
echo "[4/4] Đang tạo phím tắt lệnh 'ztruyen' và 'ztruyen-update'..."
START_SCRIPT="$DIR/start-server.sh"
chmod +x "$START_SCRIPT"

if ! grep -q "alias ztruyen=" ~/.bashrc 2>/dev/null; then
    echo "alias ztruyen='$START_SCRIPT'" >> ~/.bashrc
fi

if ! grep -q "alias ztruyen-update=" ~/.bashrc 2>/dev/null; then
    echo "alias ztruyen-update='cd ~/ztruyen && git fetch origin main && git reset --hard origin/main && $START_SCRIPT'" >> ~/.bashrc
fi

echo ""
echo "======================================================================"
echo "🎉 CÀI ĐẶT HOÀN TẤT!"
echo "======================================================================"
echo "👉 Từ bây giờ, bất cứ khi nào bạn muốn mở Server cho X3 tải truyện,"
echo "   bạn chỉ cần mở app Termux và gõ:  ztruyen"
echo "======================================================================"
echo ""
