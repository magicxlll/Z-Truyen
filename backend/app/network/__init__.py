"""Network utilities including mDNS service discovery."""
from app.network.mdns import mdns_service, get_local_ip_addresses

__all__ = ["mdns_service", "get_local_ip_addresses"]
