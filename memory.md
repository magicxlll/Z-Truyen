# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh tính năng**: `001-z-truyen-x3` (Đồng bộ chính thức trên nhánh `main`)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Ngày cập nhật**: 2026-08-19  

---

## 🚀 1. TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **33/33 test cases PASS 100%** (`python -m pytest backend/tests -v`).
2. **Pocket Host Server trên Android (Termux)**:
   - Đã cài đặt và vận hành ổn định trên điện thoại Android thực tế (`aarch64`, Python 3.14).
   - Tích hợp lệnh khởi chạy `ztruyen` và lệnh tự động cập nhật code không xung đột `ztruyen-update` (`android/update.sh`).
   - Đã xử lý triệt để hiện tượng Android Doze Mode / Background Freezing thông qua cơ chế `Acquire wakelock` và `Battery Unrestricted`.
3. **Cơ chế Đọc "Gần Như Online" & Nâng Cấp Giao Diện X3**:
   - **Chọn Nguồn Truyện lên trên cùng**: Giao diện OPDS Root đưa `🌐 Chọn Nguồn Truyện` và danh sách từng kho truyện (`📚 Storya`, `🌟 AkayTruyen`, `⚔️ Con Đường Bá Chủ`) lên vị trí đầu tiên, loại bỏ các từ ngữ kỹ thuật như "nguồn cào".
   - **Đa phương thức tải & Liệt kê toàn bộ chương**: Feed chi tiết sách cung cấp đầy đủ các tùy chọn:
     - ⚡ *Đọc Từng Chương (1 ➔ N & N ➔ 1)*: Liệt kê toàn bộ danh sách chương để tải tức thì 0.3s/chương.
     - 📖 *Đọc Ngay Chương 1*: Tải 1-click chương mở đầu.
     - 📥 *Tải Trọn Bộ (Full ALL)*: Nén tất cả chương thành 1 file EPUB hoàn chỉnh.
     - 📦 *Tập Gom Sẵn (50 chương/tập)*: Các tập phân đoạn tối ưu cho KOSync.
   - **Tải ngầm thông minh & Hộp thoại Đọc Ngay (Y/N)**:
     - Tải 1 chương $\rightarrow$ Tự động tải ngầm 3 chương tiếp theo và dọn dẹp 5 chương cũ phía trước.
     - Web UI có thông báo tiến trình `⏳ Đang cào & nén...` và hộp thoại xác nhận `✅ Tải về hoàn tất! Bạn có muốn mở đọc ngay bây giờ không? [📖 Đọc Ngay] [✖ Để Sau]`.
   - **Tự động tạo folder theo tên truyện**: Toàn bộ file EPUB tải về được tự động phân loại và lưu trong thư mục con riêng theo tên truyện (`downloads/{story_slug}/` và `data/epubs/{story_slug}/`).
   - **Proxy tối ưu hóa bìa truyện cho E-ink**:
     - Endpoint `/opds/cover/{source}/{slug}` tự động chuyển đổi định dạng ảnh (WebP, PNG $\rightarrow$ Standard JPEG), tương thích 100% với bộ giải mã `JPEGDEC` trên CrossPoint X3 và KOReader.
     - Tự động tăng độ tương phản và căn chỉnh kích thước (240x360), giúp bìa truyện hiển thị sắc nét ở 16 mức xám E-ink.
4. **Máy ảo Xteink X3 Đồ họa Thật (CrossPoint Reader Native Virtual Machine trên WSL2/WSLg)**:
   - Sử dụng mã nguồn chính thức [CrossPoint Reader](https://github.com/crosspoint-reader/crosspoint-reader) + [CrossPoint Simulator](https://github.com/crosspoint-reader/crosspoint-simulator).
   - Khởi chạy 1-Click qua `run_crosspoint_x3.bat`, `run_x3_simulator.bat`, hoặc `.\scripts\run_crosspoint_x3.ps1`.
   - Hiển thị cửa sổ đồ họa E-ink thực thụ (792 × 528 pixel) trực tiếp trên Windows Desktop qua WSLg.
   - Hỗ trợ đầy đủ phím cứng (D-pad Mũi tên, Enter/Space, ESC/Back, Nguồn P) và cảm ứng chuột.
   - Tự động nạp sẵn cấu hình OPDS (`http://127.0.0.1:8080/opds`, `http://<WSL_GATEWAY>:8080/opds`, `http://192.168.43.1:8080/opds`) và Font tiếng Việt `Ubuntu-Vietnamese`.

---

## 📚 2. BẢN ĐỒ TÀI LIỆU QUAN TRỌNG (NEXT AGENT MUST READ FIRST)

| STT | Tài liệu trọng tâm | Đường dẫn file | Nội dung & Mục đích tham chiếu |
|:---:|---|---|---|
| 1 | **Nhật ký Debug & Bài học kinh nghiệm** | [`docs/FIELD_TEST_AND_DEBUG_LOG.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/FIELD_TEST_AND_DEBUG_LOG.md) | **ĐỌC ĐẦU TIÊN**: Tổng hợp 8 lỗi thực tế (BUG-001 đến BUG-008), phân tích hiệu năng nền Android, giải pháp khắc phục triệt để. |
| 2 | **Hướng dẫn Android Host Server** | [`docs/ANDROID_SMARTPHONE_HOST_GUIDE.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/ANDROID_SMARTPHONE_HOST_GUIDE.md) | Hướng dẫn cài đặt Termux, phím tắt `ztruyen`, `ztruyen-update`, cấu hình WakeLock, Hotspot IP `192.168.43.1`. |
| 3 | **Hướng dẫn Máy ảo X3 Simulator** | [`docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md) | Hướng dẫn chạy máy ảo X3 trên Windows, kết nối IP và đọc truyện. |
| 4 | **Đặc tả Kỹ thuật & Yêu cầu** | [`specs/001-z-truyen-x3/spec.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/spec.md) | Chuẩn OPDS 1.2, 3 Nguồn truyện (`storyaclick`, `akaytruyen`, `conduongbachu`), KOSync SHA-1. |

---

## 🏛️ 3. Tóm Tắt Kiến Trúc Kỹ Thuật Đã Triển Khai

```text
               ┌─────────────────────────────────────────────────────────┐
               │              SMARTPHONE ANDROID (POCKET HOST)           │
               │                                                         │
               │  - App Termux: FastAPI + SQLite + Background Tasks      │
               │  - Single-Chapter Streaming + Auto Prefetch Next 3 Ch   │
               │  - Smart Cache Cleanup (giữ bộ nhớ máy luôn gọn nhẹ)    │
               │  - WakeLock Held: Chạy ngầm liên tục khi tắt màn hình   │
               │  - Lắng nghe: 0.0.0.0:8080                              │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                  HTTP OPDS │ (Port 8080)
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │        XTEINK X3 (MÁY THẬT HOẶC MÁY ẢO WINDOWS)         │
               │                                                         │
               │  - Máy thật: OPDS Browser CrossVi 1.1.2 / KOReader      │
               │  - Máy ảo PC: run_crosspoint_x3.bat (CrossPoint VM GUI) │
               │  - Duyệt Hot/New/Full, lọc theo Nguồn                   │
               │  - Tải từng chương lẻ (0.3s) / Gom 1-32 / Gom Trọn Bộ   │
               │  - Tải Tập 50 chương chuẩn hóa KOSync SHA-1             │
               └─────────────────────────────────────────────────────────┘
```

---

## 🎯 4. Nhiệm Vụ Trọng Tâm Cho Phiên Tiếp Theo (Next Session Focus)

1. **Test thực tế trên máy đọc sách Xteink X3 thật**:
   - Kết nối máy X3 thật vào Wi-Fi hoặc Điểm phát sóng di động (Hotspot) của điện thoại Android.
   - Nhập URL: `http://ztruyen.local:8080/opds` hoặc `http://192.168.43.1:8080/opds` trên OPDS Browser của CrossVi / KOReader.
   - Kiểm tra tốc độ duyệt và hiển thị bìa sách trên màn hình E-ink thật.
2. **Nâng cấp gói cài đặt 1-Click APK (Roadmap Cấp 2)**:
   - Nghiên cứu đóng gói Z-Truyen Backend thành file `.apk` độc lập (sử dụng Python-for-Android / Kivy / Termux GUI wrapper) để người dùng không chuyên chỉ cần bấm 1 nút là mở server.
3. **Quy trình làm việc chuẩn cho Agent**:
   - Khi sửa code, luôn chạy test: `python -m pytest backend/tests -v` (đảm bảo 28/28 tests PASS).
   - Tự động `git add`, `git commit` và `git push origin main`.
   - Báo người dùng cập nhật trên điện thoại bằng đúng 1 lệnh: `ztruyen-update`.
