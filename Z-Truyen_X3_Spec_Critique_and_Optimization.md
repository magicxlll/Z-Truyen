# Z-Truyen X3 — Phản Biện Chi Tiết Specification & Kiến Trúc Tối Ưu Đã Thống Nhất

**Ngày lập:** 2026-08-13  
**Đối tượng phản biện:** [Z-Truyen_X3_Project_Spec.md](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/Z-Truyen_X3_Project_Spec.md)  
**Trạng thái:** Báo cáo phản biện độc lập & Kiến trúc tối ưu hóa (Đã qua Phỏng vấn Phản biện / Grill-me)  

---

## 1. Tổng Quan Đánh Giá Spec Gốc

Tài liệu `Z-Truyen_X3_Project_Spec.md` là một bản thiết kế kỹ thuật (Engineering Specification) rất chỉn chu, có tư duy hệ thống cao, tôn trọng nguyên tắc an toàn phần cứng (không độ chế firmware ngay từ đầu), phân chia rõ các phase từ Phase 0 tới Phase 14 và đưa ra chiến lược kiểm thử nghiêm ngặt.

Tuy nhiên, qua phân tích chuyên sâu ở góc độ thực thi thực tế (real-world execution) trên phần cứng ESP32-C3 (RAM ~380KB) và hệ sinh thái truyện chữ/truyện tranh online tại Việt Nam, **spec gốc tồn tại 5 điểm nghẽn nghiêm trọng (Critical Bottlenecks)** đã được phản biện và thống nhất phương án tối ưu sau phỏng vấn.

---

## 2. 5 Điểm Phản Biện Trọng Tâm & Quyết Định Sau Phỏng Vấn (Grill-me Decisions)

### 2.1. Chiến lược đóng gói EPUB & Trải nghiệm đọc (Section 8.1 trong Spec)
- **Vấn đề Spec gốc:** Đề xuất Phase MVP chỉ tạo mỗi chương truyện (Chapter) thành 1 file EPUB riêng lẻ (`1 Chapter = 1 EPUB`).
- **Phản biện kỹ thuật:** Đọc 1 chương (2-3 phút) phải thoát ra menu OPDS để tải chương tiếp theo gây gián đoạn trải nghiệm đọc; đồng thời gây quá tải chỉ mục FAT32 trên thẻ nhớ SD của ESP32-C3.
- **Quyết định đã thống nhất:** **Hỗ trợ linh hoạt cả 2 chế độ trên Backend**:
  - Chế độ Gom Tập/Quyển (Dynamic Volume Bundling: 50 - 100 chương / 1 file EPUB) để đọc liên tục mượt mà, tối ưu thẻ nhớ SD.
  - Chế độ Tải lẻ từng chương (Single Chapter EPUB) phục vụ nhu cầu tải nhanh từng chương cập nhật mới.
  - Người dùng có thể lựa chọn chế độ tải qua thông số truy vấn OPDS hoặc cấu hình Backend.

---

### 2.2. Nguồn truyện ưu tiên & Cơ chế Bypass Cloudflare Anti-Bot (Section 9.1 & 5.3)
- **Vấn đề Spec gốc:** Dự kiến Backend dùng `httpx` + `selectolax` thuần túy.
- **Phản biện kỹ thuật:** Các trang web truyện chữ Việt Nam thường đặt sau Cloudflare Protection (Turnstile/Challenge) hoặc Anti-DDoS Guard, gửi HTTP request thuần sẽ bị trả về 403 Forbidden.
- **Quyết định đã thống nhất:** 
  - **Ưu tiên 3 nguồn truyện chính do người dùng chỉ định:**
    1. `storya.click`
  - **Cơ chế kỹ thuật cào dữ liệu 3 nguồn (trích xuất từ `Z-Truyenviet.koplugin`):**
    1. **`storya.click`**: Web dạng Next.js SPA. Cào trực tiếp qua hệ thống **REST API JSON** (`https://storya.click/api/v1`). Search (`/stories/search`), Chapter List (`/chapters/story/{slug}?limit=100`), Chapter Content (`/chapters/{story}/{chap}`). Tốc độ cực nhanh, không cần parse HTML DOM.
    2. **`akaytruyen.com`**: Web dạng Laravel. Hỗ trợ **Đăng nhập lấy chương VIP** (`POST /login` với token CSRF và Cookie session). Lấy danh sách chương qua API JSON (`/search-chapters?page=N`) trả về fragment HTML. Parse nội dung chương từ `<div id="chapter-content">`.
    3. **`conduongbachu.com`**: Web dạng WordPress CMS. Cào danh mục chương qua **WordPress REST API** (`/wp-json/wp/v2/posts?categories={cat_id}&per_page=100`). Đã map sẵn 4 danh mục: Chính Truyện (Cat 3) và 3 Ngoại Truyện (Cat 12, 14, 15). Parse nội dung chương từ `<div class="entry-content">`.
  - **Kiến trúc Scraper 2 Lớp (Hybrid Scraper Architecture):**
    - Fast Path (`httpx` + `selectolax` / JSON API) cho các request tốc độ cao.
    - Headless Browser Fallback Path (**FlareSolverr / Playwright Stealth**) chạy ẩn trong Docker Backend khi dính Cloudflare Challenge.

---


### 2.3. Hạ tầng triển khai Backend & Kết nối từ xa (Section 11 & 12)
- **Vấn đề Spec gốc:** Khuyến nghị dùng Cloud Run + Cloudflare D1 + R2 làm kiến trúc chính.
- **Phản biện kỹ thuật:** Chạy Headless Browser trên Cloud Run tốn nhiều tài nguyên RAM/CPU, dễ phát sinh chi phí vượt Free Tier.
- **Quyết định đã thống nhất:** **Hybrid Local-First Architecture**:
  - Triển khai Backend Docker trên máy **Mac mini M4** tại nhà (chạy 24/7, dư thừa hiệu năng).
  - Tích hợp **Cloudflare Tunnel (Zero Trust - Mã hóa HTTPS miễn phí)** giúp thiết bị X3 truy cập an toàn từ xa ở bất kỳ đâu có Wi-Fi mà không cần mở port router.

---

### 2.4. Tính Khả Thi của KOSync Cross-Device (Section 4 & Phase 4)
- **Vấn đề Spec gốc:** Đồng bộ tiến trình đọc (KOSync) với KOReader trên Android/Kobo.
- **Phản biện kỹ thuật:** Nếu file EPUB trên X3 và thiết bị khác không đồng nhất 100% từng byte hoặc khác cấu trúc DOM, KOSync sẽ nhảy sai trang.
- **Quyết định đã thống nhất:** **Strict Document Identity Protocol**:
  - Chuẩn hóa quy tắc đặt tên file: `ztruyen_{source_id}_{book_id}_v{vol_index}.epub`.
  - Đảm bảo cấu trúc HTML/CSS bên trong file EPUB là 100% deterministic (byte-exact), giúp Hash SHA-1 trùng khớp tuyệt đối giữa X3 và KOReader trên Android/Kobo/PC.

---

### 2.5. Định Hướng Can Thiệp Firmware X3 (Section 16 & Phase 6)
- **Vấn đề Spec gốc:** Kế hoạch sửa firmware CrossVi C/C++ ở Phase 6 để viết App Native Z-Truyen trên X3.
- **Phản biện kỹ thuật:** Sửa C/C++ trên firmware ESP32 tăng rủi ro crash, tràn bộ nhớ RAM (380KB), gây rủi ro brick thiết bị và khó bảo trì khi upstream phát hành bản mới. Trong khi CrossVi 1.1.2 đã có sẵn OPDS Browser rất hoàn chỉnh.
- **Quyết định đã thống nhất:** **Bắt đầu với 100% OPDS chuẩn của CrossVi trước**:
  - Đảm bảo an toàn tuyệt đối 100%, không có rủi ro brick X3.
  - Chỉ xem xét nghiên cứu sửa Firmware Native C/C++ nếu trong quá trình sử dụng thực tế OPDS bộc lộ hạn chế nghiêm trọng không thể khắc phục bằng Backend.

---

## 3. Kiến Trúc Giải Pháp Tối Ưu Đã Thống Nhất (Target Architecture)

```text
                               INTERNET
                                  |
            +---------------------+---------------------+
            |                     |                     |
            v                     v                     v
     storya.click          akaytruyen.com       conduongbachu.com
            +---------------------+---------------------+
                                  |
                                  | (HTTPS / Hybrid Scraper: Fast + Playwright)
                                  v
+-------------------------------------------------------------------+
| Z-TRUYEN BACKEND (Docker trên Mac mini M4 gia đình)               |
|                                                                   |
|  +-------------------+  +--------------------+  +--------------+  |
|  | Hybrid Scraper    |  | Storage & Cache    |  | EPUB Builder |  |
|  | - storya.click    |  | - SQLite (Metadata)|  | - Single Ch  |  |
|  | - akaytruyen.com  |  | - Local File Cache |  | - Volume Ch  |  |
|  | - conduongbachu   |  |   (EPUB/Covers)    |  | - Determin-  |  |
|  | - Playwright Fall |  +---------+----------+  |   istic Hash |  |
|  +---------+---------+            |             +-------+------+  |
|            |                      |                     |     |
|            +----------------------+---------------------+     |
|                                   |                           |
|                                   v                           |
|                        +--------------------+                 |
|                        | OPDS 1.2 Provider  |                 |
|                        | Fast API Gateway   |                 |
|                        +---------+----------+                 |
+----------------------------------|--------------------------------+
                                   | (Mã hóa HTTPS qua Cloudflare Tunnel)
                                   v
             +---------------------+---------------------+
             |                                           |
             v                                           v
  +-----------------------+                   +--------------------+
  | Xteink X3 (CrossVi)   |                   | KOReader Devices   |
  | Native OPDS Client    |                   | Android / Kobo...  |
  | (Không cần sửa FW)    |                   +--------------------+
  +-----------+-----------+
              | (Tải EPUB Đơn / Quyển)
              v
  +-----------------------+
  | Thẻ nhớ SD (Storage)  |
  +-----------+-----------+
              |
              v
  +-----------------------+
  | Native Reader Engine  |
  | (KOSync đồng bộ vị trí)|
  +-----------------------+
```

---

## 4. Kế Hoạch Triển Khai Tiếp Theo (Action Plan)

1. **Phase 0 & 1:** Khởi tạo Backend Skeleton bằng Python (FastAPI + Pydantic + SQLite + Ebooklib).
2. **Phase 2:** Phát triển Source Adapter cho 3 nguồn ưu tiên (`storya.click`, `akaytruyen.com`, `conduongbachu.com`).
3. **Phase 3:** Xây dựng Engine đóng gói EPUB kép (Hỗ trợ cả Tải đơn chương & Gom quyển) + Trình xuất OPDS 1.2 XML.
4. **Phase 4:** Kết nối Docker Backend với Cloudflare Tunnel để cấp URL HTTPS công cộng an toàn.
5. **Phase 5:** Thử nghiệm kết nối OPDS trực tiếp từ Xteink X3 (CrossVi 1.1.2) & Kiểm tra KOSync với KOReader trên Android.
