# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh hoạt động**: `main` (Đã dọn dẹp sạch sẽ, thuần khiết mã nguồn trên GitHub)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Bản sao lưu an toàn**: `Z-Truyen_backup_20260819_212332.zip` (5.40 MB)  
**Ngày cập nhật**: 2026-08-19  

---

## 🚀 1. TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **33/33 test cases PASS 100%** (`python -m pytest backend/tests -v`).
2. **Pocket Host Server trên Android (Termux)**:
   - Đã cài đặt và vận hành ổn định trên điện thoại Android thực tế (`aarch64`, Python 3.14).
   - Tích hợp lệnh khởi chạy `ztruyen` và lệnh tự động cập nhật code `ztruyen-update` (`android/update.sh`).
   - Đã xử lý triệt để hiện tượng Android Doze Mode / Background Freezing thông qua cơ chế `Acquire wakelock` và `Battery Unrestricted`.
3. **Cơ chế Đọc "Gần Như Online" & Nâng Cấp Giao Diện OPDS X3**:
   - **Quy tắc Firmware**: **100% Stock Factory Firmware** — Không can thiệp, vá hay sửa đổi firmware gốc của Xteink X3 / CrossPoint Simulator. Toàn bộ logic giao diện, phân loại, sắp xếp được xử lý chuẩn mực tại Backend OPDS 1.2 RFC.
   - **Tối ưu hiển thị danh sách chương (Chống tràn chữ/bị cắt `...`)**:
     - Thẻ `<title>`: Chỉ chứa `Chương X: Tên Chương` (hiển thị dòng 1 in đậm to).
     - Thẻ `<author>`: Chứa `{Tên Truyện}` (hiển thị dòng 2 nhỏ bên dưới).
     - Loại bỏ hoàn toàn prefix dài gây tràn 792px màn hình e-ink.
   - **Cấu trúc Trang chủ OPDS 7 Mục Chuẩn Hóa**:
     1. 📖 **Đọc Tiếp: {Tên Truyện} (Chương {X})**: Tự động ghi nhớ từ bảng SQLite `last_read`, dẫn thẳng vào danh sách chương đang đọc dở.
     2. 🌐 **Chọn Nguồn Truyện**: Lựa chọn kho truyện (`📚 Storya`, `🌟 AkayTruyen`, `⚔️ Con Đường Bá Chủ`).
     3. 📚 **Nguồn Hiện Tại: {Tên Nguồn}**: Hiển thị nguồn đang được kích hoạt.
     4. ⚡ **Truyện Mới Cập Nhật**.
     5. 🔥 **Truyện Hot & Đọc Nhiều**.
     6. ✅ **Truyện Hoàn Thành (Full Trọn Bộ)**.
     7. 📂 **Thể Loại Truyện**.
   - **Đa phương thức tải & gom tập**: Tải từng chương 0.3s, đọc ngay chương 1, tải trọn bộ All-in-One, tải tập gom 50 chương chuẩn hóa KOSync SHA-1.
   - **Tự động lưu thư mục theo tên truyện**: File EPUB tải về được lưu tại `downloads/{story_slug}/` và `data/epubs/{story_slug}/`.
   - **Khôi phục ảnh bìa gốc**: Liên kết ảnh bìa chuẩn OPDS `rel="http://opds-spec.org/image"`, hiển thị trực tiếp và mượt mà trên CrossPoint X3.
4. **Máy ảo Xteink X3 Native Virtual Machine trên WSL2/WSLg**:
   - Dùng mã nguồn sạch chuẩn [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) + [CrossPoint Simulator](https://github.com/crosspoint-reader/crosspoint-simulator).
   - Khởi chạy 1-Click: `run_crosspoint_x3.bat`, `run_x3_simulator.bat` hoặc `.\scripts\run_crosspoint_x3.ps1`.
   - Cấu hình qua `platformio.local.ini`, xử lý hoàn chỉnh các cờ tương thích GCC 15 (`-Wno-narrowing`, `-Dmemcpy_P=memcpy`, C23 bool check).

---

## 📂 2. CẤU TRÚC REPOSITORY ĐÃ DỌN DẸP SẠCH SẼ (CLEAN CODEBASE)

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
│   │   ├── api/                    # Routers: opds.py, books.py, chapters.py, search.py, web.py, health.py
│   │   │   └── opds_builder.py     # Bộ tạo XML Atom/OPDS 1.2 chuẩn hóa cho X3
│   │   ├── cache/                  # metadata_repo.py (SQLite + last_read), object_storage.py, cover_service.py
│   │   ├── domain/                 # Models, IDs, Vietnamese Sanitizer
│   │   ├── epub/                   # EPUB Builder, Volume Bundler (KOSync SHA-1)
│   │   ├── fetcher/                # HTTP Client, Session, Headless fallback
│   │   ├── network/                # mDNS auto-discovery (ztruyen.local)
│   │   └── sources/                # Registry & Adapters: storyaclick, akaytruyen, conduongbachu
│   ├── tests/                      # 33 Integration & Unit tests (100% PASS)
│   ├── Dockerfile & docker-compose.yml
│   └── pyproject.toml
├── docs/                            # Tài liệu dự án đầy đủ
│   ├── ANDROID_SMARTPHONE_HOST_GUIDE.md     # Hướng dẫn cài đặt & vận hành trên điện thoại
│   ├── CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md# Hướng dẫn máy ảo CrossPoint Simulator
│   ├── FIELD_TEST_AND_DEBUG_LOG.md          # Nhật ký 10 lỗi thực tế & bài học kinh nghiệm
│   └── TESTING.md & WINDOWS_TEST_GUIDE.md   # Hướng dẫn test trên Windows & WSL
├── scripts/                         # Scripts công cụ dev & launcher máy ảo
│   ├── configure_sim_ini.py        # Thiết lập platformio.local.ini cho simulator
│   ├── patch_simulator.py          # Vá stub GCC 15 / C23 cho simulator
│   ├── run_crosspoint_x3.ps1       # Script PowerShell chạy máy ảo
│   └── run-dev.ps1 / run-dev.sh    # Khởi chạy dev backend
├── specs/001-z-truyen-x3/          # Đặc tả kiến trúc kỹ thuật chuẩn
├── .gitignore                       # Chặn file rác, caches, logs, .claude, .specify, .agents
├── memory.md                        # Bộ nhớ dự án & hướng dẫn chuyển phiên
├── README.md                        # Hướng dẫn tổng quan dự án
├── run_crosspoint_x3.bat            # Phím tắt chạy máy ảo X3 trên Windows
├── run_x3_simulator.bat            # Phím tắt chạy máy ảo X3 trên Windows
└── start-ztruyen.ps1                # Phím tắt khởi động backend trên Windows
```

---

## 💡 3. ĐÚC KẾT BÀI HỌC KINH NGHIỆM TRỌNG TÂM (KEY LESSONS LEARNED)

| STT | Bài học kinh nghiệm | Chi tiết & Nguyên tắc |
|:---:|---|---|
| **1** | **Nguyên tắc Stock Firmware** | Tuyệt đối **KHÔNG** chỉnh sửa mã nguồn firmware của Xteink X3 / CrossPoint Reader. Mọi tính năng trình bày, phân trang, gom tập phải được hiện thực hoàn toàn phía Backend OPDS 1.2 RFC. |
| **2** | **Bố cục hiển thị E-ink 792px** | Đặt tên chương ở `<title>` (`Chương 1: Khởi Đầu`) và tên truyện ở `<author>` (`Mục Thần Ký`). Firmware sẽ hiển thị Dòng 1 to đậm và Dòng 2 nhỏ bên dưới, không bao giờ bị cắt ngắn thành `...`. |
| **3** | **Cơ chế Đọc Tiếp (Continue Reading)** | Bảng SQLite `last_read` lưu truyện và chương vừa thao tác. Feed `/opds` tự động đưa `📖 Đọc Tiếp: {Tên Truyện}` lên đầu để người dùng 1-click vào thẳng chương đọc dở. |
| **4** | **Quản lý tiến trình nền Android** | Cần kích hoạt `Acquire wakelock` trên Termux và đặt Battery sang `Unrestricted` để Android không đóng băng tiến trình CPU khi tắt màn hình. |
| **5** | **Biên dịch Native CrossPoint trên WSL** | Dùng `sample-platformio-linux-wsl.ini` copy sang `platformio.local.ini` (không sửa `platformio.ini` gốc). Thêm `-Wno-narrowing`, `-Dmemcpy_P=memcpy`, và bọc C23 bool check cho thư viện `QRCode`. |

---

## 🎯 4. NHIỆM VỤ TRỌNG TÂM CHO PHIÊN TIẾP THEO (NEXT SESSION FOCUS)

1. **Kiểm thử thực tế trên máy đọc sách Xteink X3 vật lý**:
   - Bật Hotspot trên điện thoại Android (IP: `192.168.43.1:8080/opds`) hoặc kết nối chung mạng Wi-Fi.
   - Mở OPDS Browser trên X3 thật, duyệt các mục: Đọc tiếp, Chọn nguồn, Mới cập nhật, Tải chương.
   - Kiểm tra độ sắc nét và tốc độ tải thực tế trên màn hình e-ink thật.
2. **Nâng cấp gói cài đặt APK 1-Click (Roadmap Cấp 2)**:
   - Nghiên cứu đóng gói Backend thành file `.apk` độc lập (sử dụng Termux:GUI wrapper hoặc Kivy/Python-for-Android) để người dùng chỉ cần nhấn 1 nút là mở server.
3. **Quy trình làm việc chuẩn cho Agent tiếp theo**:
   - Trước khi commit: Chạy `python -m pytest backend/tests -v` (đảm bảo 33/33 tests PASS).
   - Commit và push lên `origin main`.
   - Hướng dẫn người dùng cập nhật trên điện thoại Termux bằng lệnh: `ztruyen-update`.
