# Z-Truyen X3 — Project Memory & Agent Handoff Guide

**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration for Xteink X3 & Android Pocket Host)  
**Nhánh tính năng**: `001-z-truyen-x3`  
**Ngày cập nhật**: 2026-08-19  
**Trạng thái hiện tại**:
1. **Backend Engine**: Hoàn thành 100% toàn bộ 38/38 tasks theo `specs/001-z-truyen-x3/tasks.md`. Toàn bộ 24/24 unit tests & integration tests đều đạt 100% PASS.
2. **Máy ảo Xteink X3 (Desktop Simulator)**: Đã thiết lập hoàn chỉnh trên WSL2 Ubuntu + C++ SDL2, có sẵn launcher 1-click `run_crosspoint_x3.bat` để test trực tiếp trên Windows.
3. **Pocket Host Server trên Android**: Đã tích hợp mDNS Zeroconf (`ztruyen.local:8080`), tạo bộ script tự động hóa cho Android Termux (`android/setup-termux.sh`, `android/start-server.sh`) và gói nén `ztruyen-android.zip`.
4. **Giai đoạn hiện tại của Người dùng**: Người dùng đang cài đặt lên điện thoại Android thực tế và chuẩn bị test kết nối với Xteink X3. **Phiên tiếp theo sẽ tập trung vào test lỗi, xử lý ngoại lệ và debug phát sinh từ môi trường Android/X3 thực tế.**

---

## 📚 1. BẢN ĐỒ TÀI LIỆU QUAN TRỌNG (NEXT AGENT MUST READ FIRST)

> ⚠️ **LƯU Ý DÀNH CHO AGENT PHIÊN SAU**: 
> Không cần đọc lại toàn bộ code từ đầu! Hãy đọc nhanh 4 file tài liệu dưới đây theo thứ tự để nắm trọn 100% ngữ cảnh dự án trong 30 giây:

| STT | Tài liệu trọng tâm | Đường dẫn file | Nội dung & Mục đích tham chiếu |
|:---:|---|---|---|
| 1 | **Hướng dẫn Android Host Server** | [`docs/ANDROID_SMARTPHONE_HOST_GUIDE.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/ANDROID_SMARTPHONE_HOST_GUIDE.md) | **ĐỌC ĐẦU TIÊN**: Cấu hình Android Termux, phím tắt `ztruyen`, mDNS `ztruyen.local`, Hotspot IP `192.168.43.1`, cách sửa lỗi khi người dùng báo lỗi trên điện thoại. |
| 2 | **Hướng dẫn Máy ảo X3 Desktop** | [`docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/CROSSPOINT_X3_VIRTUAL_DEVICE_GUIDE.md) | Cách vận hành CrossPoint Simulator trên Windows, phím điều khiển, cách test kết nối OPDS từ máy ảo vào điện thoại Android. |
| 3 | **Hướng dẫn Kiểm thử 4 Phương pháp** | [`docs/TESTING_VIRTUAL_ENV_GUIDE.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/docs/TESTING_VIRTUAL_ENV_GUIDE.md) | 4 công cụ test: Terminal CLI Simulator (`scripts/opds_simulator.py`), Web UI (`http://localhost:8080/`), Desktop X3 Simulator, và E-reader thật. |
| 4 | **Đặc tả Kỹ thuật & Yêu cầu** | [`specs/001-z-truyen-x3/spec.md`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/specs/001-z-truyen-x3/spec.md) | Kiến trúc OPDS 1.2, 3 Nguồn truyện (`storyaclick`, `akaytruyen`, `conduongbachu`), quy tắc gom tập 50 chương/EPUB, KOSync SHA-1. |

---

## 🏛️ 2. Tóm Tắt Kiến Trúc Kỹ Thuật Đã Hoàn Thiện

```text
               ┌─────────────────────────────────────────────────────────┐
               │              SMARTPHONE ANDROID (HOST SERVER)           │
               │                                                         │
               │  - App Termux: Chạy Z-Truyen Backend (FastAPI + SQLite) │
               │  - Module mDNS Zeroconf: Broadcast ztruyen.local:8080   │
               │  - Lắng nghe: 0.0.0.0:8080                              │
               │  - Hotspot IP: 192.168.43.1 / Wi-Fi IP: 192.168.1.xxx   │
               └────────────────────────────┬────────────────────────────┘
                                            │
                                  HTTP OPDS │ (Port 8080)
                                            ▼
               ┌─────────────────────────────────────────────────────────┐
               │        XTEINK X3 (MÁY THẬT HOẶC MÁY ẢO WINDOWS)         │
               │                                                         │
               │  - Firmware: CrossVi 1.1.2 / CrossPoint Reader          │
               │  - OPDS Browser URL: http://ztruyen.local:8080/opds     │
               │       (hoặc: http://192.168.43.1:8080/opds)             │
               │  - Tải EPUB tiếng Việt sạch, chuẩn hóa KOSync           │
               └─────────────────────────────────────────────────────────┘
```

### Các Thành Phần Mã Nguồn Cốt Lõi:
- **Backend API & OPDS Engine** (`backend/app/api/`):
  - `opds.py`: Cung cấp Root feed, `/hot`, `/latest`, `/genres`, `/sources` và các alias `/catalog/hot`, `/catalog/new`.
  - `books.py`: Cung cấp danh sách tập (Volume Bundles 50 chương/tập) và hỗ trợ cả URL URN `source:slug`.
  - `chapters.py`: Gateway tải file EPUB on-the-fly (`/opds/download/{source_id}/{slug}/{filename}`).
  - `search.py`: Tìm kiếm truyện đa nguồn với URL-encoded queries.
  - `web.py`: Web Test Catalog trực quan tại `http://localhost:8080/`.
- **Hybrid Scraper Engine** (`backend/app/sources/`):
  - `storyaclick.py`: REST JSON API scraper.
  - `akaytruyen.py`: HTML scraper + VIP chapter session.
  - `conduongbachu.py`: WordPress REST API (4 categories: Chính truyện & 3 Ngoại truyện).
  - `backend/app/fetcher/client.py`: Async httpx client + Playwright Stealth fallback khi gặp Cloudflare Turnstile.
- **EPUB Builder & Bundler** (`backend/app/epub/`):
  - `builder.py`: Sinh XHTML sạch `<p id="p-N">`, tạo file EPUB tất định tương thích KOSync SHA-1.
  - `bundler.py`: Dynamic Volume Bundling (50 chương/EPUB), cơ chế chống race condition với build locks.
- **Service Discovery** (`backend/app/network/`):
  - `mdns.py`: Tự động phát mDNS broadcast `ztruyen.local:8080` trên cả Wi-Fi và Hotspot.
- **Android Automation** (`android/`):
  - `setup-termux.sh`: 1-line setup cho Termux Android.
  - `start-server.sh`: Runner script với `termux-wake-lock`, tự hiển thị IP và dọn dẹp pin khi tắt (`Ctrl + C`).
  - `ztruyen-android.zip`: Gói nén cài đặt sẵn ở thư mục gốc.
- **Desktop X3 Simulator** (`run_crosspoint_x3.bat`):
  - Khởi chạy cửa sổ E-ink Xteink X3 (792 × 528) qua WSL2 Ubuntu.

---

## 🎯 3. Nhiệm Vụ Trọng Tâm Cho Phiên Tiếp Theo (Next Session Focus)

Khi người dùng quay lại trong phiên tiếp theo, Agent thực hiện các nội dung sau:

1. **Tiếp nhận phản hồi và lỗi test từ người dùng**:
   - Nếu lỗi liên quan đến **cài đặt Termux trên Android**: Kiểm tra `requirements-termux.txt`, cấp quyền bộ nhớ `termux-setup-storage` hoặc thư viện biên dịch `clang/make`.
   - Nếu lỗi liên quan đến **kết nối mạng X3 -> Android**: Hướng dẫn dùng IP Hotspot cố định `http://192.168.43.1:8080/opds` hoặc kiểm tra port 8080.
   - Nếu lỗi liên quan đến **cào truyện cụ thể từ 3 nguồn**: Kiểm tra log Termux, tối ưu hóa parser hoặc cập nhật selector của nguồn đó.
2. **Kiểm tra tính toàn vẹn của mã nguồn**:
   - Luôn chạy lại test suite: `python -m pytest tests -v` (đảm bảo 24/24 tests pass) khi thực hiện bất kỳ sửa đổi nào.
3. **Giữ vững nguyên tắc cốt lõi**:
   - Không can thiệp sửa đổi firmware X3 (0% brick risk).
   - Duy trì cấu trúc thư mục độc lập trong `backend/` và `android/`.
