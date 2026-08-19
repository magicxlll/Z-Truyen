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

echo ""
echo "[OK] Cập nhật thành công! Đang khởi chạy Server..."
echo ""
exec bash "$DIR/start-server.sh"
