# Quickstart & Validation Guide: Z-Truyen X3

**Feature**: `001-z-truyen-x3`  
**Date**: 2026-08-18  
**Status**: Draft  

---

## 1. Yêu Cầu Tiền Đề (Prerequisites)

- Máy tính phát triển / Server: macOS (Mac mini M4), Linux hoặc Windows.
- Python 3.12+ và Docker Desktop đã được cài đặt.
- Trình đọc kiểm thử:
  - Máy đọc sách vật lý **Xteink X3** chạy CrossVi 1.1.2 hoặc CrossPoint 1.5.0.
  - Hoặc **CrossVi Simulator / Calibre / KOReader** trên máy tính / điện thoại.

---

## 2. Khởi Chạy Local Backend (Quickstart Commands)

### 2.1. Chạy Trực Tiếp Bằng Python (Development Mode)

```bash
# 1. Đi vào thư mục backend
cd backend

# 2. Tạo virtualenv và cài đặt dependencies
python -m venv .venv
source .venv/bin/activate  # Trên Windows: .venv\Scripts\Activate.ps1
pip install -e .

# 3. Cài đặt Playwright browser (cho chế độ bypass anti-bot)
playwright install chromium

# 4. Khởi chạy server FastAPI
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

### 2.2. Chạy Qua Docker Compose (Production-like Mode)

```bash
# Khởi chạy toàn bộ hệ thống Z-Truyen Backend
docker compose up -d

# Kiểm tra log hoạt động
docker compose logs -f
```

---

## 3. Các Kịch Bản Kiểm Thử & Xác Nhận Tính Năng (Validation Scenarios)

### Kịch Bản 1: Kiểm Tra Healthcheck & API Cơ Bản
- **Lệnh**: `curl -s http://localhost:8080/healthz`
- **Kết quả kỳ vọng**: Trả về `{"status":"ok","version":"1.0.0"}` với HTTP Status 200 trong < 50ms.

---

### Kịch Bản 2: Kiểm Tra OPDS Root Feed
- **Lệnh**: `curl -s -H "Accept: application/atom+xml" http://localhost:8080/opds`
- **Kết quả kỳ vọng**: Trả về tài liệu XML chuẩn Atom Feed chứa các link điều hướng tới "Truyện Hot", "Mới Cập Nhật", "Thể Loại" và link Search OpenSearch Description.

---

### Kịch Bản 3: Kiểm Tra Cào Truyện & Tìm Kiếm Đa Nguồn
- **Lệnh**:
  - `curl -s "http://localhost:8080/opds/search?q=con+duong+ba+chu"`
  - `curl -s "http://localhost:8080/opds/search?q=linh+di&source=storyaclick"`
- **Kết quả kỳ vọng**: Trả về danh sách truyện khớp với từ khóa từ nguồn chỉ định, kèm metadata ảnh bìa và tóm tắt.

---

### Kịch Bản 4: Kiểm Tra Tạo File EPUB Volume Gom Chương & Đọc Thử
- **Thực hiện**:
  1. Gửi request tải Volume 1 bộ truyện:  
     `curl -s -o test_vol1.epub "http://localhost:8080/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_v01.epub"`
  2. Mở file `test_vol1.epub` bằng Calibre / KOReader / CrossVi Simulator.
- **Kết quả kỳ vọng**:
  - File EPUB mở tức thì, chứa đầy đủ mục lục 50 chương đầu tiên.
  - Văn bản chuẩn UTF-8 tiếng Việt, font hiển thị sạch, không có quảng cáo/rác.
  - Dung lượng file < 1MB.

---

### Kịch Bản 5: Kết Nối Thực Tế Từ Máy Đọc Sách Xteink X3
- **Thực hiện**:
  1. Bật Wi-Fi trên máy X3.
  2. Mở menu **OPDS Browser** trên CrossVi 1.1.2.
  3. Thêm máy chủ mới: `http://192.168.x.x:8080/opds` (hoặc URL Cloudflare Tunnel `https://ztruyen.yourdomain.com/opds`).
  4. Duyệt tìm truyện, chọn Volume 1 và bấm Download.
- **Kết quả kỳ vọng**:
  - X3 tải file về thư mục sách trên thẻ nhớ SD trong vài giây.
  - Mở đọc trơn tru trên E-ink, lật trang qua các chương liên tục không bị văng/crash.
