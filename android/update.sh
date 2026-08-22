#!/usr/bin/env bash
# ==============================================================================
# Z-Truyen X3 — Script Cập Nhật Tự Động & Chống Xung Đột Triệt Để
# ==============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"

echo ""
echo "======================================================================"
echo "    🔄 ĐANG CẬP NHẬT Z-TRUYEN X3 TỪ GITHUB (TỰ ĐỘNG DỌN XUNG ĐỘT)...  "
echo "======================================================================"
cd "$PROJECT_ROOT"

# Tắt kiểm tra filemode của git để chống xung đột quyền file vĩnh viễn
git config core.filemode false 2>/dev/null || true

# Đăng ký các alias tiện ích nếu chưa có
DEBUG_SCRIPT="$DIR/debug-network.sh"
START_SCRIPT="$DIR/start-server.sh"
UPDATE_SCRIPT="$DIR/update.sh"

sed -i '/alias ztruyen=/d' ~/.bashrc 2>/dev/null || true
sed -i '/alias ztruyen-update=/d' ~/.bashrc 2>/dev/null || true
sed -i '/alias ztruyen-debug=/d' ~/.bashrc 2>/dev/null || true

echo "alias ztruyen='bash $START_SCRIPT'" >> ~/.bashrc
echo "alias ztruyen-update='bash $UPDATE_SCRIPT'" >> ~/.bashrc
echo "alias ztruyen-debug='bash $DEBUG_SCRIPT'" >> ~/.bashrc

echo ""
echo "[OK] Cập nhật thành công! Đang khởi chạy Server..."
echo ""
exec bash "$DIR/start-server.sh"
