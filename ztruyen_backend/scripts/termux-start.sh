#!/bin/bash
# Z-Truyen Termux Quick Start Script
# Run this script after opening Termux

set -e

echo "=========================================="
echo "  Z-Truyen X3 - Quick Start"
echo "=========================================="
echo ""

# Check if in Termux
if [ ! -d "/data/data/com.termux/files/usr" ]; then
    echo "Error: This script must be run in Termux on Android"
    exit 1
fi

# Get local IP
get_ip() {
    ip route get 1 | awk '{print $(NF-2); exit}'
}

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting Z-Truyen Backend...${NC}"
echo ""

# Navigate to backend
cd ~/ztruyen_backend 2>/dev/null || {
    echo "Error: ztruyen_backend folder not found"
    echo "Please copy ztruyen_backend to ~/"
    exit 1
}

# Start avahi if not running
if ! pgrep -x avahi-daemon > /dev/null; then
    echo "Starting mDNS (avahi)..."
    avahi-daemon -D 2>/dev/null || true
    sleep 1
fi

# Get IP
IP=$(get_ip)
HOSTNAME="ztruyen.local"

echo "=========================================="
echo -e "${GREEN}Server Starting!${NC}"
echo "=========================================="
echo ""
echo "OPDS URLs:"
echo "  mDNS:  http://$HOSTNAME:8080/opds"
echo "  IP:    http://$IP:8080/opds"
echo ""
echo "On X3 CrossVi:"
echo "  Settings > OPDS > Add Server"
echo "  URL: http://$HOSTNAME:8080/opds"
echo ""
echo "Press Ctrl+C to stop server"
echo "=========================================="
echo ""

# Start server
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
