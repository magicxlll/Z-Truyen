#!/usr/bin/env bash
# ==============================================================================
# Z-Truyen X3 — Script Khởi Chạy Pocket Host Server Trên Android
# ==============================================================================
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$DIR")"
PORT=8080

# Kích hoạt môi trường ảo Python
if [ -d "$HOME/.ztruyen-venv" ]; then
    source "$HOME/.ztruyen-venv/bin/activate"
fi

# Chống Android đưa app vào chế độ ngủ sâu (Wake Lock)
if command -v termux-wake-lock &> /dev/null; then
    termux-wake-lock
fi

# Hàm dọn dẹp khi tắt server
cleanup() {
    echo ""
    echo "[*] Đang dừng Z-Truyen Server..."
    if command -v termux-wake-unlock &> /dev/null; then
        termux-wake-unlock
    fi
    echo "[OK] Đã tắt Server và giải phóng pin."
    exit 0
}
trap cleanup SIGINT SIGTERM EXIT

# Đảm bảo toàn quyền đọc/ghi cho thư mục dữ liệu và cache
chmod -R u+rwx "$PROJECT_ROOT" 2>/dev/null || true
mkdir -p "$PROJECT_ROOT/backend/data/cache/epubs" 2>/dev/null || true
mkdir -p "$PROJECT_ROOT/backend/data/cache/covers" 2>/dev/null || true

# Lấy danh sách địa chỉ IP mạng nội bộ hiện tại
IP_ADDRESSES=""
if command -v ip &> /dev/null; then
    IP_ADDRESSES=$(ip -4 addr show 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' || true)
elif command -v ifconfig &> /dev/null; then
    IP_ADDRESSES=$(ifconfig 2>/dev/null | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' || true)
fi

echo ""
echo "======================================================================"
echo "    🚀 Z-TRUYEN X3 POCKET HOST SERVER ĐANG HOẠT ĐỘNG (PORT $PORT)    "
echo "======================================================================"
echo ""
echo " 🌐 1. Tự động nhận diện (mDNS Zeroconf):"
echo "    http://ztruyen.local:$PORT/opds"
echo ""
echo " 📶 2. Khi bạn phát Điểm phát sóng di động (Hotspot):"
echo "    http://192.168.43.1:$PORT/opds"
echo ""
if [ -n "$IP_ADDRESSES" ]; then
    echo " 🏠 3. Địa chỉ IP Wi-Fi hiện tại của điện thoại:"
    for ip in $IP_ADDRESSES; do
        echo "    http://$ip:$PORT/opds"
    done
    echo ""
fi
echo " 📚 HƯỚNG DẪN DÀNH CHO MÁY ĐỌC SÁCH XTEINK X3:"
echo "    - Mở OPDS Browser trên X3"
echo "    - Nhập URL: http://ztruyen.local:$PORT/opds (hoặc IP ở trên)"
echo "    - Duyệt truyện & bấm Tải về máy!"
echo ""
echo " 💡 Nhấn tổ hợp phím [Ctrl + C] trên bàn phím để tắt server."
echo "======================================================================"
echo ""

cd "$PROJECT_ROOT/backend"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
