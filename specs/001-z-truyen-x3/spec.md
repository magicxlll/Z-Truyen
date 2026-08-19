# Feature Specification: Z-Truyen X3 Vietnamese Story Backend & OPDS Integration

**Feature Branch**: `001-z-truyen-x3`  
**Created**: 2026-08-18  
**Status**: Draft  
**Input**: Phỏng vấn phản biện kiến trúc Z-Truyen X3 và chi tiết cào dữ liệu từ `Z-Truyenviet.koplugin` cho 3 nguồn `storya.click`, `akaytruyen.com`, `conduongbachu.com`.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Khám phá & Đọc truyện liền mạch qua OPDS trên Xteink X3 (Priority: P1)

Người dùng sở hữu máy đọc sách E-ink Xteink X3 (chạy firmware CrossVi 1.1.2 hoặc CrossPoint 1.5.0). Người dùng kết nối Wi-Fi, mở tính năng OPDS Browser có sẵn trên máy, truy cập vào thư viện Z-Truyen, tìm kiếm truyện tiếng Việt từ các nguồn hỗ trợ (`storya.click`, `akaytruyen.com`, `conduongbachu.com`), duyệt mục lục chương và tải gói EPUB về thẻ nhớ SD để đọc offline liên tục mà không bị gián đoạn.

**Why this priority**: Đây là luồng giá trị cốt lõi (Core Value Stream) của toàn bộ dự án. Giúp người dùng biến X3 thành máy đọc truyện online/offline mượt mà mà không cần chỉnh sửa/nạp lại firmware.

**Independent Test**: Khởi động Backend Z-Truyen, dùng máy X3 (hoặc CrossVi Simulator / Calibre / KOReader) kết nối tới `/opds`, tìm kiếm "Con Đường Bá Chủ", chọn tải Volume 1 (Chương 1-50) dạng EPUB và mở đọc ngay trên máy.

**Acceptance Scenarios**:
1. **Given** X3 kết nối URL OPDS của Z-Truyen, **When** người dùng tìm kiếm từ khóa hoặc duyệt danh mục Hot/Mới, **Then** hệ thống trả về danh sách truyện kèm ảnh bìa, tác giả và tóm tắt trong thời gian < 1s (từ cache) hoặc < 5s (khi cào mới).
2. **Given** người dùng chọn 1 bộ truyện cụ thể, **When** bấm vào để xem mục lục, **Then** hệ thống cung cấp 2 tùy chọn tải: "Tải theo Tập/Quyển (Bundled Volume: 50 chương/EPUB)" và "Tải lẻ từng chương".
3. **Given** người dùng chọn tải 1 Volume EPUB, **When** tải xong về thẻ SD, **Then** trình đọc tích hợp của CrossVi mở file mượt mà, hỗ trợ lật trang liên tục qua 50 chương, format chuẩn UTF-8 tiếng Việt, không lỗi font hay layout.
4. **Given** máy X3 ngắt Wi-Fi sau khi tải, **When** người dùng mở lại thư viện nội bộ trên thẻ SD, **Then** toàn bộ các file EPUB đã tải vẫn đọc được offline 100%.

---

### User Story 2 - Thu thập dữ liệu đa nguồn tin cậy & Bypass Anti-bot (Priority: P1)

Hệ thống Backend tự động điều phối các Source Adapter chuyên biệt để cào truyện từ 3 nguồn:
1. `storya.click`: Cào qua REST API JSON tốc độ cao.
2. `akaytruyen.com`: Cào qua HTML + JSON chapter endpoint, hỗ trợ phiên đăng nhập cho chương VIP.
3. `conduongbachu.com`: Cào qua WordPress REST API (`wp-json`) bóc tách Chính truyện (Cat 3) và Ngoại truyện (Cat 12, 14, 15).
Đồng thời, hệ thống trang bị cơ chế Hybrid Scraper (Fast Path HTTP + Headless Playwright Fallback) để tự động vượt Cloudflare Turnstile / Challenge khi gặp mã lỗi 403/503.

**Why this priority**: Nếu không cào được dữ liệu do Cloudflare hoặc sai định dạng DOM thì hệ thống không thể cung cấp truyện cho người đọc.

**Independent Test**: Gửi request cào chương truyện từ cả 3 nguồn độc lập qua bộ test tự động (pytest), xác minh nội dung trả về là văn bản tiếng Việt sạch, có đầy đủ cấu trúc đoạn `<p>`, không dính quảng cáo hay text rác.

**Acceptance Scenarios**:
1. **Given** request lấy truyện từ `storya.click`, **When** gọi `GET /chapters/{story}/{chap}`, **Then** backend parse JSON trả về nội dung chương sạch.
2. **Given** request lấy mục lục `conduongbachu.com`, **When** gọi API WordPress, **Then** backend lấy đủ danh sách toàn bộ các chương theo thứ tự tăng dần.
3. **Given** trang web nguồn kích hoạt Cloudflare Challenge, **When** Fast HTTP request nhận 403, **Then** hệ thống tự động chuyển sang Playwright Stealth headless browser để giải mã và lấy nội dung mà không gây gián đoạn request của người dùng.

---

### User Story 3 - Đồng bộ Tiến trình Đọc Chuẩn xác với KOReader (KOSync) (Priority: P2)

Người dùng đọc truyện trên Xteink X3 ở nhà, sau đó ra ngoài mở KOReader trên điện thoại Android / máy tính bảng / Kobo để đọc tiếp. Nhờ quy tắc sinh file EPUB byte-exact và Document ID chuẩn hóa, hệ thống KOSync tự động nhận diện đúng vị trí đoạn văn / chương đang đọc dở.

**Why this priority**: Đảm bảo trải nghiệm đọc liền mạch đa thiết bị cho cộng đồng dùng KOReader và máy đọc sách mini.

**Independent Test**: Tải cùng 1 Volume EPUB trên X3 và trên KOReader Android, đọc đến chương 5 đoạn 3 trên X3 -> kích hoạt KOSync -> mở KOReader Android và xác minh vị trí đọc tự động nhảy đến đúng đoạn 3 chương 5.

**Acceptance Scenarios**:
1. **Given** file EPUB được tạo từ Z-Truyen Backend, **When** kiểm tra tên file, **Then** tên file tuân thủ quy chuẩn `ztruyen_{source_id}_{book_id}_v{vol_index}.epub`.
2. **Given** hai thiết bị khác nhau tải cùng 1 volume, **When** tính checksum SHA-1 và phân tích cấu trúc DOM XHTML, **Then** cấu trúc các thẻ `<p id="...">` là 100% deterministic (không chứa timestamp ngẫu nhiên).

---

### User Story 4 - Vận hành Local-First trên Mac mini M4 & Truy cập từ xa qua Cloudflare Tunnel (Priority: P2)

Người dùng cài đặt Z-Truyen Backend trên máy Mac mini M4 gia đình thông qua Docker Compose. Backend tự động chạy ngầm 24/7, lưu cache metadata vào SQLite và file EPUB/ảnh bìa vào ổ cứng cục bộ. Người dùng cấu hình Cloudflare Tunnel (miễn phí) để cấp tên miền HTTPS an toàn, cho phép X3 kết nối từ mọi nơi mà không cần mở port modem.

**Why this priority**: Tận dụng tối đa phần cứng sẵn có, tiết kiệm 100% chi phí máy chủ đám mây và bảo vệ an toàn mạng gia đình.

**Independent Test**: Chạy `docker compose up -d`, kiểm tra healthcheck `http://localhost:8080/healthz`, sau đó truy cập qua URL Cloudflare Tunnel từ mạng 4G/di động và xác nhận OPDS hoạt động bình thường.

**Acceptance Scenarios**:
1. **Given** môi trường Docker Desktop trên macOS / Linux / Windows, **When** chạy `docker compose up -d`, **Then** toàn bộ Backend + SQLite + Cache Storage khởi động thành công trong < 10 giây.
2. **Given** URL Cloudflare Tunnel `https://ztruyen.yourdomain.com/opds`, **When** thiết bị X3 kết nối qua Wi-Fi ngoài quán cafe, **Then** X3 tải truyện mượt mà qua kết nối HTTPS bảo mật.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống Backend MUST cung cấp chuẩn giao thức **OPDS 1.2 Catalog** (XML/Atom Feed) tương thích 100% với trình duyệt OPDS của CrossVi 1.1.2 và CrossPoint 1.5.0.
- **FR-002**: Hệ thống MUST hỗ trợ tìm kiếm truyện theo từ khóa (`/opds/search?q={query}`), duyệt truyện theo danh mục Hot, Mới cập nhật và Thể loại.
- **FR-003**: Hệ thống MUST hỗ trợ 3 Source Adapter khởi đầu: `storyaclick`, `akaytruyen`, `conduongbachu`.
- **FR-004**: Hệ thống MUST hỗ trợ cơ chế bóc tách 2 lớp (Hybrid Scraper): Lớp Fast HTTP (httpx + selectolax) và Lớp Headless Fallback (Playwright) khi gặp Cloudflare Challenge.
- **FR-005**: Hệ thống MUST cung cấp 2 chế độ đóng gói EPUB:
  - **Volume Bundling**: Gom 50 chương vào 1 file EPUB (ví dụ: `ztruyen_conduongbachu_main_v01.epub`).
  - **Single Chapter**: Tạo file EPUB riêng lẻ cho từng chương.
- **FR-006**: Trình tạo EPUB (EPUB Builder) MUST sinh cấu trúc XHTML sạch chuẩn UTF-8, CSS gọn nhẹ, không chứa JavaScript, không chèn tài nguyên ngoài, và cấu trúc thẻ đoạn `<p>` mang tính tất định (deterministic) để tối ưu cho thuật toán XPath KOSync.
- **FR-007**: Hệ thống MUST lưu cache Metadata (SQLite) và Object Storage (File cục bộ / R2) cho các chương đã cào và file EPUB đã build, tránh cào lại nhiều lần gây tải cho web nguồn.
- **FR-008**: Hệ thống MUST hỗ trợ cơ chế xác thực tài khoản (Login / Session Cookies) đối với các nguồn có chương VIP như `akaytruyen.com`.
- **FR-009**: Hệ thống MUST cung cấp API Healthcheck (`GET /healthz`) và Version (`GET /version`).
- **FR-010**: Toàn bộ giải pháp MVP MUST hoạt động trên Xteink X3 mà **KHÔNG ĐƯỢC PHÉP can thiệp hay nạp lại firmware (No firmware modification)**.

---

### Key Entities

- **Source**: Đại diện cho 1 website nguồn truyện (ID, Tên, Base URL, Loại bóc tách API/HTML, Trạng thái VIP login).
- **Book (Story)**: Đại diện cho 1 bộ truyện (ID chuẩn hóa `source_id:book_slug`, Tiêu đề, Tác giả, Ảnh bìa, Tóm tắt, Trạng thái, Thể loại).
- **Chapter**: Đại diện cho 1 chương truyện (ID chuẩn hóa, Số thứ tự/Order, Tiêu đề chương, URL gốc, Nội dung HTML sạch).
- **VolumeBundle**: Đại diện cho 1 tập/quyển gồm nhiều chương (Index quyển, Từ chương X đến chương Y, Tên file EPUB, Checksum SHA-1, Dung lượng bytes).
- **OPDSFeed**: Cấu trúc XML Atom Feed cung cấp cho thiết bị X3 (Danh mục, Search link, Acquisition link tải EPUB, Thumbnail link).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Thiết bị Xteink X3 kết nối và duyệt danh mục OPDS thành công, mở xem mục lục truyện trong thời gian < 1 giây đối với dữ liệu đã cache.
- **SC-002**: Tải và mở thành công 1 file EPUB Volume 50 chương trên X3 qua kết nối Wi-Fi trong thời gian < 5 giây (khi file đã được build sẵn trên Backend cache).
- **SC-003**: Trình cào dữ liệu hoạt động ổn định với tỷ lệ thành công > 98% trên cả 3 nguồn `storya.click`, `akaytruyen.com`, `conduongbachu.com`.
- **SC-004**: File EPUB sinh ra vượt qua 100% các công cụ kiểm tra tính hợp lệ EPUB (EPUBCheck standard).
- **SC-005**: 100% không phát sinh lỗi tràn bộ nhớ (Heap Out of Memory) hay đơ máy trên ESP32-C3 X3 khi đọc các Volume EPUB do Z-Truyen tạo ra.
- **SC-006**: Triển khai trọn gói Backend lên Docker chỉ với 1 câu lệnh (`docker compose up -d`).

---

## Assumptions

- Thiết bị Xteink X3 đã được cài đặt firmware CrossVi 1.1.2 (hoặc CrossPoint 1.5.0) có sẵn kết nối Wi-Fi và tính năng OPDS Browser.
- Máy tính chủ (Mac mini M4 hoặc PC) cài sẵn Docker và có kết nối Internet ổn định.
- Các website nguồn truyện giữ nguyên cấu trúc API/HTML hiện tại hoặc chỉ thay đổi nhỏ trong phạm vi cập nhật rule adapter.
- Cloudflare Tunnel được sử dụng để cung cấp tên miền HTTPS miễn phí mà không yêu cầu người dùng phải có IP tĩnh hay mở cổng NAT/Port Forwarding.
