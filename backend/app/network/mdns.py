"""mDNS / Zeroconf Service Discovery module for Z-Truyen.

Broadcasts 'ztruyen.local' and '_http._tcp.local.' so Xteink X3 and other
e-readers can discover the OPDS catalog automatically across Wi-Fi & Hotspots.
"""

import socket
from typing import Optional
from app.logging import logger

try:
    from zeroconf import Zeroconf, ServiceInfo
    ZEROCONF_AVAILABLE = True
except ImportError:
    ZEROCONF_AVAILABLE = False


def get_local_ip_addresses() -> list[str]:
    """Retrieve all non-loopback IPv4 addresses on local interfaces, prioritizing Hotspot and LAN over Cellular."""
    ip_list: list[str] = []

    # 1. Try parsing system network interfaces via 'ip -4 -o addr show' (Linux / Android Termux)
    try:
        import subprocess
        out = subprocess.check_output(['ip', '-4', '-o', 'addr', 'show'], text=True, stderr=subprocess.DEVNULL)
        hotspot_ips: list[str] = []
        wifi_ips: list[str] = []
        other_ips: list[str] = []

        for line in out.strip().split('\n'):
            parts = line.split()
            if len(parts) >= 4:
                ifname = parts[1].lower()
                ip = parts[3].split('/')[0]
                if ip.startswith('127.'):
                    continue
                if any(h in ifname for h in ['ap', 'softap', 'swlan', 'wlan1', 'rndis', 'tether']) or ip.startswith('192.168.43.'):
                    hotspot_ips.append(ip)
                elif any(w in ifname for w in ['wlan0', 'eth', 'en', 'wlan']):
                    wifi_ips.append(ip)
                elif not any(c in ifname for c in ['rmnet', 'ccmni', 'pdp', 'dummy', 'tun', 'tap', 'v4-']):
                    other_ips.append(ip)
                else:
                    other_ips.append(ip)

        for ip in hotspot_ips + wifi_ips + other_ips:
            if ip not in ip_list:
                ip_list.append(ip)
    except Exception:
        pass

    # 2. Try socket route fallback
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        s.connect(("8.8.8.8", 80))
        route_ip = s.getsockname()[0]
        s.close()
        if route_ip and not route_ip.startswith("127.") and route_ip not in ip_list:
            ip_list.append(route_ip)
    except Exception:
        pass

    # 3. Fallback to hostname resolution
    try:
        hostname = socket.gethostname()
        for ip in socket.gethostbyname_ex(hostname)[2]:
            if ip not in ip_list and not ip.startswith("127."):
                ip_list.append(ip)
    except Exception:
        pass

    if not ip_list:
        ip_list.append("127.0.0.1")

    return ip_list


class MdnsService:
    """Manages mDNS advertisement lifecycle."""

    def __init__(self, port: int = 8080, service_name: str = "ztruyen"):
        self.port = port
        self.service_name = service_name
        self.zeroconf: Optional[Zeroconf] = None
        self.service_info: Optional[ServiceInfo] = None

    def start(self) -> None:
        """Register the mDNS service with all local IPv4 addresses."""
        if not ZEROCONF_AVAILABLE:
            logger.warning("[mDNS] Zeroconf library not installed; skipping mDNS broadcast.")
            return

        try:
            local_ips = get_local_ip_addresses()
            ip_bytes_list = []
            for ip in local_ips:
                try:
                    ip_bytes_list.append(socket.inet_aton(ip))
                except Exception:
                    pass

            if not ip_bytes_list:
                ip_bytes_list = [socket.inet_aton("127.0.0.1")]

            primary_ip = local_ips[0]
            server_name = f"{self.service_name}.local."
            full_service_type = "_http._tcp.local."
            full_service_name = f"Z-Truyen OPDS Server.{full_service_type}"

            properties = {
                "path": "/opds",
                "name": "Z-Truyen X3",
                "version": "1.0.0",
                "type": "opds-catalog",
            }

            self.service_info = ServiceInfo(
                type_=full_service_type,
                name=full_service_name,
                addresses=ip_bytes_list,
                port=self.port,
                properties=properties,
                server=server_name,
            )

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)
            logger.info(
                f"[mDNS] Registered service '{server_name}:{self.port}' -> IPs {local_ips} (http://{self.service_name}.local:{self.port}/opds)"
            )
        except Exception as e:
            logger.warning(f"[mDNS] Could not register mDNS service: {e}")

    def stop(self) -> None:
        """Unregister the mDNS service."""
        if self.zeroconf and self.service_info:
            try:
                self.zeroconf.unregister_service(self.service_info)
                self.zeroconf.close()
                logger.info("[mDNS] Unregistered mDNS service.")
            except Exception as e:
                logger.warning(f"[mDNS] Error unregistering service: {e}")
            finally:
                self.zeroconf = None
                self.service_info = None


mdns_service = MdnsService(port=8080)
