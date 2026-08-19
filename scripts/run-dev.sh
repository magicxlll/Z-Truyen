#!/bin/bash
# Start Z-Truyen backend and CrossVi simulator
# Usage: ./run-dev.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "${SCRIPT_DIR}")"

# Get local IP address for OPDS server
# Try en0 first (Wi-Fi), then en1 (Ethernet), fallback to localhost
IP=$(ipconfig getifaddr en0 2>/dev/null) || IP=$(ipconfig getifaddr en1 2>/dev/null) || IP="localhost"

echo "=================================================="
echo "  Z-Truyen Backend & OPDS Server"
echo "=================================================="
echo ""
echo "  OPDS URL for X3/CrossVi: http://$IP:8080/opds"
echo "  Backend: http://$IP:8080"
echo ""
echo "  Press Ctrl+C to stop"
echo "=================================================="
echo ""

# Change to backend directory
cd "${PROJECT_ROOT}/ztruyen_backend"

# Check for virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies if needed
pip install -q -e ".[dev]" 2>/dev/null || pip install -q -e .

# Start backend
echo "Starting Z-Truyen backend..."
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID)"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "Stopping backend (PID: $BACKEND_PID)..."
    kill $BACKEND_PID 2>/dev/null || true
    echo "Done."
}

# Set trap for cleanup
trap cleanup INT TERM

# Wait for user interrupt
echo "Press Ctrl+C to stop..."
wait $BACKEND_PID
