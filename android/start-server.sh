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

# Tự động giải phóng cổng 8080 triệt để (quét socket inode qua procfs + SIGKILL)
python3 -c "
import os, signal

def kill_process_on_port(port=8080):
    hex_port = f':{port:04X}'
    inodes = set()
    for net_file in ['/proc/net/tcp', '/proc/net/tcp6']:
        try:
            with open(net_file, 'r') as f:
                for line in f.readlines()[1:]:
                    parts = line.strip().split()
                    if len(parts) >= 10 and parts[1].endswith(hex_port):
                        inodes.add(parts[9])
        except Exception:
            pass

    if inodes:
        my_pid = os.getpid()
        for pid_str in os.listdir('/proc'):
            if pid_str.isdigit() and int(pid_str) != my_pid:
                pid = int(pid_str)
                fd_dir = f'/proc/{pid}/fd'
                try:
                    for fd in os.listdir(fd_dir):
                        try:
                            target = os.readlink(f'{fd_dir}/{fd}')
                            if any(f'[{inode}]' in target for inode in inodes):
                                os.kill(pid, signal.SIGKILL)
                                break
                        except Exception:
                            pass
                except Exception:
                    pass

kill_process_on_port(8080)
" 2>/dev/null || true
pkill -9 -f "uvicorn.*app.main:app" 2>/dev/null || true
pkill -9 -f "python.*app.main" 2>/dev/null || true
sleep 0.5

# Phân loại và lấy danh sách IP mạng nội bộ thông minh
NET_INFO=$(python3 -c "
import subprocess, re, os

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
cellular_keywords = ['rmnet', 'ccmni', 'pdp', 'dummy', 'tun', 'tap', 'v4-', 'radio', 'wwan', 'cellular', 'seth_w', 'ipa']

for ifname, ip in interfaces:
    ifn_lower = ifname.lower()
    # 1. Mạng di động (4G/5G Cellular): IP dạng 10.x.x.x, 100.x.x.x hoặc card mạng di động
    if ip.startswith('10.') or ip.startswith('100.') or any(c in ifn_lower for c in cellular_keywords):
        cell_ips.append((ifname, ip))
    # 2. Hotspot (Điểm phát sóng): card ap, softap, swlan, wlan1 hoặc dải 192.168.43.x / 192.168.50.x
    elif any(h in ifn_lower for h in ['ap', 'softap', 'swlan', 'wlan1', 'rndis', 'tether']) or ip.startswith('192.168.43.') or ip.startswith('192.168.50.'):
        hotspot_ips.append((ifname, ip))
    # 3. Wi-Fi gia đình (LAN)
    elif ip.startswith('192.168.') or ip.startswith('172.'):
        wifi_ips.append((ifname, ip))
    else:
        cell_ips.append((ifname, ip))

# Tự động dò tìm qua bảng ARP nếu X3 đã kết nối Hotspot
try:
    if os.path.exists('/proc/net/arp'):
        with open('/proc/net/arp', 'r') as f:
            for line in f.readlines()[1:]:
                parts = line.strip().split()
                if len(parts) >= 6:
                    client_ip = parts[0]
                    dev = parts[5]
                    if client_ip.startswith('192.168.') or client_ip.startswith('172.'):
                        prefix = '.'.join(client_ip.split('.')[:3])
                        gw = f'{prefix}.1'
                        if not any(ip == gw for _, ip in hotspot_ips):
                            hotspot_ips.append((dev, gw))
except Exception:
    pass

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
CELL_LIST=$(echo "$NET_INFO" | grep '^CELL' | cut -d'|' -f3 || true)

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
elif [ -z "$WIFI_LIST" ]; then
    echo " 📶 [CHẾ ĐỘ HOTSPOT DI ĐỘNG] (Khi ra ngoài / Tắt Wi-Fi dùng 5G Hotspot):"
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

if [ -n "$CELL_LIST" ]; then
    echo " 📡 [DỮ LIỆU DI ĐỘNG 4G/5G] Đã kết nối mạng 5G (Sẵn sàng cào truyện mới)."
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
