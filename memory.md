# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh hoạt động**: `main` (Chuẩn hóa toàn diện, sạch sẽ trên GitHub)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Ngày cập nhật**: 2026-08-22  
**Trạng thái kiểm thử thực tế**: 🟢 **ĐÃ XÁC THỰC THÀNH CÔNG 100% TRÊN MÁY THẬT XTEINK X3 (CROSSPOINT 1.6-RC) QUA 5G HOTSPOT DI ĐỘNG & WI-FI LAN**.

---

## 🚀 1. TỔNG QUAN VÀ TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **36/36 test cases PASS 100%** (`python -m pytest backend/tests -v`).
2. **Giao Diện Menu Chính OPDS Tinh Gọn (8 Mục Chuẩn Cho E-ink)**:
   - `🌐 1. Chọn Nguồn Truyện` (`/opds/sources`): Chuyển đổi giữa các kho truyện `AkayTruyen`, `Storya.click`, `Con Đường Bá Chủ`, `Tất Cả Nguồn`.
   - `📚 2. Nguồn: [Tên Nguồn Hiện Tại]`: Hiển thị nguồn đang kích hoạt (lưu trong SQLite `active_source`).
   - `📖 3. Đọc Tiếp: [Tên Truyện] (Chương X)`: Dẫn trực tiếp đến danh sách chương của tác phẩm vừa tải/đọc gần nhất.
   - `⚡ 4. Truyện Mới Cập Nhật`: Lọc theo nguồn đang kích hoạt.
   - `🔥 5. Truyện Hot & Đọc Nhiều`: Lọc theo nguồn đang kích hoạt.
   - `✅ 6. Truyện Hoàn Thành (Full Trọn Bộ)`: Lọc theo nguồn đang kích hoạt.
   - `📂 7. Thể Loại Truyện`: Lọc theo nguồn đang kích hoạt.
   - `🔍 8. Tìm Truyện (Không Dấu & Có Dấu)`: Tìm kiếm tác phẩm trong nguồn hiện tại.
3. **Bộ Tìm Kiếm Tiếng Việt Không Dấu (`remove_accents`)**:
   - Khắc phục triệt để rào cản bàn phím ảo Latin (ASCII) của máy đọc sách E-ink.
   - Cho phép người dùng gõ từ khóa không dấu (ví dụ: `muc than ky`, `thien la`, `con duong ba chu`, `chung cuc truyen ky`...) và tìm thấy chính xác tác phẩm.
4. **Phân Khối Chương 50 & Gom Tập EPUB Tối Ưu Cho E-ink**:
   - Vượt qua giới hạn bộ nhớ `MAX_ENTRIES = 62` của thiết bị X3 bằng cách phân nhóm 50 chương/khối: `Chương 1 - 50`, `Chương 51 - 100`... kèm hỗ trợ duyệt phân trang `<link rel="next">`/`<link rel="previous">`.
   - Chi tiết truyện cung cấp đa dạng tùy chọn tải: Đọc từng chương lẻ (streaming 0.3s), Tải trọn bộ (ALL), và các tập gom sẵn (`Tập 01 (Chương 1-50)`, `Tập 02 (Chương 51-100)`...).
5. **Cấu Trúc Lưu Trữ SDCard & Đặt Tên File Tự Động**:
   - **Thư mục lưu trữ**: Tự động tạo thư mục con theo tên truyện trên thẻ nhớ: `SDCard/Books/{Tên Truyện}/{Tên File}.epub`.
   - **Cú pháp tên file**: `{Tên viết tắt}_{Tập truyện}_{Chương truyện}.epub` (Ví dụ: `LHTNQ_Trọn Bộ_chương 1-54.epub`, `NTCTCL_Trọn Bộ_chương 1-35.epub`, `STNT_Trọn Bộ_chương 1-51.epub`).
6. **Xử Lý Ảnh Bìa (Cover Art) Sắc Nét Cho E-ink**:
   - Bộ cào dữ liệu tự động bóc tách ảnh bìa đa tầng: OpenGraph `<meta property="og:image">` và DOM `.book-3d img`.
   - Tự động chuyển đổi ảnh PNG/WebP sang JPEG 16-level grayscale kích thước chuẩn E-ink.
   - Gói EPUB chứa đầy đủ `cover_page.xhtml` và metadata `cover-image` giúp firmware X3 trích xuất thumbnail hiển thị trên màn hình Home/Sleep.
7. **Tốc độ phản hồi tức thì (Fast In-Memory TTL Cache)**:
   - Phản hồi khi lật trang, duyệt danh mục hoặc bấm nút **Back** đạt tốc độ **< 5ms**.
8. **Môi Trường Vận Hành Đa Nền Tảng**:
   - Chạy nền 24/7 trên điện thoại Android Termux với lệnh 1-Click `ztruyen` / `ztruyen-update` / `ztruyen-debug` / `ztruyen-monitor`.
   - Máy ảo Windows WSL2 / WSLg kích hoạt qua `run_crosspoint_x3.bat`.
   - Máy ảo macOS kích hoạt 1-Click qua `run_crossvi_x3.command`.

---

## 💡 2. ĐÚC KẾT BÀI HỌC KINH NGHIỆM TRỌNG TÂM (KEY LESSONS LEARNED)

| STT | Bài học kinh nghiệm | Chi tiết & Nguyên tắc kỹ thuật |
|:---:|---|---|
| **1** | **Nguyên Tắc Stock Firmware (Không can thiệp FW thật)** | Toàn bộ thiết bị máy đọc sách Xteink X3 thực tế chạy firmware gốc (Stock CrossVi / CrossPoint). Toàn bộ xử lý giao diện, ngắt khối 50 chương, điều hướng URL, lọc tiêu đề, và phân trang `rel="next"` **PHẢI được giải quyết 100% tại tầng Backend OPDS**. |
| **2** | **Cơ Chế Tạo Thư Mục Con `Books/{Tên Truyện}` Qua Thẻ `<author>`** | Firmware X3 (`OpdsBookBrowserActivity.cpp`) tự động tạo thư mục con khi tải sách dựa trên thẻ `<author><name>` trong OPDS feed. Nếu truyền tên tác giả, sách sẽ bị phân tán hoặc vào thư mục "Đang cập nhật". **Backend phải truyền `<author><name>{story.title}</name>` trong các entry tải sách** để firmware gom toàn bộ tập/chương vào đúng thư mục tên truyện `SDCard/Books/{Tên Truyện}/`. |
| **3** | **Trích Xuất & Xử Lý Ảnh Bìa (Cover Art) Đa Tầng** | Một số nguồn truyện (như AkayTruyen) đặt ảnh bìa trong OpenGraph `<meta>` hoặc thẻ `div.book-3d img`. Scraper phải kiểm tra cả OpenGraph lẫn DOM. Module `cover_service` phải chuyển đổi ảnh sang chuẩn JPEG Grayscale và nhúng `cover_page.xhtml` + `properties="cover-image"` trong file `.opf` để firmware sinh `thumb_226.bmp`. |
| **4** | **Tìm Kiếm Tiếng Việt Không Dấu Cho Bàn Phím E-ink** | Bàn phím ảo X3 chỉ có ký tự Latin (ASCII). Module `sanitizer.py` tích hợp `remove_accents` chuẩn hóa Unicode. Backend hỗ trợ tìm kiếm đa tầng (direct search, slug search `muc-than-ky`, và so khớp chuỗi không dấu) giúp tìm thấy truyện ngay cả khi gõ không dấu. |
| **5** | **Giới Hạn 62 Entries Của Bộ Nhớ E-ink (MAX_ENTRIES = 62)** | Trình phân tích OPDS của firmware X3 giới hạn tối đa 62 mục trên mỗi trang hiển thị. Với các bộ truyện dài (hàng trăm đến hàng ngàn chương), tuyệt đối không trả về toàn bộ danh sách trong 1 feed mà phải chia thành các khối **50 chương/khối** (`Chương 1 - 50`, `Chương 51 - 100`...). |
| **6** | **Mã Hóa Bắt Buộc `&amp;` Trong XML Atom (RFC Compliance)** | Bộ phân tích Expat XML của firmware thiết bị đọc sách rất nghiêm ngặt. Bất kỳ URL nào chứa nhiều tham số query (ví dụ: `?start=1&limit=50&sort=asc`) nếu không được encode thành `&amp;` sẽ khiến bộ đọc dừng ngay lập tức với lỗi `XML PARSE ERROR: not well-formed (invalid token)` và báo `Lỗi tải danh mục`. Luôn bọc toàn bộ URL qua `html.escape()`. |
| **7** | **Ẩn Thẻ `<author>` Trên Mục Tải Chương Để Xóa Hậu Tố** | Trong firmware CrossVi (`OpdsBookBrowserActivity.cpp`), nếu mục kiểu `BOOK` có thẻ `<author>` không rỗng, firmware sẽ tự động nối ` - {author}` vào cuối tên hiển thị trên màn hình. Để tiêu đề chương hiển thị sạch sẽ `Chương 1_Tên Chương`, Backend phải lược bỏ thẻ `<author>` trong các entry hiển thị chương. |
| **8** | **Lọc Sạch Nhãn Trạng Thái Trên Tiêu Đề Truyện** | Khi cào dữ liệu từ các trang web, các thẻ badge HTML (`Đang viết`, `Full`, `Hot`, `New`, `VIP`) thường nằm sát thẻ tên truyện khiến `a.text()` gom dính liền thành `Chung Cực Truyền KỳĐang viếtHotNew`. Cần dùng biểu thức chính quy `re.sub(r"(?:Đang\s*viết|Hoàn\s*thành|Full|Hot|New|VIP)+$", "", title)` để làm sạch. |
| **9** | **Tương Thích Bộ Font Màn Hình E-ink (Tránh Ký Tự Lạ / Emoji)** | Bộ font tích hợp sẵn trên firmware X3 không chứa các ký tự unicode đặc biệt như `⚡`, `➔`, `📖`, `📦`, khiến màn hình hiển thị thành các hình thoi đen chấm hỏi ``. Luôn dùng ký tự ASCII hoặc tiếng Việt chuẩn (`->`, `Chương 1`, `Tập 01...`). |
| **10** | **Tối Ưu Tốc Độ Phản Hồi Với FastCache (< 5ms)** | Khi người dùng thao tác bấm Back hoặc chuyển đổi qua lại giữa các menu, nếu phải cào web lại sẽ mất 3-4s. Bộ nhớ đệm RAM TTL `FastCache` lưu trữ tạm thời metadata và danh mục giúp tốc độ phản hồi đạt mức tức thì (< 5ms). |
| **11** | **Quản Lý Tiến Trình Nền Android (Termux Pocket Host)** | Hệ điều hành Android tự động đóng băng (freeze) CPU khi tắt màn hình. Trên Termux, bắt buộc phải kích hoạt `Acquire wakelock` và tắt tối ưu hóa pin (`Unrestricted Battery`) để Pocket Server duy trì kết nối cho máy X3 đọc truyện xuyên suốt. |
| **12** | **Cấu Hình Wi-Fi Hotspot 2.4 GHz & WPA2 Cho Xteink X3** | Chip Wi-Fi ESP32 của X3 chỉ hỗ trợ băng tần 2.4 GHz (không hỗ trợ 5.0 GHz) và tương thích tốt nhất với WPA2-Personal (WPA2-PSK). Khi phát Hotspot từ điện thoại, bắt buộc đặt AP Band = 2.4 GHz, Bảo mật = WPA2-Personal, tắt Wi-Fi 6, tắt PMF, và tắt VPN/AdGuard. |
| **13** | **Dải IP Hotspot Động Của Android (OEM Subnets: `10.x.x.x` trên `wlan2`)** | Nhiều smartphone 5G đời mới (Oppo, Realme, Vivo) không dùng `192.168.43.1` mà gán IP động như `10.59.53.37` cho Hotspot interface `wlan2`. Backend phải phân loại chính xác các card `wlan*`, `ap*`, `softap*` để in ra đúng IP Gateway thực tế cho người dùng nhập trên máy X3. |
| **14** | **Giải Phóng Port 8080 Cưỡng Chế Qua Linux Procfs Inode** | Khi khởi động lại server trên Termux, lệnh `pkill` thông thường có thể để lại socket treo. Cần quét inode trong `/proc/net/tcp` và gửi `SIGKILL` (`kill -9`) thẳng vào PID đang giữ port để triệt tiêu lỗi `Errno 98 address already in use`. |

---

## 🛠️ 3. BẢNG TỔNG HỢP LỖI THỰC TẾ & CÁCH XỬ LÝ (ERROR & RESOLUTION LOG)

| Mã lỗi | Hiện tượng lỗi | Nguyên nhân gốc rễ | Cách xử lý triệt để |
|:---:|---|---|---|
| **BUG-001** | Lỗi tải danh mục Home ngay khi kết nối IP | URL mục `Đọc Tiếp` chứa ký tự `&` chưa được escape (`?start=1&limit=50&sort=asc`), làm hỏng Expat XML parser. | Áp dụng `html.escape()` cho 100% URL trong tất cả các feed OPDS XML. |
| **BUG-002** | Danh sách chương bị đúp hậu tố `- tên-truyện` | Firmware CrossVi tự động ghép `" - " + entry.author` vào sau tiêu đề chương. | Lược bỏ thẻ `<author>` trong XML feed của các chương truyện. |
| **BUG-003** | Tên truyện dính nhãn `Đang viếtHotNew` | HTML scraper lấy text của cả thẻ span badge dính liền vào tên truyện. | Dùng Regex cắt bỏ toàn bộ chuỗi nhãn trạng thái ở đuôi tên truyện. |
| **BUG-004** | Mất danh sách các tập tải (chỉ hiện 1 chương) | Nguồn truyện trả về `total_chapters = 0`, khiến hệ thống tính nhầm là truyện có 1 chương. | Tự động phân tích pagination/danh sách chương để tính đúng tổng số chương, kèm cơ chế fallback `len(chapters)`. |
| **BUG-005** | Biểu tượng unicode bị lỗi hình thoi đen `` | Font chữ E-ink của X3 không có glyph cho emoji `⚡`, `➔`. | Thay thế bằng ký tự ASCII chuẩn `->` và nhãn chữ tiếng Việt rõ ràng. |
| **BUG-006** | Máy ảo macOS bị crash/treo kết nối với Termux | Tràn bit địa chỉ 64-bit `uintptr_t` trong `SDL2` event loop của simulator. | Thêm file patch `scripts/patch_crossvi.py` ép kiểu con trỏ an toàn khi build máy ảo desktop. |
| **BUG-007** | Lỗi 404 khi nhấn vào bộ truyện trên Web UI | Endpoint JSON không khớp route giữa `/api/book/{source}/{slug}` và `/chapters`. | Thêm route alias đồng thời trong `books.py` và nâng cấp Web UI với `Promise.allSettled`. |
| **BUG-008** | Android Doze Mode làm treo kết nối khi tắt màn hình | Android tự động kích hoạt Phantom Process Killer và cgroup background freeze. | Bật `Acquire wakelock`, khóa Recent Apps 🔒, và chọn Battery Unrestricted cho Termux. |
| **BUG-009** | Tràn và cắt tiêu đề chương thành `...` trên X3 | Đưa cả tên truyện vào thẻ `<title>` khiến độ dài vượt quá độ phân giải 792px. | Tách biệt: `<title>` chỉ chứa tên chương, `<author>` chứa tên truyện để X3 hiển thị 2 dòng. |
| **BUG-010** | Xung đột GCC 15 / C23 khi build CrossPoint trên WSL | Narrowing conversion và C23 bool keyword trong header bên thứ ba. | Thêm cờ `-Wno-narrowing`, `-Dmemcpy_P=memcpy`, và bọc kiểm tra chuẩn C23. |
| **BUG-011** | Lỗi tràn số nguyên 64-bit trong `HttpDownloader.cpp` trên macOS | Ép kiểu `size_t` 64-bit sang `int64_t` biến thành `-1`, khiến mọi request HTTP bị hủy. | Viết `patch_crossvi.py` sửa điều kiện kiểm tra kích thước `contentLength > 0 && static_cast<uint64_t>(contentLength) > sink.maxBytes`. |
| **BUG-012** | Lỗi mất ảnh bìa & metadata nguồn AkayTruyen | Scraper cũ chỉ tìm thẻ `h1` và `.story-thumb`, không lấy được OpenGraph `<meta>` và `.book-3d img`. | Nâng cấp scraper AkayTruyen bóc tách đa tầng OpenGraph/DOM, nâng cấp `cover_service` tự động thay thế placeholder. |
| **BUG-013** | File tải về lưu vào thư mục tên Tác Giả thay vì Tên Truyện | Firmware X3 tạo thư mục theo thẻ `<author><name>` trong OPDS feed tải sách. | Đổi thẻ `<author><name>` trong `build_book_volumes_feed` và `build_book_chapters_feed` thành tên truyện (`story.title`). |
| **BUG-014** | X3 báo lỗi kết nối khi bắt Wi-Fi Hotspot từ điện thoại | Hotspot phát băng tần 5.0 GHz (ESP32 chỉ hỗ trợ 2.4 GHz), WPA3-SAE gây lỗi bắt tay, hoặc nhập `ztruyen.local` bị Android chặn mDNS. | Đổi Hotspot sang 2.4 GHz, WPA2-Personal, tắt VPN, nhập trực tiếp IP Gateway hiển thị trên Termux. |
| **FEAT-001** | Menu chính rườm rà & không gõ được tiếng Việt không dấu | Menu cũ hiển thị lẫn lộn các kho nguồn và danh mục; bàn phím X3 không có bộ gõ tiếng Việt. | Tái cấu trúc Menu chính 8 mục tinh gọn theo nguồn hiện tại, lưu `active_source` trong SQLite, tích hợp `remove_accents` cho tìm kiếm. |

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
│   │   │   └── opds_builder.py     # Bộ tạo XML Atom/OPDS 1.2 chuẩn hóa cho X3 (clean titles, story subfolder)
│   │   ├── cache/                  # fast_cache.py (In-Memory TTL), metadata_repo.py (SQLite), cover_service.py
│   │   ├── domain/                 # Models, IDs, Vietnamese Sanitizer (remove_accents)
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
│   ├── patch_crosspoint_downloader.py # Vá logic download folder cho máy ảo WSL
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

### C. Dành cho máy ảo Simulator
- **Windows (WSL2/WSLg)**: Chạy phím tắt `run_crosspoint_x3.bat`.
- **macOS**: Chạy phím tắt 1-click `run_crossvi_x3.command`.

---

## 🎯 6. NHIỆM VỤ TRỌNG TÂM CHO PHIÊN TIẾP THEO (NEXT SESSION FOCUS)

1. **Kiểm thử thực tế trên máy đọc sách Xteink X3 vật lý**:
   - Bật Hotspot trên điện thoại Android (IP: `192.168.43.1:8080/opds`) hoặc kết nối chung mạng Wi-Fi (`192.168.1.15:8080/opds`).
   - Mở OPDS Browser trên X3 thật, duyệt các mục: Đọc tiếp, Chọn nguồn, Mới cập nhật, Tải chương.
   - Kiểm tra độ sắc nét và tốc độ tải thực tế trên màn hình e-ink thật.
2. **Nâng cấp gói cài đặt APK 1-Click (Roadmap Cấp 2)**:
   - Nghiên cứu đóng gói Backend thành file `.apk` độc lập (sử dụng Termux:GUI wrapper hoặc Kivy/Python-for-Android) để người dùng chỉ cần nhấn 1 nút là mở server.
3. **Quy trình làm việc chuẩn cho Agent tiếp theo**:
   - Trước khi commit: Chạy `python -m pytest backend/tests -v` (đảm bảo 36/36 tests PASS).
   - Commit và push lên `origin main`.
   - Hướng dẫn người dùng cập nhật trên điện thoại Termux bằng lệnh: `ztruyen-update`.
