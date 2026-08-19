"""Unit tests for mDNS service discovery."""

from app.network.mdns import get_local_ip_addresses, MdnsService


def test_get_local_ip_addresses():
    ips = get_local_ip_addresses()
    assert isinstance(ips, list)
    assert len(ips) > 0
    # Every returned IP should be a non-empty string
    for ip in ips:
        assert isinstance(ip, str)
        assert len(ip) > 0


def test_mdns_service_lifecycle():
    service = MdnsService(port=8888, service_name="test-ztruyen")
    service.start()
    # It should either succeed or fail gracefully without unhandled exception
    service.stop()
    assert service.zeroconf is None
