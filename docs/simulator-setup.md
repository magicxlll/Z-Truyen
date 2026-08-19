# CrossVi Simulator Setup Guide

This guide explains how to set up the Z-Truyen backend and CrossVi simulator on macOS for testing OPDS catalog integration with Xteink X3 devices.

## Prerequisites

- macOS (Apple Silicon M1/M2/M3/M4 or Intel)
- Python 3.12+
- Git
- SDL2 (for CrossVi simulator)
- Homebrew (for package management)

## Step 1: Clone CrossVi Repository

The CrossVi simulator is maintained in a separate repository. Clone it first:

```bash
git clone https://github.com/tvhdc/crossvi.git
cd crossvi
```

Alternatively, if using the CrossPoint Reader simulator:

```bash
git clone https://github.com/crosspoint-reader/crosspoint-reader.git
git clone https://github.com/uxjulia/crosspoint-simulator.git
cd crosspoint-simulator
```

## Step 2: Install Dependencies

### Python Dependencies

```bash
cd ztruyen_backend
pip install -r requirements.txt
```

### macOS System Dependencies

```bash
brew install sdl2 sdl2_image sdl2_ttf
brew install python@3.12
```

### Verify Installation

```bash
python3 --version  # Should show 3.12+
brew list sdl2     # Verify SDL2 installation
```

## Step 3: Build CrossVi Simulator (macOS Native)

### For Apple Silicon (M1-M4):

```bash
cd crosspoint-simulator
mkdir build && cd build
cmake .. -DCMAKE_OSX_ARCHITECTURES=arm64
make -j$(sysctl -n hw.ncpu)
```

### For Intel Mac:

```bash
cd crosspoint-simulator
mkdir build && cd build
cmake .. -DCMAKE_OSX_ARCHITECTURES=x86_64
make -j$(sysctl -n hw.ncpu)
```

### Universal Binary (Both Architectures):

```bash
cmake .. -DCMAKE_OSX_ARCHITECTURES="arm64;x86_64"
make -j$(sysctl -n hw.ncpu)
```

## Step 4: Run CrossVi Simulator

```bash
# From crosspoint-simulator/build directory
./crossvi_simulator
```

Or using the provided script:

```bash
python3 scripts/run_simulator.py x3
```

## Step 5: Configure OPDS Server on CrossVi/X3

1. On the simulator (or real X3 device), navigate to **Settings**
2. Select **OPDS** or **Wireless** > **OPDS Browser**
3. Add a new server with the following:
   - **Server Name**: `Z-Truyen Local`
   - **Server URL**: `http://<YOUR_MAC_IP>:8080/opds`

### Finding Your Local IP Address

```bash
# On macOS
ipconfig getifaddr en0   # For Wi-Fi
ipconfig getifaddr en1   # For Ethernet

# Or use:
ifconfig | grep "inet " | grep -v 127.0.0.1
```

## Running Z-Truyen Backend

### Option 1: Direct Python (Development)

```bash
cd ztruyen_backend
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### Option 2: Using the Helper Script

```bash
cd scripts
chmod +x run-dev.sh
./run-dev.sh
```

### Option 3: Docker (Production on Mac mini)

```bash
cd ztruyen_backend
docker compose up -d
```

## Verifying OPDS Connection

Once both backend and simulator are running:

1. Open OPDS Browser on CrossVi simulator
2. Select `Z-Truyen Local` server
3. You should see:
   - Hot/New stories
   - Genre categories
   - Search functionality

## Troubleshooting

### CrossVi Simulator Won't Start

```bash
# Check SDL2 installation
brew doctor
brew reinstall sdl2 sdl2_image sdl2_ttf

# Verify display permissions (macOS)
# System Settings > Privacy & Security > Screen Recording
```

### OPDS Server Not Connecting

```bash
# Check if backend is running
curl http://localhost:8080/healthz

# Check firewall settings
sudo pfctl -a me -s all  # List rules

# Verify IP address is correct
# Use actual IP, not localhost, from CrossVi settings
```

### Build Errors on Apple Silicon

```bash
# Install Rosetta if needed
softwareupdate --install-rosetta

# Or install Xcode command line tools
xcode-select --install
```

## Quick Reference

| Component | URL |
|-----------|-----|
| Backend Root | http://localhost:8080 |
| OPDS Catalog | http://localhost:8080/opds |
| OPDS Search | http://localhost:8080/opds/search?q=keyword |
| Health Check | http://localhost:8080/healthz |

## Next Steps

After setup, refer to:
- [docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md](./CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md) - Full device usage guide
- [scripts/opds_simulator.py](../scripts/opds_simulator.py) - Terminal-based OPDS testing
- [docs/crosvi-opds-spec.md](./crosvi-opds-spec.md) - CrossVi OPDS compatibility notes
