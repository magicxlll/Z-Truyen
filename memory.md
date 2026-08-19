# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh hoạt động**: `main` (Đã dọn dẹp sạch sẽ, thuần khiết mã nguồn trên GitHub)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Bản sao lưu an toàn**: `Z-Truyen_backup_20260819_212332.zip` (5.40 MB)  
**Ngày cập nhật**: 2026-08-20  

---

## 🚀 1. TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **36/36 test cases PASS 100%** (`python -m pytest backend/tests -v`).
2. **Bộ Nhớ Đệm Tốc Độ Cao (Fast In-Memory TTL Cache)**:
   - Module `backend/app/cache/fast_cache.py` lưu cache bộ nhớ trong cho các feed OPDS (Hot, Latest, Completed, Genres), metadata truyện và danh sách toàn bộ chương.
   - Thời gian phản hồi khi bấm nút **Back** hoặc quay lại các màn hình danh mục giảm từ 3-4s xuống còn **< 5ms (tức thì)**.
3. **Tiêu Đề & Giao Diện Sạch Sẽ (Clean UI Titles)**:
   - Khi ở trong từng kho truyện (Storya.click, AkayTruyen, Con Đường Bá Chủ), tiêu đề feed hiển thị đúng tên kho truyện: `📚 {Tên Kho}`.
   - Tên các danh mục con hiển thị gọn gàng (`⚡ Truyện Mới Cập Nhật`, `🔥 Truyện Hot & Đọc Nhiều`, `✅ Truyện Hoàn Thành`, `📂 Thể Loại Truyện`), loại bỏ hoàn toàn các hậu tố lặp lại `(khotruyen)` hoặc URL.
4. **Cú Pháp Tên Chương Chuẩn Hóa**:
   - Định dạng chuẩn: `Chương {order}_{tên chương}` (Ví dụ: `Chương 1_Tiết tử`, `Chương 2_Khởi đầu mới`).
   - Loại bỏ hoàn toàn tên truyện hoặc tên tác giả làm hậu tố phía sau cả trên thẻ `<title>` và `<summary>`.
5. **Phân Khối Chương & Phân Trang Thông Minh (Vượt Giới Hạn 62 Mục Của X3/CrossVi)**:
   - Do giới hạn bộ nhớ RAM của thiết bị e-ink X3 (`MAX_ENTRIES = 62` trong `OpdsParser`), các truyện dài (> 50 chương, như Mục Thần Ký, Đấu Phá Thương Khung 1000+ chương) được tự động phân nhóm thành các khối **50 chương/khối**:
     - `📂 Chương 1 - 50`
     - `📂 Chương 51 - 100`
     - `📂 Chương 101 - 150`
     - ...
     - Kèm mục `📖 Đọc Tiếp: Chương {X}` dẫn thẳng vào khối chương đang đọc dở.
   - Mỗi khối chương hỗ trợ đầy đủ phân trang với liên kết `<link rel="next">` và `<link rel="previous">` chuẩn OPDS 1.2 RFC, cho phép người dùng lật trang liên tục để sang 50 chương tiếp theo trên phím lật trang của X3.
6. **Lưu Trữ Tự Động Theo Thư Mục Tên Truyện**:
   - File EPUB tải về được gom riêng theo từng truyện tại `data/epubs/{story_slug}/` và `downloads/{story_slug}/`.
7. **Pocket Host Server trên Android (Termux)** & **Máy Ảo macOS/WSL**:
   - Chạy nền mượt mà trên Termux với `ztruyen`, hỗ trợ mDNS `ztruyen.local:8080/opds`.
   - Máy ảo macOS kích hoạt 1-click qua `run_crossvi_x3.command`.

---

## 📂 2. CẤU TRÚC REPOSITORY (CLEAN CODEBASE)

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
│   │   ├── api/                    # opds.py, books.py, chapters.py, search.py, web.py, health.py
│   │   │   └── opds_builder.py     # Bộ tạo XML Atom/OPDS 1.2 chuẩn hóa cho X3 (khối 50 chương & format sạch)
│   │   ├── cache/                  # fast_cache.py (In-Memory TTL), metadata_repo.py (SQLite), object_storage.py, cover_service.py
│   │   ├── domain/                 # Models, IDs, Vietnamese Sanitizer
│   │   ├── epub/                   # EPUB Builder, Volume Bundler (KOSync SHA-1)
│   │   ├── fetcher/                # HTTP Client, Session, Headless fallback
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
├── memory.md                        # Bộ nhớ dự án & hướng dẫn chuyển phiên
├── README.md                        # Hướng dẫn tổng quan dự án
├── run_crossvi_x3.command           # Phím tắt 1-Click chạy máy ảo CrossVi X3 trên macOS (Finder)
└── run_crossvi_x3.sh                # Script chạy máy ảo CrossVi X3 trên macOS (Terminal)
```

---

## 💡 3. ĐÚC KẾT BÀI HỌC KINH NGHIỆM TRỌNG TÂM (KEY LESSONS LEARNED)

| STT | Bài học kinh nghiệm | Chi tiết & Nguyên tắc |
|:---:|---|---|
| **1** | **Nguyên tắc Stock Firmware** | Tuyệt đối **KHÔNG** sửa đổi firmware của thiết bị thật X3. Toàn bộ logic giao diện, khối chương 50, phân trang `rel="next"` xử lý chuẩn mực tại Backend OPDS 1.2 RFC. |
| **2** | **Giới hạn 62 Entries của E-ink** | CrossVi / CrossPoint quy định `MAX_ENTRIES = 62` trên mỗi trang feed. Với truyện nhiều chương, luôn gom khối 50 chương/khối (`📂 Chương 1 - 50`, `📂 Chương 51 - 100`...) kèm link `rel="next"` để lật trang mượt mà không bị ngắt quãng. |
| **3** | **Tối ưu tốc độ với FastCache** | Áp dụng cache RAM TTL cho metadata truyện và danh sách chương. Khi người dùng bấm Back hoặc chuyển đổi qua lại, server phản hồi < 5ms thay vì gọi lại web scraping mất 3-4s. |
| **4** | **Cú pháp tên chương & tên truyện sạch** | Chuẩn hóa định dạng `Chương {order}_{tên chương}` (ví dụ: `Chương 1_Tiết tử`), loại bỏ tên truyện/tác giả làm hậu tố. Với danh sách truyện, loại bỏ triệt để các nhãn trạng thái `Đang viết`, `Full`, `Hot`, `New`. |
| **5** | **Ẩn thẻ Author trên Mục Tải Chương/Tập** | Firmware CrossVi tự động nối ` - {author}` vào cuối tên nếu thẻ `<author>` tồn tại trong entry. Để hiển thị tên chương/tập thuần túy không bị dài dòng hay tràn chữ, lược bỏ thẻ `<author>` tại các entry tải chương và tập gom. |
| **6** | **Mã hóa bắt buộc &amp; trong XML Atom** | Mọi URL có chứa query parameters (như `?start=1&limit=50&sort=asc`) bắt buộc phải bọc `html.escape()` thành `&amp;` để bộ giải mã Expat XML Parser của thiết bị không bị dừng với lỗi `not well-formed token`. |
| **7** | **Tránh Ký Tự / Emoji Phức Tạp Trên Màn Hình E-ink** | Font chữ mặc định của X3 không hỗ trợ các ký tự Unicode như `⚡`, `➔`, dẫn đến việc bị hiển thị thành ký tự lỗi hình thoi đen ``. Luôn dùng ký tự chuẩn `->`, `[Doc]`, `[Tai]` hoặc tiếng Việt thuần túy. |
