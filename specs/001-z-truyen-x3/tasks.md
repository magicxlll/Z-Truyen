# Tasks: Z-Truyen X3 Vietnamese Story Backend & OPDS Integration

**Feature**: `001-z-truyen-x3`  
**Input**: [specs/001-z-truyen-x3/plan.md](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/plan.md)  
**Spec**: [specs/001-z-truyen-x3/spec.md](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/spec.md)  

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Khởi tạo cấu trúc dự án Backend Python, cấu hình dependencies và môi trường chạy.

- [x] T001 Khởi tạo cấu trúc thư mục backend theo đúng kiến trúc plan tại `backend/app/`, `backend/tests/`
- [x] T002 Tạo file cấu hình `backend/pyproject.toml` khai báo Python 3.12+, FastAPI, Uvicorn, httpx, selectolax, playwright, ebooklib, pydantic, pillow, pytest
- [x] T003 [P] Cấu hình nạp biến môi trường và đường dẫn thư mục cache tại `backend/app/config.py`
- [x] T004 [P] Cấu hình hệ thống structured logging và error handlers tại `backend/app/logging.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Xây dựng hạ tầng dữ liệu, mô hình thực thể và lưu trữ SQLite/Disk cache bắt buộc trước khi triển khai các User Story.

**⚠️ CRITICAL**: Không bắt đầu triển khai các User Story cho đến khi hoàn thành xong Phase này.

- [x] T005 Tạo các Pydantic v2 domain models (`Source`, `Story`, `Chapter`, `VolumeBundle`, `SourceCredential`) tại `backend/app/domain/models.py`
- [x] T006 [P] Triển khai bộ sinh Document ID và quy tắc đặt tên file chuẩn hóa tại `backend/app/domain/ids.py`
- [x] T007 [P] Triển khai bộ chuẩn hóa và làm sạch XHTML tiếng Việt (`<p id="p-N">`) tại `backend/app/domain/sanitizer.py`
- [x] T008 [P] Triển khai kết nối SQLite (WAL mode) và khởi tạo bảng tại `backend/app/cache/database.py`
- [x] T009 [P] Triển khai Repository quản lý metadata truyện, chương và quyển tại `backend/app/cache/metadata_repo.py`
- [x] T010 [P] Triển khai Object Storage cache file EPUB và Covers trên ổ cứng tại `backend/app/cache/object_storage.py`
- [x] T011 Khởi tạo ứng dụng FastAPI với CORS và middleware tại `backend/app/main.py`
- [x] T012 Triển khai các API kiểm tra sức khỏe hệ thống `GET /healthz` và `GET /version` tại `backend/app/api/health.py`

**Checkpoint**: Nền tảng dữ liệu và server skeleton đã sẵn sàng.

---

## Phase 3: User Story 2 (P1) - Multi-Source Hybrid Scraper Engine

**Goal**: Cào dữ liệu truyện tin cậy từ 3 nguồn (`storya.click`, `akaytruyen.com`, `conduongbachu.com`) và tự động bypass Cloudflare Anti-bot.

**Independent Test**: Chạy `pytest backend/tests/integration/test_sources.py`, kiểm tra khả năng tìm kiếm, lấy mục lục và cào nội dung chương sạch từ cả 3 nguồn.

- [x] T013 [P] [US2] Định nghĩa interface protocol `SourceAdapter` tại `backend/app/sources/base.py`
- [x] T014 [P] [US2] Triển khai Async HTTP Client (`httpx`) kèm rate-limit và retry tại `backend/app/fetcher/client.py`
- [x] T015 [P] [US2] Triển khai Headless Playwright Stealth Fallback khi gặp Cloudflare Challenge tại `backend/app/fetcher/headless.py`
- [x] T016 [P] [US2] Triển khai Cookie & Credential Manager cho các nguồn yêu cầu đăng nhập tại `backend/app/fetcher/session.py`
- [x] T017 [US2] Triển khai Source Adapter cho `storya.click` (JSON REST API) tại `backend/app/sources/storyaclick.py`
- [x] T018 [US2] Triển khai Source Adapter cho `akaytruyen.com` (Laravel HTML + VIP Login) tại `backend/app/sources/akaytruyen.py`
- [x] T019 [US2] Triển khai Source Adapter cho `conduongbachu.com` (WordPress REST API 4 categories) tại `backend/app/sources/conduongbachu.py`
- [x] T020 [US2] Triển khai Source Registry điều phối các nguồn cào tại `backend/app/sources/registry.py`
- [x] T021 [P] [US2] Viết integration tests kiểm tra cào dữ liệu 3 nguồn với fixtures tại `backend/tests/integration/test_sources.py`

**Checkpoint**: Hệ thống cào dữ liệu 3 nguồn hoạt động ổn định và lưu cache metadata đầy đủ.

---

## Phase 4: User Story 3 (P2) - Deterministic EPUB Packaging & KOSync Compatibility

**Goal**: Đóng gói nội dung truyện thành file EPUB chuẩn nhẹ cho ESP32-C3, hỗ trợ gom tập 50 chương/EPUB và tương thích băm SHA-1 cho KOSync.

**Independent Test**: Build 1 file Volume EPUB (50 chương) từ dữ liệu mock, kiểm tra mở trên Calibre / KOReader, xác minh cấu trúc thẻ đoạn và mã băm SHA-1.

- [x] T022 [P] [US3] Thiết kế template XHTML và CSS siêu nhẹ (<2KB) tối ưu cho E-ink X3 tại `backend/app/epub/template.py`
- [x] T023 [US3] Triển khai Trình tạo EPUB tất định (Deterministic EPUB Builder) kèm tính toán SHA-1 tại `backend/app/epub/builder.py`
- [x] T024 [US3] Triển khai Engine gom tập `VolumeBundler` (tự động phân đoạn 50 chương/Volume hoặc tải lẻ) tại `backend/app/epub/bundler.py`
- [x] T025 [P] [US3] Viết unit tests kiểm tra tính hợp lệ và cấu trúc EPUB tại `backend/tests/unit/test_epub.py`

**Checkpoint**: Trình tạo EPUB gom quyển hoạt động mượt mà, file <1MB, mở tốt trên E-ink.

---

## Phase 5: User Story 1 (P1) 🎯 MVP - OPDS 1.2 Catalog Engine & Download Gateway for Xteink X3

**Goal**: Cung cấp giao thức OPDS 1.2 Atom Feed đầy đủ cho máy đọc sách Xteink X3 (CrossVi 1.1.2) duyệt danh mục, tìm kiếm và tải sách trực tiếp về thẻ nhớ SD.

**Independent Test**: Kết nối từ trình duyệt hoặc X3 tới `/opds`, tìm kiếm "Con Đường Bá Chủ", chọn tải Volume 1 và mở đọc ngay trên máy.

- [x] T026 [US1] Triển khai Trình tạo XML Atom Feed chuẩn OPDS 1.2 tại `backend/app/api/opds_builder.py`
- [x] T027 [US1] Triển khai các router OPDS Root, Hot, Mới cập nhật và Thể loại (`/opds`) tại `backend/app/api/opds.py`
- [x] T028 [US1] Triển khai router tìm kiếm OpenSearch (`/opds/search`) tại `backend/app/api/search.py`
- [x] T029 [US1] Triển khai router xem chi tiết truyện và danh sách Volume EPUB (`/opds/book/{source}/{slug}`) tại `backend/app/api/books.py`
- [x] T030 [US1] Triển khai router tải file EPUB về máy (`/opds/download/{source}/{slug}/{artifact}`) tại `backend/app/api/chapters.py`
- [x] T031 [P] [US1] Viết integration tests kiểm tra toàn bộ luồng OPDS catalog và tải file tại `backend/tests/integration/test_opds.py`

**Checkpoint**: Hoàn thành MVP cốt lõi! Xteink X3 kết nối và tải truyện đọc mượt mà qua OPDS có sẵn của CrossVi 1.1.2.

---

## Phase 6: User Story 4 (P2) - Local-First Docker Orchestration & Cloudflare Tunnel

**Goal**: Đóng gói toàn bộ hệ thống vào Docker Compose chạy ngầm 24/7 trên Mac mini M4 và thiết lập Cloudflare Tunnel truy cập từ xa qua HTTPS.

**Independent Test**: Chạy `docker compose up -d`, kiểm tra healthcheck và truy cập từ xa qua URL Cloudflare Tunnel.

- [x] T032 [US4] Tạo `backend/Dockerfile` tối ưu hóa đa tầng (multi-stage) cài sẵn Python 3.12 và Playwright Chromium headless
- [x] T033 [US4] Tạo `backend/docker-compose.yml` điều phối service Backend và Cloudflare Tunnel (`cloudflared`)
- [x] T034 [P] [US4] Tạo file mẫu cấu hình môi trường `backend/.env.example`
- [x] T035 [US4] Tạo scripts khởi chạy nhanh trên macOS/Linux (`scripts/run-dev.sh`) và Windows (`scripts/run-dev.ps1`)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Đánh giá kiểm thử toàn diện, tối ưu hóa hiệu năng và hoàn thiện tài liệu hướng dẫn.

- [x] T036 [P] Chạy toàn bộ 5 kịch bản kiểm thử End-to-End theo hướng dẫn `specs/001-z-truyen-x3/quickstart.md`
- [x] T037 [P] Kiểm tra độ hợp lệ của các file EPUB sinh ra bằng tiêu chuẩn EPUBCheck
- [x] T038 Cập nhật file `README.md` hướng dẫn chi tiết các bước thiết lập Backend trên Mac mini M4 và cấu hình OPDS trên máy Xteink X3

---

## Dependencies & Execution Order

### Phase Dependencies
1. **Setup (Phase 1)**: Bắt đầu ngay lập tức, không phụ thuộc.
2. **Foundational (Phase 2)**: Phụ thuộc vào Phase 1 (Chặn toàn bộ User Story).
3. **Scraper Engine (Phase 3 - US2)**: Cần hoàn thành để có nguồn dữ liệu truyện.
4. **EPUB Builder (Phase 4 - US3)**: Cần hoàn thành để đóng gói nội dung cào được thành sách.
5. **OPDS Engine (Phase 5 - US1 🎯 MVP)**: Tích hợp Scraper + EPUB Builder thành dịch vụ OPDS hoàn chỉnh cho X3.
6. **Docker & Tunnel (Phase 6 - US4)**: Đóng gói và phát hành máy chủ.
7. **Polish (Phase 7)**: Kiểm thử toàn diện và bàn giao.

---

## Parallel Opportunities

```bash
# Nhóm 1: Foundational Domain & Cache Models (chạy song song):
Task T006: ids.py
Task T007: sanitizer.py
Task T008: database.py
Task T009: metadata_repo.py
Task T010: object_storage.py

# Nhóm 2: Source Adapters (chạy song song):
Task T017: storyaclick.py
Task T018: akaytruyen.py
Task T019: conduongbachu.py

# Nhóm 3: EPUB & OPDS Tests (chạy song song):
Task T025: test_epub.py
Task T031: test_opds.py
```

---

## Implementation Strategy (MVP First)

1. **Bước 1**: Hoàn thành Phase 1 (Setup) + Phase 2 (Foundational).
2. **Bước 2**: Triển khai Phase 3 (Scraper Engine) và Phase 4 (EPUB Builder).
3. **Bước 3**: Triển khai Phase 5 (OPDS Engine) -> **ĐẠT MỐC MVP!** Thử nghiệm kết nối X3 thực tế.
4. **Bước 4**: Triển khai Phase 6 (Docker & Cloudflare Tunnel) để đưa vào sử dụng 24/7 trên Mac mini M4.
5. **Bước 5**: Chạy kiểm thử Phase 7 và hoàn tất bàn giao.
