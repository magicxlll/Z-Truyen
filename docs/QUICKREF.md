# Z-Truyen Quick Reference

Quick reference guide for testing Z-Truyen OPDS backend on Mac mini with CrossVi simulator.

---

## Server Commands

### Start Backend

```bash
# Native Python (port 8080)
cd ztruyen_backend
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080

# Docker
cd ztruyen_backend
docker compose up -d
```

### Test Backend

```bash
# Health check
curl http://localhost:8080/healthz
# Expected: {"status": "ok", "version": "0.1.0"}

# OPDS catalog
curl http://localhost:8080/opds | head -30
```

### Stop Backend

```bash
# Ctrl+C (for native Python)

# Docker
docker compose down
```

### Get Mac IP

```bash
ipconfig getifaddr en0   # Wi-Fi
ipconfig getifaddr en1   # Ethernet
```

---

## OPDS Endpoints

| Endpoint | URL | Description |
|----------|-----|-------------|
| **Catalog** | `http://IP:8080/opds` | Main OPDS feed |
| **Search** | `http://IP:8080/opds/search?q=keyword` | Search books |
| **Book Detail** | `http://IP:8080/opds/book/{source}:{id}` | Get book info |
| **Download** | `http://IP:8080/opds/download/{chapter_id}` | Get EPUB file |
| **Health** | `http://IP:8080/opds/healthz` | Server status |

---

## Book ID Patterns

| Source | Book ID Format | Example |
|--------|----------------|---------|
| Storya | `storya:{slug}` | `storya:con-duong-ba-chu` |
| ConDuongBaChu | `conduongbachu:{id}` | `conduongbachu:12345` |

## Chapter ID Patterns

| Source | Chapter ID Format | Example |
|--------|-------------------|---------|
| Storya | `storya:{book}:{chapter}` | `storya:con-duong-ba-chu:chuong-1` |
| ConDuongBaChu | `conduongbachu:{id}:{num}` | `conduongbachu:12345:1` |

---

## CrossVi Simulator

### Run Simulator

```bash
cd crossvi
python3 scripts/run_simulator.py x3

# Or from build directory
./crossvi_simulator
```

### Configure OPDS

1. Settings > OPDS Servers
2. Add Server:
   - Name: `Z-Truyen Local`
   - URL: `http://<MAC_IP>:8080/opds`
3. Save

---

## Expected Test Results

### Backend Health

- [ ] `/healthz` returns `{"status": "ok"}`

### OPDS Catalog

- [ ] `/opds` returns valid XML with `<feed>` root
- [ ] Feed contains books from storya & conduongbachu
- [ ] Feed has navigation links

### Search

- [ ] `/opds/search?q=bach` returns results
- [ ] Empty search returns empty catalog (not error)

### Book Detail

- [ ] `/opds/book/storya:con-duong-ba-chu` shows book
- [ ] Response has chapter list
- [ ] Response has acquisition links

### EPUB Download

- [ ] `/opds/download/storya:con-duong-ba-chu:chuong-1` returns EPUB
- [ ] Response type is `application/epub+zip`
- [ ] File downloads correctly

### CrossVi Integration

- [ ] Simulator connects to OPDS server
- [ ] Can browse catalog in simulator
- [ ] Can search in simulator
- [ ] Can download EPUB in simulator
- [ ] Can read downloaded EPUB

---

## Common Issues

| Problem | Solution |
|---------|----------|
| Port 8080 in use | Use `--port 8081` or `lsof -i :8080` to find process |
| Can't connect from simulator | Use actual IP, not `localhost` |
| Empty search results | Query must be 2+ characters |
| Books not loading | Check logs for API errors, may be using mock data |
| Simulator won't start | Reinstall SDL2: `brew reinstall sdl2 sdl2_image sdl2_ttf` |

---

## File Locations

| File | Path |
|------|------|
| Backend | `ztruyen_backend/` |
| Backend main | `ztruyen_backend/main.py` |
| OPDS renderer | `ztruyen_backend/opds_renderer.py` |
| EPUB builder | `ztruyen_backend/epub_builder.py` |
| Sources | `ztruyen_backend/sources/` |
| CrossVi | `crossvi/` |
| Virtual SD card | `~/crosspoint-reader/sdcard/` |

---

## Quick Debug

```bash
# Run with debug logging
uvicorn ztruyen_backend.main:app --host 0.0.0.0 --port 8080 --log-level debug

# Check container logs
docker compose logs -f

# Test with verbose curl
curl -v http://localhost:8080/healthz
```
