#!/usr/bin/env python3
"""
Z-Truyen X3 — Realtime Hotspot & Connection Monitor.
Monitors Wi-Fi connection from Xteink X3 (MAC f8:5b:1b:fc:3f:a0),
captures live HTTP requests on port 8080, and diagnoses Wi-Fi handshake issues.
"""

from __future__ import annotations

import os
import re
import socket
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

TARGET_MAC = "f8:5b:1b:fc:3f:a0"
X3_CONNECTED = False
X3_IP = None


def get_arp_clients() -> list[dict]:
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
                    mac = parts[3].lower().replace("-", ":")
                    dev = parts[5]
                    if flags == "0x2" and mac != "00:00:00:00:00:00":
                        clients.append({"ip": ip, "mac": mac, "dev": dev})
        except Exception:
            pass
    return clients


def get_interfaces() -> list[dict]:
    interfaces = []
    try:
        import subprocess
        out = subprocess.check_output(["ip", "-4", "-o", "addr", "show"], text=True, stderr=subprocess.DEVNULL)
        for line in out.split("\n"):
            parts = line.split()
            if len(parts) >= 4:
                ifname = parts[1]
                ip = parts[3].split("/")[0]
                if not ip.startswith("127."):
                    interfaces.append({"name": ifname, "ip": ip})
    except Exception:
        pass
    return interfaces


class LiveDebugHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        client_ip = self.client_address[0]
        print(f"\n🔥 [NHẬN KẾT NỐI TỪ X3!] IP: {client_ip} -> Đường dẫn: {self.path}")
        print(f"   Headers: {dict(self.headers)}")
        
        # Respond with valid OPDS or Healthz
        self.send_response(200)
        if "/opds" in self.path:
            self.send_header("Content-Type", "application/atom+xml;charset=utf-8")
            self.end_headers()
            xml = """<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>tag:ztruyen:test</id>
  <title>Z-Truyen X3 Test Feed</title>
  <updated>2026-08-22T00:00:00Z</updated>
  <author><name>Z-Truyen</name></author>
  <entry>
    <title>✅ KẾT NỐI HOTSPOT THÀNH CÔNG!</title>
    <id>tag:ztruyen:success</id>
    <updated>2026-08-22T00:00:00Z</updated>
    <content type="text">Chúc mừng! Máy X3 đã kết nối thành công với điện thoại qua 5G Hotspot.</content>
  </entry>
</feed>"""
            self.wfile.write(xml.encode("utf-8"))
        else:
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status":"ok","message":"Z-Truyen Hotspot Ready"}')

    def log_message(self, format, *args):
        # Suppress default server log
        pass


def run_live_monitor():
    print("\n" + "=" * 70)
    print("    📡 Z-TRUYEN X3 — TRÌNH GIÁM SÁT KẾT NỐI HOTSPOT THỜI GIAN THỰC")
    print("=" * 70)
    print(f"🎯 Thiết bị mục tiêu: Máy đọc sách Xteink X3 (MAC: {TARGET_MAC})")
    print("⏳ Đang lắng nghe kết nối Wi-Fi và yêu cầu OPDS trên cổng 8080...")
    print("=" * 70 + "\n")

    # Start dummy/test server on port 8080 if not already running
    server = None
    try:
        server = HTTPServer(("0.0.0.0", 8080), LiveDebugHandler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        print("✅ Đã mở cổng kiểm tra 8080 thành công.")
    except Exception as e:
        print(f"ℹ️ Cổng 8080 đang được chạy bởi tiến trình khác ({e}). Tiếp tục giám sát ARP...")

    start_time = time.time()
    found_x3 = False

    while True:
        clients = get_arp_clients()
        interfaces = get_interfaces()

        for c in clients:
            mac = c["mac"].lower()
            ip = c["ip"]
            dev = c["dev"]
            prefix = ".".join(ip.split(".")[:3])
            gw_ip = f"{prefix}.1"

            if not found_x3 and (mac == TARGET_MAC.lower() or "f8:5b:1b" in mac):
                found_x3 = True
                print(f"\n🎉 [THÀNH CÔNG: ĐÃ BẮT ĐƯỢC MÁY X3!]")
                print(f"   • IP máy X3: {ip}")
                print(f"   • MAC máy X3: {mac}")
                print(f"   • Card kết nối: {dev}")
                print(f"   👉 ĐỊA CHỈ OPDS CHÍNH XÁC: http://{gw_ip}:8080/opds\n")
                print("👉 Bây giờ trên máy X3, hãy bấm vào nguồn 'zhost' để tải truyện!")

        elapsed = int(time.time() - start_time)
        if not found_x3 and elapsed > 0 and elapsed % 10 == 0:
            print(f"⏳ Đang chờ máy X3 kết nối vào Wi-Fi Hotspot... ({elapsed}s)")
            print("   ⚠️ NẾU TRÊN X3 HIỆN 'Tìm thấy 0 mạng' HOẶC 'Đang kết nối...':")
            print("      1. TẮT 'Chuẩn Wi-Fi 6' trên Hotspot điện thoại.")
            print("      2. TẮT 'Khung quản lý được bảo vệ' (PMF) hoặc chọn WPA2-Personal.")
            print("      3. Đảm bảo băng tần là 2.4 GHz.")
            print("      4. TẮT 'Ẩn điểm phát sóng' (Broadcast SSID).")
            print("-" * 60)

        time.sleep(1.5)


if __name__ == "__main__":
    try:
        run_live_monitor()
    except KeyboardInterrupt:
        print("\n[OK] Đã dừng giám sát.")
