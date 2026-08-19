#!/bin/bash
# setup-ztruyen-wsl2.sh
# Setup script for Z-Truyen on WSL2 Ubuntu

set -e

echo "========================================"
echo "  Z-Truyen X3 - WSL2 Setup"
echo "========================================"
echo ""

# Check if running in WSL
if ! grep -qEi "(microsoft|wsl)" /proc/version 2>/dev/null; then
    echo "Error: This script must be run in WSL2"
    echo "On Windows, run: wsl -d Ubuntu-22.04"
    exit 1
fi

# Get username
USERNAME=$(whoami)
echo "Running as: $USERNAME"
echo ""

# Step 1: Update packages
echo "[1/8] Updating packages..."
sudo apt update && sudo apt upgrade -y
echo "Done."
echo ""

# Step 2: Install dependencies
echo "[2/8] Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    git \
    curl \
    wget \
    unzip \
    build-essential \
    pkg-config \
    libsdl2-dev \
    libssl-dev \
    ca-certificates \
    cmake \
    g++ \
    net-tools \
    netcat
echo "Done."
echo ""

# Step 3: Install PlatformIO
echo "[3/8] Installing PlatformIO..."
if ! command -v pio &> /dev/null; then
    python3 -m venv ~/.venvs/pio
    source ~/.venvs/pio/bin/activate
    pip install --upgrade pip
    pip install platformio
    echo "PlatformIO installed."
else
    echo "PlatformIO already installed."
fi
echo ""

# Step 4: Clone/Copy Backend
echo "[4/8] Setting up Z-Truyen Backend..."
WORKSPACE="$HOME/workspace"
mkdir -p "$WORKSPACE"

if [ -d "$WORKSPACE/ztruyen-backend" ]; then
    echo "Backend already exists. Updating..."
    cd "$WORKSPACE/ztruyen-backend"
    git pull
else
    echo "Please enter the path to your Z-Truyen backend folder"
    echo "Or press Enter to clone from Git:"
    read -p "Backend path/Git URL: " backend_path

    if [ -z "$backend_path" ]; then
        echo "Please manually copy your backend to: $WORKSPACE/ztruyen-backend"
    elif [[ "$backend_path" == http* ]]; then
        git clone "$backend_path" "$WORKSPACE/ztruyen-backend"
    else
        cp -r "$backend_path" "$WORKSPACE/ztruyen-backend"
    fi
fi
echo ""

# Step 5: Setup Python venv
echo "[5/8] Setting up Python environment..."
cd "$WORKSPACE/ztruyen-backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn httpx lxml ebooklib Pillow pytest pytest-asyncio
pip install -e .

echo "Python environment ready."
echo ""

# Step 6: Clone CrossPoint Simulator
echo "[6/8] Setting up CrossPoint Simulator..."
if [ ! -d "$WORKSPACE/crosspoint-simulator" ]; then
    cd "$WORKSPACE"
    git clone https://github.com/crosspoint-reader/crosspoint-simulator.git
fi

echo "Simulator cloned to: $WORKSPACE/crosspoint-simulator"
echo ""

# Step 7: Create startup scripts
echo "[7/8] Creating startup scripts..."

# Backend start script
cat > "$HOME/start-backend.sh" << 'EOF'
#!/bin/bash
cd ~/workspace/ztruyen-backend
source venv/bin/activate

IP=$(hostname -I | awk '{print $1}')

echo "========================================"
echo "  Z-Truyen Backend"
echo "========================================"
echo ""
echo "OPDS URL: http://$IP:8080/opds"
echo "mDNS:     http://ztruyen.local:8080/opds"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================"
echo ""

uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
EOF

chmod +x "$HOME/start-backend.sh"

# Simulator start script
cat > "$HOME/start-simulator.sh" << 'EOF'
#!/bin/bash
cd ~/workspace/crosspoint-simulator

echo "========================================"
echo "  CrossPoint Simulator"
echo "========================================"
echo ""
echo "Building simulator..."
pio run -e simulator_x3

echo ""
echo "Starting simulator..."
pio run -e simulator_x3 -t upload
EOF

chmod +x "$HOME/start-simulator.sh"

# Quick start (both)
cat > "$HOME/start-ztruyen.sh" << 'EOF'
#!/bin/bash
echo "========================================"
echo "  Z-Truyen + Simulator"
echo "========================================"

# Get IP
IP=$(hostname -I | awk '{print $1}')

echo ""
echo "Backend: http://$IP:8080/opds"
echo "Simulator: pio run -e simulator_x3 -t upload"
echo ""
echo "Starting backend in background..."
echo ""

# Start backend
cd ~/workspace/ztruyen-backend
source venv/bin/activate
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 &
BACKEND_PID=$!

echo "Backend started (PID: $BACKEND_PID)"
echo ""
echo "Press Ctrl+C to stop both"
echo "========================================"

# Wait for interrupt
trap "kill $BACKEND_PID 2>/dev/null; exit" INT TERM
wait
EOF

chmod +x "$HOME/start-ztruyen.sh"

echo "Scripts created:"
echo "  ~/start-backend.sh    - Start backend only"
echo "  ~/start-simulator.sh - Start simulator only"
echo "  ~/start-ztruyen.sh   - Start both"
echo ""

# Step 8: Verify
echo "[8/8] Verifying installation..."
cd "$WORKSPACE/ztruyen-backend"
source venv/bin/activate

echo "Testing backend..."
timeout 5 python -c "
from ztruyen_backend.main import app
print('Backend module: OK')
" 2>/dev/null && echo "Backend: OK" || echo "Backend: FAILED"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Quick Start:"
echo "  1. Run: ~/start-backend.sh"
echo "  2. Copy WSL IP shown"
echo "  3. In simulator: Settings > OPDS > Add Server"
echo "  4. URL: http://<IP>:8080/opds"
echo ""
echo "Or run both: ~/start-ztruyen.sh"
echo ""
echo "========================================"
