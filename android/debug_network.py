#!/usr/bin/env python3
# Z-Truyen X3 — Deep Network Diagnostic & Hotspot IP Analyzer for Android Termux.
# Scans all network interfaces, ARP tables, routing tables, and socket listeners.

import os
import re
import socket
import subprocess
import sys
import urllib.request


def print_banner(text: str) -> None:
    print("\n" + "=" * 70)
    print(f"    🔍 {text}")
    print("=" * 70)


def get_cmd_output(cmd: list) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def parse_interfaces() -> list:
    interfaces = []
    out = get_cmd_output(["ip", "-4", "-o", "addr", "show"])
    if out:
        for line in out.split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                ifname = parts[1]
                ip_mask = parts[3]
                ip = ip_mask.split("/")[0]
                mask = ip_mask.split("/")[1] if "/" in ip_mask else "32"
                interfaces.append({"name": ifname, "ip": ip, "cidr": mask})
        if interfaces:
            return interfaces

    out = get_cmd_output(["ifconfig"])
    if out:
        current_if = "unknown"
        for line in out.split("\n"):
            if line and not line.startswith(" "):
                current_if = line.split(":")[0].split()[0]
            m = re.search(r"inet\s+(?:addr:)?(\d+\.\d+\.\d+\.\d+)", line)
            if m:
                interfaces.append({"name": current_if, "ip": m.group(1), "cidr": "24"})

    return interfaces


def parse_arp_table() -> list:
    clients = []
    if os.path.exists("/proc/net/arp"):
        try:
            with open("/proc/net/arp", "r") as f:
                lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 6:
                    ip = parts[0]
                    flags = parts[2]
                    mac = parts[3]
                    dev = parts[5]
                    if flags == "0x2" and mac != "00:00:00:00:00:00":
                        clients.append({"ip": ip, "mac": mac, "dev": dev})
        except Exception:
            pass
    return clients


def check_port_listener(port: int = 8080) -> list:
    hex_port = f":{port:04X}"
    listeners = []
    for net_file in ["/proc/net/tcp", "/proc/net/tcp6"]:
        if not os.path.exists(net_file):
            continue
        try:
            with open(net_file, "r") as f:
                lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 10:
                    local_addr = parts[1]
                    state = parts[3]
                    inode = parts[9]
                    if local_addr.endswith(hex_port) and state == "0A":
                        listeners.append({"file": net_file, "local": local_addr, "inode": inode})
        except Exception:
            pass
    return listeners


def test_http_endpoint(ip: str, port: int = 8080) -> bool:
    url = f"http://{ip}:{port}/healthz"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ZTruyen-Debugger"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def run_diagnostics():
    print_banner("Z-TRUYEN X3 — CÔNG CỤ CHẨN ĐOÁN MẠNG & HOTSPOT CHUYÊN SÂU")

    print("\n📋 1. DANH SÁCH CÁC CARD MẠNG (INTERFACES):")
    interfaces = parse_interfaces()
    if not interfaces:
        print("   ❌ Không tìm thấy card mạng nào.")
    else:
        for iface in interfaces:
            name = iface["name"]
            ip = iface["ip"]
            cidr = iface["cidr"]
            
            if ip.startswith("127."):
                desc = "Loopback (Nội bộ máy)"
            elif ip.startswith("10.") or ip.startswith("100.") or any(c in name.lower() for c in ["rmnet", "ccmni", "pdp", "v4-"]):
                desc = "📶 Mạng Dữ Liệu Di Động 4G/5G (Cellular WAN)"
            elif any(h in name.lower() for h in ["ap", "softap", "swlan", "wlan1", "rndis", "tether"]) or ip.startswith("192.168.43.") or ip.startswith("192.168.50."):
                desc = "🔥 Điểm Phát Sóng Di Động (Hotspot SoftAP)"
            elif ip.startswith("192.168.") or ip.startswith("172."):
                desc = "🏠 Mạng Wi-Fi / LAN Nội Bộ"
            elif any(t in name.lower() for t in ["tun", "tap", "dummy"]):
                desc = "🔒 VPN / Bộ Lọc Quảng Cáo (AdGuard/WARP)"
            else:
                desc = "Mạng khác"

            print(f"   • [{name}] {ip}/{cidr}  -->  {desc}")

    print("\n📱 2. KIỂM TRA THIẾT BỊ ĐANG KẾT NỐI VÀO HOTSPOT (BẢNG ARP):")
    arp_clients = parse_arp_table()
    detected_gw_ips = []
    if not arp_clients:
        print("   ⚠️ Chưa thấy máy đọc sách X3 gửi gói tin ARP.")
        print("      (Gợi ý: Đảm bảo máy X3 đã kết nối Wi-Fi Hotspot của điện thoại)")
    else:
        for client in arp_clients:
            c_ip = client["ip"]
            c_mac = client["mac"]
            c_dev = client["dev"]
            prefix = ".".join(c_ip.split(".")[:3])
            gw_ip = f"{prefix}.1"
            detected_gw_ips.append(gw_ip)
            print(f"   ✅ Phát hiện thiết bị kết nối: IP = {c_ip} | MAC = {c_mac} | Card = {c_dev}")
            print(f"      👉 IP Gateway (Điện thoại) cho dải này: {gw_ip}")

    print("\n🔌 3. KIỂM TRA TRẠNG THÁI SERVER CỔNG 8080:")
    listeners = check_port_listener(8080)
    if listeners:
        print("   ✅ Server Z-Truyen ĐANG LẮNG NGHE trên cổng 8080 (0.0.0.0:8080).")
    else:
        print("   ❌ Server Z-Truyen CHƯA CHẠY trên cổng 8080!")
        print("      (Hãy chạy lệnh 'ztruyen' trong một cửa sổ Termux khác)")

    print("\n🌐 4. KIỂM TRA ĐỘ PHẢN HỒI HTTP API:")
    loopback_ok = test_http_endpoint("127.0.0.1", 8080)
    print(f"   • Loopback [127.0.0.1:8080]: {'✅ OK (Phản hồi tốt)' if loopback_ok else '❌ Không phản hồi'}")

    candidate_ips = []
    for iface in interfaces:
        ip = iface["ip"]
        if not ip.startswith("127.") and not ip.startswith("10.") and not ip.startswith("100."):
            candidate_ips.append(ip)
    for gw in detected_gw_ips:
        if gw not in candidate_ips:
            candidate_ips.append(gw)

    if "192.168.43.1" not in candidate_ips:
        candidate_ips.append("192.168.43.1")

    for ip in candidate_ips:
        res = test_http_endpoint(ip, 8080)
        status_text = "✅ KẾT NỐI THÀNH CÔNG" if res else "⚠️ Chưa phản hồi trực tiếp"
        print(f"   • Thử IP [{ip}:8080]: {status_text}")

    has_vpn = any("tun" in iface["name"].lower() for iface in interfaces)
    if has_vpn:
        print("\n⚠️ CẢNH BÁO VPN:")
        print("   Phát hiện interface VPN (tun). Nếu bạn đang bật 1.1.1.1 WARP, AdGuard hoặc VPN,")
        print("   hãy TẮT VPN trên điện thoại vì nó sẽ chặn kết nối từ máy X3 vào cổng 8080!")

    print("\n" + "=" * 70)
    print("    🎯 ĐỊA CHỈ OPDS CẦN THỬ TRÊN MÁY XTEINK X3:")
    print("=" * 70)
    
    for idx, ip in enumerate(candidate_ips, 1):
        print(f"   👉 Tùy chọn {idx}: http://{ip}:8080/opds")

    print("\n💡 HƯỚNG DẪN KIỂM TRA & KHẮC PHỤC TRÊN MÁY X3 & ĐIỆN THOẠI:")
    print("   1. Trên X3: Vào Cài đặt Wi-Fi -> Bấm vào tên Hotspot -> Xem dòng 'Gateway'.")
    print("   2. Mở OPDS Browser trên X3 -> Nhập URL theo đúng số IP Gateway đó.")
    print("   3. NẾU VẪN BÁO LỖI: Trên điện thoại, vào Cài đặt -> Cài đặt nhà phát triển (Developer Options)")
    print("      -> TẮT mục 'Tăng tốc phần cứng chia sẻ kết nối' (Tethering hardware acceleration).")
    print("      (Khi tắt tính năng này, Android mới cho phép X3 kết nối vào cổng nội bộ 8080).")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    run_diagnostics()
