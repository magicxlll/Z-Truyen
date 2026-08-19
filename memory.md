# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh hoạt động**: `main` (Chuẩn hóa toàn diện, sạch sẽ trên GitHub)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Bản sao lưu an toàn**: `Z-Truyen_backup_20260819_212332.zip`  
**Ngày cập nhật**: 2026-08-20  

---

## 🚀 1. TỔNG QUAN VÀ TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **36/36 test cases PASS 100%** (`backend/.venv/bin/pytest backend/tests -v`).
2. **Giao diện OPDS 1.2 RFC Chuẩn hóa cho Màn hình E-ink (Stock Firmware X3)**:
   - **Root Catalog (`/opds`)**: Hiển thị trực tiếp các kho truyện chính (`Storya.click`, `AkayTruyen`, `Con Đường Bá Chủ`), các danh mục tổng hợp (`Truyện Mới Cập Nhật`, `Truyện Hot`, `Truyện Hoàn Thành`, `Thể Loại`), tính năng `Tìm Kiếm Truyện` (hỗ trợ bàn phím ảo của X3), và mục `Đọc Tiếp` thông minh.
   - **Tốc độ phản hồi tức thì (Fast In-Memory TTL Cache)**: Phản hồi khi lật trang, duyệt danh mục hoặc bấm nút **Back** giảm từ 3-4s xuống còn **< 5ms**.
3. **Hiển thị Tên Truyện & Tên Chương Sạch (Clean UI)**:
   - Danh sách truyện: Loại bỏ hoàn toàn các nhãn trạng thái dính liền (`Đang viết`, `Hoàn thành`, `Full`, `Hot`, `New`, `VIP`).
   - Danh sách chương: Định dạng chuẩn `Chương {order}_{tên chương}` (Ví dụ: `Chương 1_Tiết tử`), loại bỏ hoàn toàn hậu tố tên truyện/tác giả `- {author}`.
4. **Phân Khối Chương 50 & Gom Tập EPUB Tối Ưu Cho E-ink**:
   - Vượt qua giới hạn bộ nhớ `MAX_ENTRIES = 62` của thiết bị X3 bằng cách phân nhóm 50 chương/khối: `Chương 1 - 50`, `Chương 51 - 100`... kèm hỗ trợ duyệt phân trang `<link rel="next">`/`<link rel="previous">`.
   - Chi tiết truyện cung cấp đa dạng tùy chọn tải: Đọc Chương 1, Tải trọn bộ (ALL), và các tập gom sẵn (`Tập 01 (Chương 1-50)`, `Tập 02 (Chương 51-100)`...).
5. **Định Dạng EPUB & Quản Lý Thư Mục SD Card**:
   - File EPUB sinh ra chứa đầy đủ trang bìa `cover_page.xhtml` và metadata `cover-image` giúp X3 trích xuất cover thumbnail hiển thị trên màn hình Sleep/Home.
   - File tải về tự động được phân loại theo thư mục tên truyện: `/books/{Tên Truyện}/{Tên File}.epub`.
6. **Môi Trường Vận Hành Đa Nền Tảng**:
   - Chạy nền 24/7 trên điện thoại Android Termux với lệnh 1-Click `ztruyen` / `ztruyen-update`.
   - Máy ảo macOS kích hoạt 1-Click qua `run_crossvi_x3.command`.

---

## 💡 2. ĐÚC KẾT BÀI HỌC KINH NGHIỆM TRỌNG TÂM (KEY LESSONS LEARNED)

| STT | Bài học kinh nghiệm | Chi tiết & Nguyên tắc kỹ thuật |
|:---:|---|---|
| **1** | **Nguyên Tắc Stock Firmware (Không can thiệp FW thật)** | Toàn bộ thiết bị máy đọc sách Xteink X3 thực tế chạy firmware gốc (Stock CrossVi / CrossPoint). Toàn bộ xử lý giao diện, ngắt khối 50 chương, điều hướng URL, lọc tiêu đề, và phân trang `rel="next"` **PHẢI được giải quyết 100% tại tầng Backend OPDS**. |
| **2** | **Giới Hạn 62 Entries Của Bộ Nhớ E-ink (MAX_ENTRIES = 62)** | Trình phân tích OPDS của firmware X3 giới hạn tối đa 62 mục trên mỗi trang hiển thị. Với các bộ truyện dài (hàng trăm đến hàng ngàn chương), tuyệt đối không trả về toàn bộ danh sách trong 1 feed mà phải chia thành các khối **50 chương/khối** (`Chương 1 - 50`, `Chương 51 - 100`...). |
| **3** | **Mã Hóa Bắt Buộc `&amp;` Trong XML Atom (RFC Compliance)** | Bộ phân tích Expat XML của firmware thiết bị đọc sách rất nghiêm ngặt. Bất kỳ URL nào chứa nhiều tham số query (ví dụ: `?start=1&limit=50&sort=asc`) nếu không được encode thành `&amp;` sẽ khiến bộ đọc dừng ngay lập tức với lỗi `XML PARSE ERROR: not well-formed (invalid token)` và báo `Lỗi tải danh mục`. Luôn bọc toàn bộ URL qua `html.escape()`. |
| **4** | **Ẩn Thẻ `<author>` Trên Mục Tải Chương Để Xóa Hậu Tố** | Trong firmware CrossVi (`OpdsBookBrowserActivity.cpp`), nếu mục kiểu `BOOK` có thẻ `<author>` không rỗng, firmware sẽ tự động nối ` - {author}` vào cuối tên hiển thị trên màn hình. Để tiêu đề chương hiển thị sạch sẽ `Chương 1_Tên Chương`, **Backend phải lược bỏ thẻ `<author>`** trong các entry tải chương. |
| **5** | **Lọc Sạch Nhãn Trạng Thái Trên Tiêu Đề Truyện** | Khi cào dữ liệu từ các trang web (như AkayTruyen), các thẻ badge HTML (`Đang viết`, `Full`, `Hot`, `New`, `VIP`) thường nằm sát thẻ tên truyện khiến `a.text()` gom dính liền thành `Chung Cực Truyền KỳĐang viếtHotNew`. Cần dùng biểu thức chính quy `re.sub(r"(?:Đang\s*viết|Hoàn\s*thành|Full|Hot|New|VIP)+$", "", title)` để làm sạch. |
| **6** | **Tương Thích Bộ Font Màn Hình E-ink (Tránh Ký Tự Lạ / Emoji)** | Bộ font tích hợp sẵn trên firmware X3 không chứa các ký tự unicode đặc biệt như `⚡`, `➔`, `📖`, `📦`, khiến màn hình hiển thị thành các hình thoi đen chấm hỏi ``. Luôn dùng ký tự ASCII hoặc tiếng Việt chuẩn (`->`, `Chương 1`, `Tập 01...`). |
| **7** | **Tối Ưu Tốc Độ Phản Hồi Với FastCache (< 5ms)** | Khi người dùng thao tác bấm Back hoặc chuyển đổi qua lại giữa các menu, nếu phải cào web lại sẽ mất 3-4s. Bộ nhớ đệm RAM TTL `FastCache` lưu trữ tạm thời metadata và danh mục giúp tốc độ phản hồi đạt mức tức thì (< 5ms). |
| **8** | **Cơ Chế Bìa Sách Cho CrossVi / CrossPoint Thumbnail** | Để firmware trích xuất được ảnh bìa thu nhỏ (thumbnail) ra ngoài màn hình Home/Sleep, gói EPUB bắt buộc phải có file `cover_page.xhtml` chứa thẻ `<img src="cover.jpg" />` và khai báo `properties="cover-image"` trong file `.opf`. |
| **9** | **Quản Lý Tiến Trình Nền Android (Termux Pocket Host)** | Hệ điều hành Android tự động đóng băng (freeze) CPU khi tắt màn hình. Trên Termux, bắt buộc phải kích hoạt `Acquire wakelock` và tắt tối ưu hóa pin (`Unrestricted Battery`) để Pocket Server duy trì kết nối cho máy X3 đọc truyện xuyên suốt. |

---

## 🛠️ 3. BẢNG TỔNG HỢP LỖI THỰC TẾ & CÁCH XỬ LÝ (ERROR & RESOLUTION LOG)

| Hiện tượng lỗi | Nguyên nhân gốc rễ | Cách xử lý triệt để |
|---|---|---|
| **Lỗi tải danh mục Home ngay khi kết nối IP** | URL mục `Đọc Tiếp` chứa ký tự `&` chưa được escape (`?start=1&limit=50&sort=asc`), làm hỏng Expat XML parser. | Áp dụng `html.escape()` cho 100% URL trong tất cả các feed OPDS XML. |
| **Danh sách chương bị đúp hậu tố `- tên-truyện`** | Firmware CrossVi tự động ghép `" - " + entry.author` vào sau tiêu đề chương. | Lược bỏ thẻ `<author>` trong XML feed của các chương truyện. |
| **Tên truyện dính nhãn `Đang viếtHotNew`** | HTML scraper lấy text của cả thẻ span badge dính liền vào tên truyện. | Dùng Regex cắt bỏ toàn bộ chuỗi nhãn trạng thái ở đuôi tên truyện. |
| **Mất danh sách các tập tải (chỉ hiện 1 chương)** | Nguồn truyện trả về `total_chapters = 0`, khiến hệ thống tính nhầm là truyện có 1 chương. | Tự động phân tích pagination/danh sách chương để tính đúng tổng số chương, kèm cơ chế fallback `len(chapters)`. |
| **Biểu tượng unicode bị lỗi hình thoi đen ``** | Font chữ E-ink của X3 không có glyph cho emoji `⚡`, `➔`. | Thay thế bằng ký tự ASCII chuẩn `->` và nhãn chữ tiếng Việt rõ ràng. |
| **Máy ảo macOS bị crash/treo kết nối với Termux** | Tràn bit địa chỉ 64-bit `uintptr_t` trong `SDL2` event loop của simulator. | Thêm file patch `scripts/patch_crossvi.py` ép kiểu con trỏ an toàn khi build máy ảo desktop. |

---

## 📂 4. CẤU TRÚC REPOSITORY (CLEAN REPOSITORY STRUCTURE)

```text
Z-Truyen/
├── android/                         # Script cài đặt & chạy 1-Click trên Termux Android
│   ├── package-for-android.bat     # Đóng gói zip triển khai sang điện thoại
│   ├── requirements-termux.txt     # Danh sách dependencies tối ưu cho ARM64
│   ├── setup-termux.sh             # Script cài đặt tự động môi trường Termux
│   ├── start-server.sh             # Script khởi động server nền Uvicorn
│   └── update.sh                   # Script cập nhật code 1-Click (ztruyen-update)
├── backend/                         # Mã nguồn chính thức FastAPI Backend & OPDS
│   ├── app/
│   │   ├── api/                    # opds.py, books.py, chapters.py, search.py, health.py
│   │   │   └── opds_builder.py     # Bộ tạo XML Atom/OPDS 1.2 chuẩn hóa cho X3 (clean titles, no suffixes)
│   │   ├── cache/                  # fast_cache.py (In-Memory TTL), metadata_repo.py (SQLite), cover_service.py
│   │   ├── domain/                 # Models, IDs, Vietnamese Sanitizer
│   │   ├── epub/                   # EPUB Builder (cover_page.xhtml), Volume Bundler (KOSync SHA-1)
│   │   ├── fetcher/                # HTTP Client, Session Manager
│   │   ├── network/                # mDNS auto-discovery (ztruyen.local)
│   │   └── sources/                # Registry & Adapters: storyaclick, akaytruyen, conduongbachu
│   ├── tests/                      # 36 Integration & Unit tests (100% PASS)
│   │   ├── conftest.py             # Reset fast_cache và registry giữa các test
│   │   └── integration/            # test_features_x3.py, test_opds.py, test_sources.py...
│   ├── Dockerfile & docker-compose.yml
│   └── pyproject.toml
├── docs/                            # Tài liệu dự án đầy đủ
│   ├── ANDROID_SMARTPHONE_HOST_GUIDE.md     # Hướng dẫn cài đặt & vận hành trên điện thoại
│   ├── CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md# Hướng dẫn máy ảo CrossPoint Simulator
│   ├── FIELD_TEST_AND_DEBUG_LOG.md          # Nhật ký các lỗi thực tế & bài học kinh nghiệm
│   └── TESTING.md & WINDOWS_TEST_GUIDE.md   # Hướng dẫn test trên Windows & WSL
├── scripts/                         # Scripts công cụ dev & launcher máy ảo
│   ├── patch_crossvi.py            # Vá tương thích 64-bit cho máy ảo macOS desktop
│   ├── run_crosspoint_x3.ps1       # Script PowerShell chạy máy ảo WSL
│   └── run-dev.ps1 / run-dev.sh    # Khởi chạy dev backend
├── specs/001-z-truyen-x3/          # Đặc tả kiến trúc kỹ thuật chuẩn
├── memory.md                        # Bộ nhớ dự án & tổng hợp kinh nghiệm chuyển phiên
├── README.md                        # Hướng dẫn tổng quan dự án
├── run_crossvi_x3.command           # Phím tắt 1-Click chạy máy ảo CrossVi X3 trên macOS (Finder)
└── run_crossvi_x3.sh                # Script chạy máy ảo CrossVi X3 trên macOS (Terminal)
```

---

## 📖 5. HƯỚNG DẪN VẬN HÀNH & BÀN GIAO (OPERATION CHEATSHEET)

### A. Dành cho điện thoại Android (Pocket Host Server)
1. **Khởi động server**: Mở Termux $\rightarrow$ gõ `ztruyen`.
2. **Cập nhật mã nguồn mới nhất**: Gõ `ztruyen-update`.
3. **Giữ server chạy khi tắt màn hình**: Kéo thanh thông báo Android $\rightarrow$ chọn **Acquire wakelock**.

### B. Dành cho máy đọc sách Xteink X3 (Thiết bị thật)
1. Mở **OPDS Browser** trên máy X3.
2. Nhập địa chỉ: `http://ztruyen.local:8080/opds` (hoặc IP hiển thị trên màn hình Termux, ví dụ `http://192.168.1.15:8080/opds`).
3. Duyệt truyện và bấm **Tải về** để đọc mượt mà offline.

### C. Dành cho máy ảo Simulator (macOS)
- Chạy phím tắt 1-click [run_crossvi_x3.command](file:///Users/vietph/Library/CloudStorage/GoogleDrive-vietph.eng@gmail.com/Other%20computers/My%20Computer/DATA/Antigravity/Z-Truyen/Z-Truyen/run_crossvi_x3.command).
