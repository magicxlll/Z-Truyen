# Z-Truyen X3 - Testing Guide

This guide provides comprehensive instructions for testing the Z-Truyen OPDS backend on a Mac mini with CrossVi simulator.

## Prerequisites

- Mac mini M4 (or any Mac with macOS 12+)
- Z-Truyen backend code (from `ztruyen_backend/`)
- CrossVi 1.1.2 Simulator or CrossPoint Reader Simulator
- Python 3.12+
- Git
- Homebrew (for macOS package management)

---

## Step 1: Setup Backend on Mac mini

### Option A: Native Python (Recommended for Development)

```bash
# Navigate to backend directory
cd ztruyen_backend

# Install dependencies
pip install -e ".[dev]"

# Get your Mac's IP address
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1)
echo "Your IP: $IP"

# Start backend server
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080
```

### Option B: Docker (Recommended for Production)

```bash
cd ztruyen_backend

# Build and start container
docker compose up -d

# Check container status
docker compose ps
```

### Option C: Run Script (If Available)

```bash
cd scripts
chmod +x run-dev.sh
./run-dev.sh
```

---

## Step 2: Verify Backend

Test the backend endpoints to ensure they are working correctly.

### Health Check

```bash
curl http://localhost:8080/healthz
```

**Expected Response:**
```json
{"status": "ok", "version": "0.1.0"}
```

### OPDS Root Catalog

```bash
curl http://localhost:8080/opds | head -50
```

**Expected Response:**
- XML with OPDS feed
- Contains `<feed>` root element
- Includes books from storya.click and ConDuongBaChu
- Has navigation links to search and categories

### OPDS Search

```bash
curl "http://localhost:8080/opds/search?q=bach" | head -30
```

**Expected Response:**
- XML with search results
- Contains matching books from sources

### Book Detail

```bash
curl "http://localhost:8080/opds/book/storya:con-duong-ba-chu" | head -50
```

**Expected Response:**
- XML with book metadata (title, author, summary)
- Contains chapter list
- Has acquisition links for downloading

---

## Step 3: Build CrossVi Simulator

### Clone Repository

```bash
# For CrossVi simulator
git clone https://github.com/tvhdc/crossvi.git
cd crossvi

# Or for CrossPoint Reader simulator
git clone https://github.com/crosspoint-reader/crosspoint-reader.git
git clone https://github.com/uxjulia/crosspoint-simulator.git
```

### Install System Dependencies

```bash
# Install SDL2 libraries
brew install sdl2 sdl2_image sdl2_ttf

# Verify Python version
python3 --version  # Should show 3.12+
```

### Install Python Dependencies

```bash
cd crossvi
pip install -r requirements.txt
```

### Build Simulator (Apple Silicon)

```bash
cd crosspoint-simulator
mkdir build && cd build
cmake .. -DCMAKE_OSX_ARCHITECTURES=arm64
make -j$(sysctl -n hw.ncpu)
```

### Run Simulator

```bash
# From build directory
./crossvi_simulator

# Or using the provided script
python3 scripts/run_simulator.py x3
```

---

## Step 4: Configure OPDS on CrossVi

1. **Open Settings** on the CrossVi simulator
2. **Navigate to**: Settings > OPDS Servers (or Wireless > OPDS Browser)
3. **Add Server**:
   - **Name**: `Z-Truyen Local`
   - **URL**: `http://<YOUR_MAC_IP>:8080/opds`
4. **Save** the configuration

### Finding Your Mac's IP Address

```bash
# For Wi-Fi
ipconfig getifaddr en0

# For Ethernet
ipconfig getifaddr en1

# Alternative method
ifconfig | grep "inet " | grep -v 127.0.0.1
```

---

## Step 5: Test Flow

Perform the following tests on the CrossVi simulator:

### Test 1: Browse Catalog

1. Open **OPDS Browser**
2. Select **Z-Truyen Local** server
3. Verify you see:
   - Hot/New stories feed
   - Genre categories
   - Source list

### Test 2: Search

1. From OPDS Browser, select **Search**
2. Enter a keyword (e.g., "bach", "vuong", "truyen")
3. Verify search results are returned

### Test 3: Book Detail

1. Tap on a book title
2. Verify book detail page shows:
   - Book title and author
   - Summary/description
   - List of chapters/volumes

### Test 4: Download EPUB

1. From book detail page, tap on a chapter volume
2. Verify download begins
3. Check that EPUB file is saved to virtual SD card

### Test 5: Read EPUB

1. Open **Library** or **Recent Books**
2. Select the downloaded book
3. Verify content renders correctly
4. Test page navigation

---

## OPDS Endpoint Reference

| Endpoint | URL | Description |
|----------|-----|-------------|
| Root Catalog | `http://IP:8080/opds` | Main OPDS feed with all books |
| Search | `http://IP:8080/opds/search?q=keyword` | Search for books |
| Book Detail | `http://IP:8080/opds/book/{source}:{id}` | Get book info and chapters |
| Download | `http://IP:8080/opds/download/{chapter_id}` | Download chapter as EPUB |
| Health Check | `http://IP:8080/opds/healthz` | Server health status |

### Book ID Formats

| Source | Format | Example |
|--------|--------|---------|
| Storya | `storya:{book_slug}` | `storya:con-duong-ba-chu` |
| ConDuongBaChu | `conduongbachu:{story_id}` | `conduongbachu:12345` |

### Chapter ID Formats

| Source | Format | Example |
|--------|--------|---------|
| Storya | `storya:{book_slug}:{chapter_slug}` | `storya:con-duong-ba-chu:chuong-1` |
| ConDuongBaChu | `conduongbachu:{story_id}:{chapter_num}` | `conduongbachu:12345:1` |

---

## Troubleshooting

### Backend Won't Start

```bash
# Check if port 8080 is already in use
lsof -i :8080

# Try a different port
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8081
```

### OPDS Server Not Connecting from Simulator

```bash
# Verify backend is running
curl http://localhost:8080/healthz

# Check firewall settings
sudo pfctl -a me -s all

# Ensure IP address is correct (use actual IP, not localhost)
```

### CrossVi Simulator Won't Start

```bash
# Check SDL2 installation
brew doctor
brew reinstall sdl2 sdl2_image sdl2_ttf

# Verify display permissions (macOS)
# System Settings > Privacy & Security > Screen Recording
```

### EPUB Download Fails

```bash
# Test download endpoint directly
curl -v http://localhost:8080/opds/download/storya:con-duong-ba-chu:chuong-1

# Check backend logs for errors
```

### Empty Search Results

- Ensure search query has at least 2 characters
- Note: ConDuongBaChu source does not support search
- Try searching for common terms like "bach", "vuong"

### Books Not Showing

- Backend may be falling back to mock data
- Check network connectivity to storya.click and ConDuongBaChu.com
- Review backend logs for API errors

### Build Errors on Apple Silicon

```bash
# Install Rosetta if needed
softwareupdate --install-rosetta

# Or install Xcode command line tools
xcode-select --install
```

---

## Quick Test Checklist

Run through this checklist to verify everything works:

- [ ] Backend starts without errors
- [ ] `/healthz` returns `{"status": "ok"}`
- [ ] `/opds` returns valid OPDS XML with books
- [ ] `/opds/search?q=bach` returns search results
- [ ] `/opds/book/storya:con-duong-ba-chu` shows book detail
- [ ] CrossVi simulator launches successfully
- [ ] OPDS server connects to backend
- [ ] Can browse catalog in CrossVi
- [ ] Can search for books in CrossVi
- [ ] Can download chapter as EPUB
- [ ] Can open and read downloaded EPUB

---

## Additional Resources

- [CrossVi OPDS Specification](./crosvi-opds-spec.md) - Detailed OPDS compatibility notes
- [Simulator Setup Guide](./simulator-setup.md) - CrossVi setup instructions
- [CrossPoint X3 Virtual Device Guide](./CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md) - Full device usage guide
- [Z-Truyen Backend README](../ztruyen_backend/README.md) - Backend documentation

---

## Support

If you encounter issues not covered here:

1. Check the backend logs for error messages
2. Verify all prerequisites are installed
3. Try running the backend in debug mode:

```bash
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 --log-level debug
```
