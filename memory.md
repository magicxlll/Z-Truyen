# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh tính năng**: `001-z-truyen-x3` (Đồng bộ chính thức trên nhánh `main`)  
**GitHub Repository**: [https://github.com/magicxlll/Z-Truyen.git](https://github.com/magicxlll/Z-Truyen.git)  
**Ngày cập nhật**: 2026-08-19  

---

## 🚀 1. TRẠNG THÁI HIỆN TẠI (CURRENT PROJECT STATE)

1. **Kiểm thử toàn diện**: **28/28 test cases PASS 100%** (`python -m pytest tests -v`).
2. **Pocket Host Server trên Android (Termux)**:
   - Đã cài đặt và vận hành ổn định trên điện thoại Android thực tế (`aarch64`, Python 3.14).
   - Tích hợp lệnh khởi chạy `ztruyen` và lệnh tự động cập nhật code không xung đột `ztruyen-update` (`android/update.sh`).
   - Đã xử lý triệt để hiện tượng Android Doze Mode / Background Freezing thông qua cơ chế `Acquire wakelock` và `Battery Unrestricted`.
3. **Cơ chế Đọc "Gần Như Online" (Near-Online Streaming Engine)**:
   - **Tải tức thì 0.3s/chương**: Tạo file EPUB 1 chương siêu nhẹ (15 - 30KB).
   - **Tải ngầm 3 chương tiếp theo (Background Prefetch)**: Tự động cào và nén sẵn chương $N+1, N+2, N+3$ vào cache ngầm khi người dùng đọc chương $N$.
   - **Dọn dẹp bộ nhớ thông minh (Smart Cache)**: Tự động xóa các chương cũ hơn 5 chương phía trước ($< N - 5$) để không đầy bộ nhớ điện thoại.
   - **Đa dạng hình thức tải**: Tải 1 chương lẻ (`32`), tải gom khoảng chương tùy chọn (`1-32`), tải trọn bộ (`ALL`), và tải tập gom sẵn 50 chương/tập.
4. **Bộ lọc & Phân loại đa nguồn**:
   - Chọn nguồn: `Tất cả nguồn`, `Storya.click`, `AkayTruyen`, `Con Đường Bá Chủ`.
   - Bộ lọc danh mục: `🔥 Truyện Hot`, `⚡ Mới Cập Nhật`, `✅ Hoàn Thành (Full Trọn Bộ)`.
   - Sắp xếp chương: `⬆️ Từ đầu (1 ➔ N)` $\leftrightarrow$ `⬇️ Mới nhất (N ➔ 1)`.
5. **Máy ảo Xteink X3 Simulator 1-Click trên Windows Desktop**:
   - Khởi chạy 1-click qua `run_x3_simulator.bat` (Python native UTF-8).
   - Kết nối trực tiếp qua IP Wi-Fi/Hotspot của điện thoại (hoặc localhost).
   - Tự động lưu file EPUB tải về vào thư mục `downloads/`.
   - Tích hợp trình đọc E-ink Terminal Reader trực tiếp (lật trang bằng Enter / N / P).

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
               │  - Máy ảo PC: run_x3_simulator.bat                      │
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
   - Khi sửa code, luôn chạy test: `python -m pytest tests -v` (đảm bảo 28/28 tests PASS).
   - Tự động `git add`, `git commit` và `git push origin main`.
   - Báo người dùng cập nhật trên điện thoại bằng đúng 1 lệnh: `ztruyen-update`.
