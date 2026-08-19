# Hướng Dẫn Thiết Lập Môi Trường Ảo & Kiểm Thử Z-Truyen X3 Trên Windows & macOS

Tài liệu này cung cấp hướng dẫn từng bước chi tiết để thiết lập các môi trường ảo (Container / Virtualenv / E-Reader Emulator) nhằm kiểm thử trọn vẹn toàn bộ hệ thống Backend, luồng cào truyện, tạo file EPUB gom tập (50 chương/quyển) và đồng bộ đọc sách OPDS 1.2 trên **Windows** và **macOS** mà không cần sở hữu máy đọc sách vật lý ngay lập tức.

---

## 🎯 4 Phương Pháp Kiểm Thử Môi Trường Ảo

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Z-TRUYEN X3 BACKEND                             │
│                  (FastAPI + SQLite WAL + Scrapers)                     │
│                       http://localhost:8080                            │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
       ┌───────────────────────────┼───────────────────────────┐
       ▼                           ▼                           ▼
[1. KOReader Desktop]      [2. OPDS Simulator]        [3. Web Test UI]
  Mô phỏng 100% E-ink        Mô phỏng thiết bị          Giao diện Web
  X3 & CrossVi 1.1.2         OPDS qua Terminal          trên Browser
```

---

## PHƯƠNG PHÁP 1: Giả Lập Trực Quan Bằng KOReader Desktop (Khuyên Dùng Nhất 🌟)

KOReader là phần mềm đọc sách mã nguồn mở chạy chính xác cùng nhân rendering với máy đọc sách E-ink. Cài đặt KOReader Desktop trên Windows/macOS sẽ giúp bạn trải nghiệm **100% giao diện, thao tác duyệt OPDS, tải sách và lật trang giống như trên máy Xteink X3 thật**.

### 1.1. Cài Đặt KOReader Desktop

#### Trên Windows:
1. Tải bản cài đặt KOReader cho Windows (`koreader-windows-x86_64-v...zip` hoặc `.exe`) từ [KOReader GitHub Releases](https://github.com/koreader/koreader/releases).
2. Giải nén và mở file `koreader.exe`.

#### Trên macOS:
- Cài đặt nhanh qua Homebrew:
  ```bash
  brew install --cask koreader
  ```
- Hoặc tải file `.dmg` từ [KOReader GitHub Releases](https://github.com/koreader/koreader/releases) và kéo vào thư mục `Applications`.

---

### 1.2. Kết Nối KOReader Tới Server Z-Truyen

1. **Khởi động Backend**:
   - Mở terminal chạy:
     ```bash
     # Trên Windows (PowerShell):
     .\scripts\run-dev.ps1

     # Trên macOS:
     ./scripts/run-dev.sh
     ```
   *(Server sẵn sàng tại `http://localhost:8080`)*

2. **Cấu hình trên KOReader**:
   - Bấm vào biểu tượng **Kính Lúp / Thư viện (Search & Library)** ở menu trên cùng.
   - Chọn mục **OPDS Catalog (Danh mục OPDS)**.
   - Chọn **Thêm máy chủ mới (Add new catalog)**:
     - **Tên (Title)**: `Z-Truyen Local`
     - **Địa chỉ (URL)**: `http://localhost:8080/opds` (hoặc `http://127.0.0.1:8080/opds`)
   - Bấm **Lưu (Save)**.

3. **Trải nghiệm**:
   - Chọn vào thư mục **Z-Truyen Local**: Bạn sẽ thấy các mục:
     - 🔥 **Truyện Hot & Đọc Nhiều**
     - ⚡ **Mới Cập Nhật**
     - 📂 **Thể Loại Truyện**
     - 🔍 **Tìm Kiếm Truyện**
   - Tìm kiếm truyện (ví dụ: *Con Đường Bá Chủ*), chọn bộ truyện -> chọn **Tập 01 (Chương 1-50)** -> bấm **Download**.
   - Sách được tải xong sẽ mở ngay trên màn hình đọc với định dạng chữ rõ nét, thụt lề chuẩn và phân đoạn `<p id="p-N">`!

---

## PHƯƠNG PHÁP 2: Giả Lập Thiết Bị OPDS Bằng Terminal Simulator (`opds_simulator.py`)

Nếu bạn muốn kiểm tra nhanh luồng API, tốc độ cào, độ hợp lệ của EPUB, mã băm SHA-1 KOSync ngay trong cửa sổ dòng lệnh:

### Cách Chạy:
```bash
# Đảm bảo môi trường Python đã kích hoạt
python scripts/opds_simulator.py
```

### Các Tính Năng Đã Tích Hợp Sẵn Trong Simulator:
1. **Kiểm tra Healthcheck**: Tự động ping `/healthz` kiểm tra trạng thái máy chủ.
2. **Duyệt Feed Atom XML**: Tự động parse các feed `/opds/hot`, `/opds/latest`, `/opds/genres`, `/opds/sources`.
3. **Tìm kiếm truyện đa nguồn**: Gõ từ khóa tìm kiếm trên cả 3 nguồn truyện.
4. **Tải và Xác Minh File EPUB**:
   - Đóng gói file EPUB theo thời gian thực.
   - Kiểm tra mã băm `X-KOSync-SHA1`.
   - Phân tích cấu trúc file `.epub` bên trong: Metadata tiêu đề, tác giả, số lượng chương trong tập và độ chuẩn hóa XHTML.

---

## PHƯƠNG PHÁP 3: Môi Trường Máy Ảo Cô Lập Qua Docker Container

Chạy Backend hoàn toàn biệt lập bên trong Docker Container (Linux Alpine/Debian) trên Windows WSL2 hoặc macOS Docker Desktop.

### 3.1. Thiết Lập & Khởi Chạy
```bash
# 1. Đi vào thư mục backend
cd backend

# 2. Khởi tạo cấu hình môi trường
cp .env.example .env

# 3. Khởi chạy container cô lập
docker compose up -d --build

# 4. Xem logs hoạt động thời gian thực
docker compose logs -f backend
```

### 3.2. Kiểm Tra Trạng Thái Container
```bash
docker compose ps
curl http://localhost:8080/healthz
```

---

## PHƯƠNG PHÁP 4: Giao Diện Web Test Trực Tiếp Trên Trình Duyệt

Mở trình duyệt bất kỳ (Chrome, Safari, Edge, Firefox) và truy cập:
👉 **`http://localhost:8080/`** (hoặc **`http://localhost:8080/web`**)

- Giao diện Dark Mode hiện đại hiển thị toàn bộ truyện, ảnh bìa, nhãn nguồn.
- Thanh tìm kiếm hỗ trợ lọc theo từng nguồn hoặc tìm kiếm toàn bộ.
- Bấm vào bất kỳ truyện nào để xem danh sách các tập và bấm **"📥 Tải EPUB"** để lưu file về máy tính.

---

## 📋 TỔNG HỢP CÁC LỆNH KIỂM THỬ NHANH

| Mục đích | Lệnh chạy (Windows PowerShell) | Lệnh chạy (macOS / Linux) |
|---|---|---|
| **Cài đặt tự động môi trường** | `.\scripts\setup-windows.ps1` | `./scripts/setup-macos.sh` |
| **Khởi chạy Backend dev** | `.\scripts\run-dev.ps1` | `./scripts/run-dev.sh` |
| **Chạy máy ảo Terminal Simulator** | `python scripts/opds_simulator.py` | `python3 scripts/opds_simulator.py` |
| **Chạy toàn bộ 22 Tests** | `cd backend; pytest` | `cd backend && pytest` |
| **Chạy Docker Cô lập** | `cd backend; docker compose up -d` | `cd backend && docker compose up -d` |
| **Mở Web UI Test** | `Start-Process http://localhost:8080` | `open http://localhost:8080` |
