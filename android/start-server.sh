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

# Đảm bảo toàn quyền đọc/ghi cho thư mục dữ liệu và cache (chỉ trên thư mục data)
mkdir -p "$PROJECT_ROOT/backend/data/cache/epubs" 2>/dev/null || true
mkdir -p "$PROJECT_ROOT/backend/data/cache/covers" 2>/dev/null || true
chmod -R u+rwx "$PROJECT_ROOT/backend/data" 2>/dev/null || true

# Phân loại và lấy danh sách IP mạng nội bộ thông minh
NET_INFO=$(python3 -c "
import subprocess, re

def get_interfaces():
    results = []
    # 1. Thử qua lệnh ip -4 -o addr show
    try:
        out = subprocess.check_output(['ip', '-4', '-o', 'addr', 'show'], text=True, stderr=subprocess.DEVNULL)
        for line in out.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                ifname = parts[1]
                ip_mask = parts[3]
                ip = ip_mask.split('/')[0]
                if not ip.startswith('127.'):
                    results.append((ifname, ip))
        if results:
            return results
    except Exception:
        pass

    # 2. Thử qua ifconfig
    try:
        out = subprocess.check_output(['ifconfig'], text=True, stderr=subprocess.DEVNULL)
        current_if = 'wlan0'
        for line in out.split('\n'):
            if line and not line.startswith(' '):
                current_if = line.split(':')[0].split()[0]
            m = re.search(r'inet\s+(?:addr:)?(\d+\.\d+\.\d+\.\d+)', line)
            if m:
                ip = m.group(1)
                if not ip.startswith('127.'):
                    results.append((current_if, ip))
        if results:
            return results
    except Exception:
        pass

    return results

interfaces = get_interfaces()

hotspot_ips = []
wifi_ips = []
cell_ips = []

for ifname, ip in interfaces:
    ifn_lower = ifname.lower()
    if any(h in ifn_lower for h in ['ap', 'softap', 'swlan', 'wlan1', 'rndis', 'tether']) or ip.startswith('192.168.43.'):
        hotspot_ips.append((ifname, ip))
    elif any(w in ifn_lower for w in ['wlan0', 'eth', 'en', 'wlan']):
        wifi_ips.append((ifname, ip))
    elif any(c in ifn_lower for c in ['rmnet', 'ccmni', 'pdp', 'dummy', 'tun', 'tap', 'v4-']):
        cell_ips.append((ifname, ip))
    else:
        wifi_ips.append((ifname, ip))

if hotspot_ips:
    for ifn, ip in hotspot_ips:
        print(f'HOTSPOT|{ifn}|{ip}')
if wifi_ips:
    for ifn, ip in wifi_ips:
        print(f'WIFI|{ifn}|{ip}')
if cell_ips:
    for ifn, ip in cell_ips:
        print(f'CELL|{ifn}|{ip}')
" 2>/dev/null || true)

HOTSPOT_LIST=$(echo "$NET_INFO" | grep '^HOTSPOT' | cut -d'|' -f3 || true)
WIFI_LIST=$(echo "$NET_INFO" | grep '^WIFI' | cut -d'|' -f3 || true)

echo ""
echo "======================================================================"
echo "    🚀 Z-TRUYEN X3 POCKET HOST SERVER ĐANG HOẠT ĐỘNG (PORT $PORT)    "
echo "======================================================================"
echo ""

if [ -n "$HOTSPOT_LIST" ]; then
    echo " 📶 [CHẾ ĐỘ HOTSPOT DI ĐỘNG] Điện thoại đang phát Wi-Fi Hotspot:"
    for ip in $HOTSPOT_LIST; do
        echo "    👉 http://$ip:$PORT/opds"
    done
    echo ""
else
    echo " 📶 [CHẾ ĐỘ HOTSPOT DI ĐỘNG] (Khi ra ngoài / Điểm phát sóng di động):"
    echo "    👉 http://192.168.43.1:$PORT/opds (hoặc IP Gateway cấp cho X3)"
    echo ""
fi

if [ -n "$WIFI_LIST" ]; then
    echo " 🏠 [CHẾ ĐỘ WI-FI GIA ĐÌNH/LAN] Cả điện thoại & X3 cùng chung Router:"
    for ip in $WIFI_LIST; do
        echo "    👉 http://$ip:$PORT/opds"
    done
    echo "    👉 http://ztruyen.local:$PORT/opds  (Tự động nhận diện mDNS)"
    echo ""
fi

echo " ----------------------------------------------------------------------"
echo " ⚠️  LƯU Ý QUAN TRỌNG KHI KẾT NỐI BẰNG HOTSPOT (ĐIỆN THOẠI PHÁT WI-FI):"
echo "    1. Băng tần Hotspot: Bắt buộc chọn [2.4 GHz] (X3 KHÔNG hỗ trợ 5.0 GHz)."
echo "    2. Bảo mật Hotspot: Chọn [WPA2-Personal] (tránh WPA3 gây lỗi bắt tay)."
echo "    3. Địa chỉ OPDS: Nhập trực tiếp IP ở mục [📶], KHÔNG dùng ztruyen.local."
echo "    4. Tắt VPN/AdGuard trên điện thoại nếu đang bật."
echo "    5. Thứ tự chuẩn: Bật 4G & Hotspot TRƯỚC -> Mở Termux gõ 'ztruyen'."
echo " ----------------------------------------------------------------------"
echo ""
echo " 🔒 MẸO GIỮ SERVER CHẠY LIÊN TỤC KHI TẮT MÀN HÌNH (CHO X3 ĐỌC TRUYỆN):"
echo "    1. Kéo thanh thông báo Android từ trên xuống."
echo "    2. Tại thông báo của Termux -> Bấm nút [Acquire wakelock]."
echo "    3. Khóa app Termux trong trình đa nhiệm (biểu tượng Ổ Khóa 🔒)."
echo ""
echo " 💡 Nhấn tổ hợp phím [Ctrl + C] trên bàn phím để tắt server."
echo "======================================================================"
echo ""

cd "$PROJECT_ROOT/backend"
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --timeout-keep-alive 75 --limit-concurrency 100
