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
    """Retrieve all non-loopback IPv4 addresses on local interfaces."""
    ip_list = []
    try:
        # Connect a dummy UDP socket to find default route
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.5)
        # Use a public DNS IP without sending packets
        s.connect(("8.8.8.8", 80))
        primary_ip = s.getsockname()[0]
        s.close()
        if primary_ip and not primary_ip.startswith("127."):
            ip_list.append(primary_ip)
    except Exception:
        pass

    try:
        # Fallback to hostname resolution
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
        """Register the mDNS service."""
        if not ZEROCONF_AVAILABLE:
            logger.warning("[mDNS] Zeroconf library not installed; skipping mDNS broadcast.")
            return

        try:
            local_ips = get_local_ip_addresses()
            primary_ip = local_ips[0]
            ip_bytes = socket.inet_aton(primary_ip)

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
                addresses=[ip_bytes],
                port=self.port,
                properties=properties,
                server=server_name,
            )

            self.zeroconf = Zeroconf()
            self.zeroconf.register_service(self.service_info)
            logger.info(
                f"[mDNS] Registered service '{server_name}:{self.port}' -> IP {primary_ip} (http://{self.service_name}.local:{self.port}/opds)"
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
