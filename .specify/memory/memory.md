# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3)  
**Nhánh tính năng**: `001-z-truyen-x3`  
**Ngày cập nhật**: 2026-08-18  
**Trạng thái hiện tại**: Đã hoàn thành toàn bộ Phase 0 (Research), Phase 1 (Spec, Plan, Data Model, Contracts, Quickstart) và Phase 2 Breakdown (`tasks.md` gồm 38 tasks). Sẵn sàng bắt đầu thực thi code với `/speckit-implement`.

---

## 1. Tóm Tắt Dự Án (Project Summary)

### 1.1. Mục Tiêu Cốt Lõi
Xây dựng một hệ thống Backend dịch vụ cào truyện tiếng Việt và cung cấp thư viện theo chuẩn giao thức **OPDS 1.2** phục vụ cho máy đọc sách E-ink **Xteink X3** (chạy firmware CrossVi 1.1.2 hoặc CrossPoint 1.5.0) và các thiết bị đọc khác sử dụng **KOReader** (Android, Kobo, PC).

### 1.2. Các Quyết Định Kỹ Thuật Đã Thống Nhất Qua Phỏng Vấn (/grill-me)
1. **Tuyệt đối không can thiệp Firmware X3 (0% brick risk)**: X3 sử dụng 100% ứng dụng **OPDS Browser có sẵn** trong CrossVi 1.1.2 để tìm kiếm, duyệt danh mục và tải sách trực tiếp vào thẻ nhớ SD.
2. **3 Nguồn truyện trọng điểm (Ported từ `Z-Truyenviet.koplugin`)**:
   - `storya.click`: Cào qua hệ thống REST API JSON tốc độ cao (`https://storya.click/api/v1`).
   - `akaytruyen.com`: Cào qua HTML Laravel + JSON chapter endpoint, hỗ trợ phiên đăng nhập cho chương VIP (`POST /login`).
   - `conduongbachu.com`: Cào qua WordPress REST API (`/wp-json/wp/v2/posts`) phân tách 4 danh mục: Chính Truyện (Cat 3) và 3 Ngoại Truyện (Cat 12, 14, 15).
3. **Kiến trúc Hybrid Scraper 2 Lớp**:
   - *Fast Path*: `httpx` (async) + `selectolax` (C-parser siêu nhanh) / JSON API cho các request thông thường.
   - *Headless Fallback Path*: `playwright` (Chromium Stealth) tự động kích hoạt khi gặp Cloudflare Turnstile / Challenge (HTTP 403/503).
4. **Chiến lược đóng gói EPUB kép (Dynamic Volume Bundling)**:
   - *Gom Tập/Quyển (Mặc định 50 chương/EPUB)*: Đọc liên tục mượt mà, dung lượng file <1MB, giảm tải số lượng file trên thẻ nhớ SD FAT32 và tiết kiệm bộ nhớ RAM (380KB) của ESP32-C3.
   - *Tải lẻ từng chương*: Phục vụ đọc các chương mới ra.
5. **Chuẩn hóa Document Identity cho KOSync**:
   - Tên file chuẩn: `ztruyen_{source_id}_{story_slug}_v{vol_index:02d}.epub`.
   - Cấu trúc XHTML sinh ra tất định (deterministic) với thẻ `<p id="p-N">` sạch, giúp mã băm SHA-1 và đồng bộ tiến trình đọc (KOSync) chính xác giữa X3 và KOReader trên Android.
6. **Vận hành Local-First trên Mac mini M4 + Cloudflare Tunnel**:
   - Backend đóng gói toàn diện bằng `docker compose` chạy ngầm 24/7 trên Mac mini M4 tại nhà.
   - Kết hợp `cloudflared` (Cloudflare Zero Trust) để cấp URL HTTPS an toàn, miễn phí, giúp X3 truy cập từ xa mọi lúc mọi nơi mà không cần mở port modem.

---

## 2. Bản Đồ Tài Liệu Dự Án (Project Documentation Map)

AI Agent phiên sau **BẮT BUỘC** phải tham chiếu các tài liệu sau theo thứ tự:

| STT | Tài liệu | Đường dẫn file | Nội dung tóm tắt |
|---|---|---|---|
| 1 | **Tasks Execution** | [`specs/001-z-truyen-x3/tasks.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/tasks.md) | **38 tasks cụ thể (T001 - T038)** phân chia theo 7 Phase và User Story để thực thi |
| 2 | **Implementation Plan** | [`specs/001-z-truyen-x3/plan.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/plan.md) | Kế hoạch kiến trúc tổng thể, cây thư mục code `backend/app/`, tech stack |
| 3 | **Feature Spec** | [`specs/001-z-truyen-x3/spec.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/spec.md) | 4 User Stories (US1: OPDS X3, US2: Scraper, US3: KOSync EPUB, US4: Docker), Requirements |
| 4 | **Data Model** | [`specs/001-z-truyen-x3/data-model.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/data-model.md) | Sơ đồ thực thể ERD, schema SQLite, cấu trúc `Source`, `Story`, `Chapter`, `VolumeBundle` |
| 5 | **API & Adapter Contracts** | [`specs/001-z-truyen-x3/contracts/`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/contracts/) | `opds-api.yaml` (OpenAPI 3.1) và `source-adapter-protocol.md` (Python Protocol) |
| 6 | **Research Decisions** | [`specs/001-z-truyen-x3/research.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/research.md) | Các quyết định công nghệ và lý do lựa chọn |
| 7 | **Validation Guide** | [`specs/001-z-truyen-x3/quickstart.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/quickstart.md) | Hướng dẫn chạy thử và 5 kịch bản kiểm thử End-to-End |
| 8 | **Mã nguồn mẫu Plugin gốc** | [`Z-Truyenviet.koplugin/`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/Z-Truyenviet.koplugin/) | Tham khảo logic bóc tách 3 nguồn tại `truyenviet/sources/storyaclick.lua`, `akaytruyen.lua`, `conduongbachu.lua` |

---

## 3. Hướng Dẫn Cụ Thể Cho AI Agent Phiên Sau (Next Agent Instructions)

### 3.1. Lệnh Khởi Động Thực Thi
Người dùng chỉ cần gõ lệnh:
```text
/speckit-implement
```
hoặc yêu cầu: *"Hãy bắt đầu thực hiện dự án theo kế hoạch và danh sách task đã lập trong `specs/001-z-truyen-x3/tasks.md`"*.

### 3.2. Quy Trình Thực Thi Từng Bước (Step-by-Step Execution Workflow)

Khi bắt đầu phiên làm việc mới, Agent thực hiện tuần tự theo quy trình sau:

1. **Bước 1 — Đọc Context**:
   - Đọc file [`memory.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/memory.md) (file này).
   - Đọc [`specs/001-z-truyen-x3/tasks.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/tasks.md).

2. **Bước 2 — Thực thi Phase 1: Setup (Shared Infrastructure)**:
   - `T001`: Khởi tạo cấu trúc thư mục `backend/app/`, `backend/tests/`.
   - `T002`: Tạo `backend/pyproject.toml` với đầy đủ dependencies.
   - `T003`: Tạo `backend/app/config.py`.
   - `T004`: Tạo `backend/app/logging.py`.

3. **Bước 3 — Thực thi Phase 2: Foundational (Blocking Prerequisites)**:
   - `T005`: Tạo Pydantic domain models tại `backend/app/domain/models.py`.
   - `T006`: Tạo ID generator tại `backend/app/domain/ids.py`.
   - `T007`: Tạo HTML sanitizer tại `backend/app/domain/sanitizer.py`.
   - `T008` & `T009` & `T010`: Triển khai SQLite database, Metadata repository và Object Storage disk cache.
   - `T011` & `T012`: Khởi tạo FastAPI app (`main.py`) và Healthcheck routes (`/healthz`, `/version`).

4. **Bước 4 — Thực thi Phase 3: User Story 2 (P1) - Hybrid Scraper Engine**:
   - `T013` - `T016`: Triển khai `SourceAdapter` protocol, async client `httpx`, Playwright fallback `headless.py`, và session manager.
   - `T017`: Triển khai `storyaclick.py` (JSON API).
   - `T018`: Triển khai `akaytruyen.py` (HTML + VIP login).
   - `T019`: Triển khai `conduongbachu.py` (WP REST API 4 categories).
   - `T020`: Triển khai `registry.py`.
   - `T021`: Viết integration tests và chạy `pytest backend/tests/integration/test_sources.py`.

5. **Bước 5 — Thực thi Phase 4: User Story 3 (P2) - Deterministic EPUB Builder**:
   - `T022` - `T024`: Triển khai XHTML template, `builder.py` (tất định, SHA-1) và `bundler.py` (gom 50 chương/volume).
   - `T025`: Viết unit tests và chạy `pytest backend/tests/unit/test_epub.py`.

6. **Bước 6 — Thực thi Phase 5: User Story 1 (P1 🎯 MVP) - OPDS Catalog Engine**:
   - `T026` - `T030`: Triển khai `opds_builder.py`, `opds.py` (Root/Hot/New/Genres), `search.py`, `books.py`, `chapters.py` (Download gateway).
   - `T031`: Viết integration test `test_opds.py` và kiểm tra toàn bộ luồng OPDS.  
   *(Tại đây đã đạt Mốc MVP, có thể kết nối X3 đọc thử ngay lập tức!)*

7. **Bước 7 — Thực thi Phase 6 & 7: Docker, Tunnel & Polish**:
   - `T032` - `T035`: Tạo `Dockerfile`, `docker-compose.yml` (kèm `cloudflared`), `.env.example`, `scripts/run-dev.sh`.
   - `T036` - `T038`: Chạy 5 kịch bản `quickstart.md`, kiểm tra EPUBCheck và cập nhật `README.md`.

---

## 4. Nguyên Tắc Làm Việc Của AI Agent (Agent Rules of Engagement)
- **Cập nhật tiến độ liên tục**: Sau khi hoàn thành mỗi task trong `tasks.md`, đánh dấu `[x]` vào checkbox tương ứng.
- **Không tự ý thay đổi kiến trúc cốt lõi**: Giữ nguyên tắc Local-First, Hybrid Scraper, Dynamic Volume Bundling (50 chương/EPUB) và tuyệt đối không can thiệp firmware X3.
- **Test-Driven & Verification**: Luôn chạy pytest và kiểm tra cú pháp code sau mỗi bước thay đổi.
