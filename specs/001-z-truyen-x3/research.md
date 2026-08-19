# Research & Technical Decisions: Z-Truyen X3

**Feature**: `001-z-truyen-x3`  
**Date**: 2026-08-18  
**Status**: Completed  

---

## 1. Kiến Trúc Backend & Web Framework

- **Decision**: Sử dụng **Python 3.12+** cùng **FastAPI** và **Uvicorn** (Asynchronous ASGI).
- **Rationale**:
  - FastAPI cung cấp hiệu năng I/O bất đồng bộ (async/await) xuất sắc cho tác vụ cào web song song và phục vụ OPDS feed.
  - Tích hợp sẵn Pydantic v2 để validate dữ liệu chặt chẽ và sinh OpenAPI docs tự động.
  - Hệ sinh thái Python có sẵn các thư viện bóc tách HTML, xử lý ảnh (Pillow), giải mã anti-bot và đóng gói EPUB mạnh nhất hiện nay.
- **Alternatives Considered**:
  - *Node.js / Express / Fastify*: Xử lý I/O tốt nhưng thiếu các thư viện xử lý EPUB sạch chuẩn định dạng và toolchain bóc tách tiếng Việt tối ưu bằng Python.
  - *Go (Golang)*: Tốc độ cao, binary gọn nhưng viết rule cào HTML linh hoạt và tích hợp headless browser (Playwright) phức tạp hơn Python.

---

## 2. Chiến Lược Scraper Engine & Bypass Cloudflare Anti-Bot

- **Decision**: Kiến trúc **Hybrid Scraper 2 Lớp**:
  - **Lớp 1 (Fast Path)**: `httpx.AsyncClient` kết hợp `selectolax` (Modest parser viết bằng C, nhanh gấp 10-20 lần BeautifulSoup4).
  - **Lớp 2 (Headless Fallback Path)**: Tích hợp `playwright-python` chạy Chromium ở chế độ Stealth khi gặp HTTP 403 Forbidden hoặc Cloudflare Turnstile Challenge.
- **Rationale**:
  - `storya.click` và `conduongbachu.com` cung cấp sẵn REST API JSON (`/api/v1` và `/wp-json/wp/v2`), Fast Path xử lý trong < 200ms.
  - `akaytruyen.com` sử dụng Laravel HTML và có thể kích hoạt bảo vệ chống bot, Fallback Path đảm bảo 100% tỷ lệ cào thành công.
- **Alternatives Considered**:
  - *FlareSolverr*: Chạy container riêng biệt, nhưng tiêu tốn thêm RAM và độ trễ cao hơn việc tích hợp trực tiếp Playwright.
  - *httpx đơn thuần*: Thất bại ngay lập tức khi web nguồn bật Cloudflare Under Attack mode.

---

## 3. Chiến Lược Đóng Gói EPUB & Tối Ưu Hóa ESP32-C3

- **Decision**: Hỗ trợ 2 chế độ đóng gói EPUB với thuật toán **Deterministic Packaging**:
  - **Quyển (Volume Bundling)**: Mặc định 50 chương / 1 file EPUB (ví dụ: `ztruyen_conduongbachu_main_v01.epub`).
  - **Chương Đơn (Single Chapter)**: 1 chương / 1 file EPUB phục vụ đọc nhanh các chương mới ra.
  - Cấu trúc file EPUB: Tạo chuẩn EPUB 2/3 với mã hóa UTF-8, CSS siêu nhẹ (< 2KB), loại bỏ hoàn toàn script, font nhúng rác và thẻ lồng nhau không cần thiết. Mỗi đoạn văn được bọc trong thẻ `<p id="p-{index}">` rõ ràng.
- **Rationale**:
  - ESP32-C3 của X3 chỉ có ~380KB RAM. File EPUB dung lượng 300KB - 800KB (50 chương) chiếm bộ nhớ rất nhỏ khi giải nén từng chương vào RAM.
  - Giảm số lượng file trên hệ thống FAT32 của thẻ SD từ hàng nghìn file xuống chỉ vài chục file, ngăn chặn hiện tượng đơ máy khi quét thư mục.
  - Cấu trúc thẻ `<p id="p-X">` tất định (deterministic) giúp thuật toán XPath mapper của CrossVi/CrossPoint KOSync hoạt động chính xác tuyệt đối.
- **Alternatives Considered**:
  - *Gom toàn bộ bộ truyện (1000-3000 chương) vào 1 file duy nhất*: Dung lượng file > 20MB sẽ làm ESP32-C3 tràn RAM (Heap Out Of Memory) khi mở sách hoặc đánh chỉ mục (indexing).

---

## 4. Giao Thức OPDS 1.2 & Tương Thích CrossVi/CrossPoint

- **Decision**: Cung cấp **OPDS 1.2 Catalog (Atom XML Feed)** đầy đủ:
  - `/opds`: Root catalog (Duyệt theo Nguồn, Truyện Hot, Truyện Mới Cập Nhật, Thể Loại).
  - `/opds/search?q={query}`: Tìm kiếm truyện theo chuẩn OpenSearch Description.
  - `/opds/book/{source_id}/{book_id}`: Chi tiết truyện, danh sách các Tập/Volume để tải và danh sách từng chương lẻ.
  - `/opds/download/{source_id}/{book_id}/{artifact_name}`: Đường dẫn tải trực tiếp file `.epub` (MIME: `application/epub+zip`).
- **Rationale**:
  - Firmware CrossVi 1.1.2 và CrossPoint 1.5.0 đã có sẵn OPDS Browser hoàn chỉnh, hỗ trợ duyệt danh mục, tìm kiếm và tải sách trực tiếp về thẻ nhớ SD.
  - Hoạt động 100% ngoài luồng (out-of-the-box) mà không cần chỉnh sửa hay nạp lại firmware X3.
- **Alternatives Considered**:
  - *Viết Native C/C++ App trên firmware CrossVi*: Tăng nguy cơ brick thiết bị, xung đột mã nguồn khi upstream cập nhật và tốn thời gian bảo trì.

---

## 5. Cơ Chế Lưu Trữ & Bộ Nhớ Đệm (Caching Strategy)

- **Decision**: **SQLite (WAL Mode)** cho Metadata + **Local Filesystem** cho Object Storage (EPUB & Covers).
  - Database schema: `sources`, `stories`, `chapters`, `volumes`, `credentials`.
  - Directory storage: `/data/cache/covers/` và `/data/cache/epubs/`.
- **Rationale**:
  - SQLite gọn nhẹ, không cần cài đặt service database nặng nề, tốc độ đọc truy vấn cao khi bật WAL mode (`PRAGMA journal_mode=WAL;`).
  - File EPUB sau khi được build lần đầu sẽ lưu vĩnh viễn trên disk cache; các lần tải tiếp theo từ X3 hoặc KOReader là Cache Hit (tốc độ tải tối đa băng thông Wi-Fi).
- **Alternatives Considered**:
  - *Redis + PostgreSQL*: Quá phức tạp và dư thừa tài nguyên cho nhu cầu self-host cá nhân trên Mac mini M4.

---

## 6. Giải Pháp Kết Nối Từ Xa An Toàn (Remote Tunneling)

- **Decision**: Sử dụng **Cloudflare Tunnel (cloudflared)** đóng gói sẵn trong `docker-compose.yml`.
- **Rationale**:
  - Miễn phí 100%, tự động cấp chứng chỉ SSL/TLS HTTPS hợp lệ.
  - Không yêu cầu mở cổng NAT (Port Forwarding) trên router gia đình, chống tấn công DDoS và quét cổng mạng.
  - Thiết bị Xteink X3 chỉ cần nhập URL dạng `https://ztruyen.tenmiencuaban.com/opds` là truy cập được ở bất kỳ mạng Wi-Fi nào.
- **Alternatives Considered**:
  - *Tailscale / WireGuard*: Rất tốt cho máy tính/điện thoại, nhưng firmware ESP32 của X3 không có client VPN chuyên dụng.
