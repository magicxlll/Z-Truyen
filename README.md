# Z-Truyen X3 — Vietnamese Story Backend & OPDS Integration

Hệ thống Backend dịch vụ cào truyện tiếng Việt và cung cấp thư viện theo chuẩn giao thức **OPDS 1.2** phục vụ cho máy đọc sách E-ink **Xteink X3** (chạy firmware CrossVi 1.1.2 hoặc CrossPoint 1.5.0) và các thiết bị đọc khác sử dụng **KOReader** (Android, Kobo, PC).

---

## 🌟 Điểm Nổi Bật

1. **0% Can Thiệp Firmware X3 (0% Brick Risk)**: Tận dụng ứng dụng **OPDS Browser có sẵn** trong CrossVi 1.1.2 để duyệt danh mục, tìm kiếm và tải sách trực tiếp vào thẻ nhớ SD.
2. **Hỗ Trợ 3 Nguồn Truyện Trọng Điểm**:
   - `storya.click`: REST API JSON v1 tốc độ cao.
   - `akaytruyen.com`: Laravel HTML + cơ chế đăng nhập tài khoản VIP.
   - `conduongbachu.com`: WordPress REST API với 4 danh mục (Chính Truyện & 3 Ngoại Truyện).
3. **Kiến Trúc Hybrid Scraper 2 Lớp**: Fast Async HTTP (`httpx` + `selectolax`) kết hợp Playwright Chromium Stealth Headless tự động kích hoạt khi gặp Cloudflare Turnstile / Bot Challenge.
4. **Đóng Gói Gom Quyển Tối Ưu (Dynamic Volume Bundling)**:
   - Tự động gom **50 chương/EPUB** (dung lượng < 1MB) giúp đọc liên tục, tiết kiệm RAM 380KB của ESP32-C3 và giảm tải số lượng file trên thẻ nhớ FAT32.
   - Hỗ trợ tải lẻ từng chương cho các chương mới ra.
5. **Chuẩn Hóa KOSync & SHA-1 Tất Định**:
   - Tên file chuẩn: `ztruyen_{source_id}_{story_slug}_v{vol_index:02d}.epub`.
   - Cấu trúc XHTML với các thẻ đoạn `<p id="p-N">` chuẩn hóa NFC tiếng Việt giúp đồng bộ tiến trình đọc (KOSync) chính xác giữa X3 và KOReader trên điện thoại / PC.
6. **Vận Hành Local-First + Cloudflare Tunnel**:
   - Chạy 24/7 bằng Docker Compose trên máy chủ gia đình (Mac mini M4, Linux, Windows WSL2).
   - Tích hợp `cloudflared` cấp HTTPS miễn phí, an toàn mà không cần mở port router.

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Khởi Chạy Nhanh Bằng Docker Compose (Khuyên dùng)

```bash
# 1. Đi vào thư mục backend
cd backend

# 2. Tạo file cấu hình môi trường từ mẫu
cp .env.example .env

# (Tùy chọn) Điền tài khoản VIP Akay hoặc Token Cloudflare Tunnel vào .env
# nano .env

# 3. Khởi chạy Backend qua Docker
docker compose up -d

# 4. Kiểm tra logs
docker compose logs -f
```

Server sẽ sẵn sàng phục vụ tại `http://localhost:8080` (hoặc IP mạng nội bộ `http://192.168.x.x:8080`).

---

### 2. Thiết Lập Môi Trường Ảo Tự Động & Test Giả Lập E-Reader

Xem hướng dẫn chi tiết tại: 👉 [docs/TESTING_VIRTUAL_ENV_GUIDE.md](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/TESTING_VIRTUAL_ENV_GUIDE.md)

#### Trên Windows (PowerShell):
```powershell
# Cài đặt tự động môi trường ảo
.\scripts\setup-windows.ps1

# Chạy trình giả lập E-Reader X3 qua Terminal
python scripts/opds_simulator.py
```

#### Trên macOS / Linux:
```bash
# Cài đặt tự động môi trường ảo
./scripts/setup-macos.sh

# Chạy trình giả lập E-Reader X3 qua Terminal
python3 scripts/opds_simulator.py
```

---

## 📱 Hướng Dẫn Cấu Hình Trên Máy Đọc Sách Xteink X3

1. **Kết Nối Wi-Fi**: Bật Wi-Fi trên máy X3 và kết nối vào cùng mạng Wi-Fi với máy chủ (hoặc mạng bất kỳ nếu dùng Cloudflare Tunnel).
2. **Mở OPDS Browser**: Trên màn hình chính của firmware CrossVi 1.1.2, chọn biểu tượng **OPDS Browser**.
3. **Thêm Máy Chủ Mới**:
   - **Tên**: `Z-Truyen`
   - **Địa chỉ (URL)**: `http://192.168.1.100:8080/opds`  
     *(Thay `192.168.1.100` bằng IP máy chạy Backend, hoặc URL HTTPS Cloudflare Tunnel `https://ztruyen.yourdomain.com/opds`)*
4. **Duyệt & Tải Truyện**:
   - Chọn mục **Truyện Hot**, **Mới Cập Nhật** hoặc nhập từ khóa vào ô **Tìm kiếm** (ví dụ: *Con Đường Bá Chủ*).
   - Chọn bộ truyện -> Chọn **Tập 01 (Chương 1-50)** -> Bấm **Tải về (Download)**.
   - Sách sẽ được tải trực tiếp vào thẻ nhớ SD và hiển thị ngay trên thư viện để mở đọc!

---

## 🧪 Kiểm Thử & Xác Nhận Chất Lượng

Chạy toàn bộ 22 unit test & integration test:

```bash
cd backend
pytest
```

---

## 📂 Cấu Trúc Mã Nguồn

```text
Z-Truyen/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application Entry & Router Registration
│   │   ├── config.py                # App Configuration & Path Resolvers
│   │   ├── logging.py               # Structured Logging & Scraper Events
│   │   ├── api/
│   │   │   ├── health.py            # /healthz & /version endpoints
│   │   │   ├── opds_builder.py      # OPDS 1.2 XML Atom Feed Generator
│   │   │   ├── opds.py              # Root, Hot, Latest & Sources feeds
│   │   │   ├── search.py            # OpenSearch Aggregator Endpoint
│   │   │   ├── books.py             # Story Details & Volume Catalog
│   │   │   └── chapters.py          # EPUB Binary Download Gateway
│   │   ├── domain/
│   │   │   ├── models.py            # Pydantic v2 Domain Models
│   │   │   ├── ids.py               # Document IDs & Slug / Filename Standardizer
│   │   │   └── sanitizer.py         # Vietnamese XHTML Normalizer (<p id="p-N">)
│   │   ├── sources/
│   │   │   ├── base.py              # SourceAdapter Protocol
│   │   │   ├── registry.py          # Source Registry & Multi-Source Dispatcher
│   │   │   ├── storyaclick.py       # Adapter cho storya.click (JSON API)
│   │   │   ├── akaytruyen.py        # Adapter cho akaytruyen.com (HTML + VIP)
│   │   │   └── conduongbachu.py     # Adapter cho conduongbachu.com (WP REST API)
│   │   ├── fetcher/
│   │   │   ├── client.py            # Async httpx Client with Rate Limiting & Retry
│   │   │   ├── headless.py          # Playwright Chromium Stealth Cloudflare Fallback
│   │   │   └── session.py           # Cookie & Credential Manager
│   │   ├── epub/
│   │   │   ├── template.py          # E-ink CSS & XHTML Templates
│   │   │   ├── builder.py           # Deterministic EPUB Packager (SHA-1)
│   │   │   └── bundler.py           # Dynamic Volume Bundler (50 ch/vol)
│   │   └── cache/
│   │       ├── database.py          # SQLite WAL Connection & Migrations
│   │       ├── metadata_repo.py     # Metadata Repository (Stories, Chaps, Volumes)
│   │       └── object_storage.py    # Local Disk Object Storage (EPUBs, Covers)
│   ├── tests/                       # Complete Pytest Test Suite
│   ├── Dockerfile                   # Multi-stage Docker Container
│   ├── docker-compose.yml           # Backend + Cloudflare Tunnel
│   └── pyproject.toml               # Python Build & Dependencies
├── specs/001-z-truyen-x3/           # Spec-Kit Engineering Artifacts
└── scripts/                         # Startup Scripts (macOS/Linux & Windows)
```

---

## 📜 Giấy Phép (License)

Dự án được phân phối dưới giấy phép MIT License.
