# Implementation Plan: Z-Truyen X3 Vietnamese Story Backend & OPDS Integration

**Branch**: `001-z-truyen-x3` | **Date**: 2026-08-18 | **Spec**: [specs/001-z-truyen-x3/spec.md](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/spec.md)

---

## Summary

Dự án **Z-Truyen X3** xây dựng một hệ thống Backend dịch vụ cào truyện và cung cấp catalog chuẩn **OPDS 1.2** cho máy đọc sách **Xteink X3** (chạy firmware CrossVi 1.1.2 / CrossPoint 1.5.0) và các thiết bị **KOReader**.
- Hỗ trợ 3 nguồn truyện mục tiêu: `storya.click` (JSON REST API), `akaytruyen.com` (Laravel HTML + VIP auth), `conduongbachu.com` (WordPress REST API).
- Sử dụng kiến trúc **Hybrid Scraper** (Fast Async HTTP + Headless Playwright Fallback cho Cloudflare Challenge).
- Cơ chế đóng gói kép: **Volume Bundling (50 chương/EPUB)** giúp đọc liền mạch, giảm tải thẻ nhớ SD cho ESP32-C3 và **Single Chapter EPUB**.
- Định dạng EPUB mang tính tất định (Deterministic & Byte-exact) phục vụ đồng bộ tiến trình đọc **KOSync**.
- Vận hành theo mô hình **Local-First** trên Mac mini M4 gia đình (hoặc Docker bất kỳ) kết hợp **Cloudflare Tunnel** cho truy cập từ xa an toàn qua HTTPS.
- Tuyệt đối **không sửa đổi firmware X3** ở giai đoạn MVP.

---

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: FastAPI, Uvicorn, httpx, selectolax, playwright, ebooklib, Pydantic v2, Pillow  
**Storage**: SQLite (WAL Mode) cho metadata và Local File Storage cho EPUB cache / Covers  
**Testing**: pytest, pytest-asyncio, Playwright test suite, EPUBCheck validation  
**Target Platform**: Docker (Linux/macOS ARM64 Apple Silicon M4 / Windows WSL2)  
**Project Type**: Web Service / API Gateway & OPDS Feed Provider  
**Performance Goals**: OPDS feed < 100ms (cache hit), Fast scrape < 500ms, Volume EPUB generation < 3s, X3 download < 5s  
**Constraints**: RAM ESP32-C3 khả dụng ~380KB (file EPUB gom quyển < 1.5MB), 0% can thiệp firmware X3  
**Scale/Scope**: Hỗ trợ 3 nguồn khởi đầu, hàng nghìn bộ truyện, tự động phân phối qua OPDS cho X3/KOReader  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Zero Firmware Modification**: Không yêu cầu nạp flash firmware tùy biến trên X3; sử dụng 100% OPDS Browser có sẵn của CrossVi 1.1.2. (PASS)
- [x] **Lightweight on Device**: Phân tách toàn bộ tác vụ nặng (Scraping, DOM parsing, EPUB building, Cloudflare bypass) về Backend; X3 chỉ nhận file EPUB thành phẩm. (PASS)
- [x] **Deterministic EPUB for KOSync**: Chuẩn hóa tên file `ztruyen_{source}_{book}_v{vol}.epub` và cấu trúc thẻ `<p id="p-X">` để đảm bảo định danh tài liệu đồng nhất. (PASS)
- [x] **Self-Contained & Local-First**: Đóng gói hoàn chỉnh trong Docker Compose, tự động lưu trữ metadata và file cache cục bộ trên Mac mini M4. (PASS)

---

## Project Structure

### Documentation (this feature)

```text
specs/001-z-truyen-x3/
├── spec.md              # Feature specification (User Stories, Requirements, SCs)
├── plan.md              # Implementation plan (This file)
├── research.md          # Phase 0 output (Technical decisions & justifications)
├── data-model.md        # Phase 1 output (Entity models, ER diagram, state transitions)
├── quickstart.md        # Phase 1 output (Installation & validation guide)
├── contracts/           # Phase 1 output (OpenAPI spec & Python Protocol)
│   ├── opds-api.yaml
│   └── source-adapter-protocol.md
└── tasks.md             # Phase 2 output (sẽ tạo ở bước /speckit-tasks)
```

### Source Code (repository root)

```text
Z-Truyen/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application Entry
│   │   ├── config.py                # Cấu hình môi trường & đường dẫn cache
│   │   ├── api/
│   │   │   ├── opds.py              # OPDS 1.2 Feed Generator & Routes
│   │   │   ├── books.py             # Book detail API
│   │   │   ├── chapters.py          # Chapter reading & download routes
│   │   │   ├── search.py            # Search aggregator endpoint
│   │   │   └── health.py            # Healthz & Version endpoints
│   │   ├── domain/
│   │   │   ├── models.py            # Pydantic v2 domain models
│   │   │   ├── ids.py               # Document & File ID standardizer
│   │   │   └── sanitizer.py         # Clean HTML & XHTML normalizer
│   │   ├── sources/
│   │   │   ├── base.py              # SourceAdapter Protocol definition
│   │   │   ├── registry.py          # Adapter Registry & Dispatcher
│   │   │   ├── storyaclick.py       # Adapter cho storya.click (JSON API)
│   │   │   ├── akaytruyen.py        # Adapter cho akaytruyen.com (HTML + VIP)
│   │   │   └── conduongbachu.py     # Adapter cho conduongbachu.com (WP REST API)
│   │   ├── fetcher/
│   │   │   ├── client.py            # Async httpx client with rate limit
│   │   │   ├── headless.py          # Playwright Stealth Cloudflare Fallback
│   │   │   └── session.py           # Cookie & credential manager
│   │   ├── epub/
│   │   │   ├── builder.py           # Deterministic EPUB packager
│   │   │   ├── bundler.py           # Volume Bundling engine (50 ch/vol)
│   │   │   └── template.py          # XHTML & CSS templates
│   │   └── cache/
│   │       ├── database.py          # SQLite connection & schema migrations
│   │       ├── metadata_repo.py     # Story/Chapter/Volume metadata repo
│   │       └── object_storage.py    # Local disk EPUB/Cover cache manager
│   ├── tests/
│   │   ├── unit/                    # Unit tests for domain, sanitizer, epub
│   │   ├── integration/             # Integration tests for OPDS and scrapers
│   │   └── fixtures/                # Mock HTML & JSON data for sources
│   ├── pyproject.toml               # Python project configuration & dependencies
│   ├── Dockerfile                   # Container build for Backend + Playwright
│   └── docker-compose.yml           # Backend + Cloudflare Tunnel orchestration
```

**Structure Decision**: Lựa chọn cấu trúc Web Service Backend độc lập đặt trong thư mục `backend/` nhằm đảm bảo tính module hóa cao, dễ dàng đóng gói Docker và tách rời hoàn toàn với thư viện tham chiếu gốc.

---

## Detailed Execution Phases

### Phase 0: Research & Foundation (Done)
- Khảo sát mã nguồn gốc `Z-Truyenviet.koplugin` và trích xuất chi tiết kỹ thuật 3 nguồn `storya.click`, `akaytruyen.com`, `conduongbachu.com`.
- Thống nhất các quyết định kiến trúc: FastAPI, Hybrid Scraper, Dynamic Volume Bundling (50 chương/EPUB), Local-First Docker + Cloudflare Tunnel.
- Tạo artifact: [`research.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/research.md).

### Phase 1: Data Model, Contracts & Quickstart (Done)
- Xây dựng mô hình dữ liệu chi tiết cho `Source`, `Story`, `Chapter`, `VolumeBundle`, `SourceCredential`, `CacheEntry`.
- Định nghĩa OpenAPI 3.1 contract (`opds-api.yaml`) và Python `SourceAdapter` Protocol (`source-adapter-protocol.md`).
- Xây dựng hướng dẫn khởi chạy và kịch bản kiểm thử mẫu (`quickstart.md`).
- Tạo artifacts: [`data-model.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/data-model.md), [`contracts/`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/contracts/), [`quickstart.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/quickstart.md).

### Phase 2: Backend Core Skeleton & Database Setup
- Cấu hình `pyproject.toml`, Dockerfile, `docker-compose.yml`.
- Thiết lập kết nối SQLite (WAL mode), khởi tạo schema bảng metadata (`stories`, `chapters`, `volumes`, `credentials`, `cache_entries`).
- Xây dựng các endpoint cơ bản: `GET /healthz`, `GET /version`.

### Phase 3: Hybrid Scraper Engine & 3 Source Adapters
- Triển khai `fetcher/client.py` và `fetcher/headless.py` (Playwright stealth).
- Triển khai Adapter 1: `storyaclick.py` (JSON API).
- Triển khai Adapter 2: `akaytruyen.py` (Laravel HTML + VIP login).
- Triển khai Adapter 3: `conduongbachu.py` (WordPress REST API với 4 category).
- Viết unit tests & integration tests với dữ liệu fixture đã lưu.

### Phase 4: Deterministic EPUB Builder & Volume Bundler
- Xây dựng trình tạo EPUB chuẩn UTF-8, CSS nhẹ, tối ưu RAM cho ESP32-C3.
- Xây dựng thuật toán gom tập `VolumeBundler` (tự động phân đoạn 50 chương/EPUB, đặt tên chuẩn `ztruyen_{source}_{slug}_v{vol}.epub`).
- Tích hợp kiểm thử tính hợp lệ EPUB và kiểm tra băm SHA-1 cho KOSync.

### Phase 5: OPDS 1.2 Catalog Engine & Download Gateway
- Xây dựng `api/opds.py` xuất XML Atom Feed chuẩn OPDS 1.2:
  - Danh mục Root, Hot, Mới nhất, Thể loại.
  - Tìm kiếm OpenSearch.
  - Trang chi tiết truyện kèm danh sách các Volume EPUB để tải.
  - Endpoint tải trực tiếp file EPUB với cache-first policy.

### Phase 6: End-to-End Validation & Docker Orchestration
- Tích hợp Cloudflare Tunnel trong `docker-compose.yml`.
- Thực hiện kiểm thử toàn diện trên CrossVi Simulator / KOReader và kết nối thực tế từ máy đọc sách Xteink X3.

---

## Complexity Tracking

| Thành phần / Quyết định | Lý do cần thiết | Giải pháp đơn giản hơn bị từ chối vì |
|---|---|---|
| **Hybrid Scraper (Playwright Fallback)** | Vượt qua Cloudflare Challenge và mã hóa JavaScript trên các web truyện Việt Nam | Dùng `httpx` thuần túy sẽ bị chặn ngay lập tức bởi mã lỗi 403 Forbidden. |
| **Volume Bundling (50 chương/EPUB)** | Tối ưu hóa dung lượng thẻ nhớ SD và RAM 380KB của ESP32-C3, mang lại trải nghiệm đọc liên tục | Tải từng chương lẻ gây ức chế khi đọc; tải toàn bộ 3000 chương vào 1 file làm tràn RAM máy X3. |
| **Cloudflare Tunnel** | Cung cấp HTTPS an toàn cho X3 kết nối từ xa mọi lúc mọi nơi | Mở cổng router (Port forwarding) tiềm ẩn rủi ro an ninh mạng gia đình. |
