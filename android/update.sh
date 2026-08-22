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

# Đồng bộ cứng với origin/main, tự động xóa sạch file rác/file tạm
git fetch origin main --quiet
git reset --hard origin/main
chmod +x "$DIR"/*.sh 2>/dev/null || true

# Đăng ký các alias tiện ích và symlink vào $PREFIX/bin
DEBUG_SCRIPT="$DIR/debug-network.sh"
MONITOR_SCRIPT="$DIR/monitor-hotspot.sh"
START_SCRIPT="$DIR/start-server.sh"
UPDATE_SCRIPT="$DIR/update.sh"

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
echo "[OK] Cập nhật thành công! Đang khởi chạy Server..."
echo ""
exec bash "$DIR/start-server.sh"
