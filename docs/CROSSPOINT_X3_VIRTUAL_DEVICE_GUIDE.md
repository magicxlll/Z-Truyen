# Hướng Dẫn Sử Dụng Máy Ảo Xteink X3 (CrossPoint Reader Desktop Simulator)

Tài liệu này hướng dẫn cách khởi chạy và kiểm thử toàn diện **Máy ảo thiết bị E-reader Xteink X3** (chạy firmware CrossPoint Reader) trực tiếp trên máy tính của bạn để tương thích 100% với hệ thống Z-Truyen.

---

## 🚀 1. Cách Khởi Chạy 1-Click

Hệ thống đã tự động cài đặt và biên dịch sẵn toàn bộ môi trường Simulator trên máy của bạn (WSL2 Ubuntu + C++ + SDL2 + CrossPoint Firmware).

### Cách chạy nhanh:
1. Mở thư mục dự án `Z-Truyen`.
2. Nhấp đúp chuột (Double-click) vào file:
   👉 **`run_crosspoint_x3.bat`** (ngay tại thư mục gốc dự án)
3. Cửa sổ E-ink của máy Xteink X3 sẽ tự động mở lên trên màn hình máy tính của bạn!

*(Hoặc chạy qua PowerShell: `.\scripts\run_crosspoint_x3.ps1`)*

---

## 🎮 2. Bàn Phím Điều Khiển Máy Ảo X3

| Thao tác trên máy X3 thật | Phím bấm trên máy tính | Chức năng |
| :--- | :--- | :--- |
| **D-Pad Lên / Xuống** | `Mũi tên Lên` / `Mũi tên Xuống` | Di chuyển lên/xuống danh mục truyện/menu |
| **D-Pad Trái / Phải** | `Mũi tên Trái` / `Mũi tên Phải` | Lật trang trước / Lật trang sau |
| **Nút Chọn (OK / Center)** | `Enter` hoặc `Space` | Chọn mục, mở sách, xác nhận tải |
| **Nút Trở Lại (Back)** | `ESC` hoặc `Backspace` | Quay lại màn hình / menu trước |
| **Nút Nguồn (Power)** | Phím `P` | Khóa màn hình / Đưa máy vào chế độ Sleep |
| **Cảm ứng màn hình** | `Chuột trái (Click & Drag)` | Chạm mở mục, cuộn danh sách |

---

## 📖 3. Hướng Dẫn Test OPDS Catalog Trên Máy Ảo X3

Khi cửa sổ máy ảo CrossPoint hiển thị:

1. **Vào Menu Cài Đặt OPDS**:
   - Dùng phím mũi tên di chuyển đến mục **Settings** -> **OPDS Servers** (hoặc mở trực tiếp mục **Wireless / OPDS Browser** trên màn hình chính).
2. **Thêm Server Z-Truyen**:
   - URL Server: `http://localhost:8080/opds` (hoặc `http://127.0.0.1:8080/opds`).
   - Tên Server: `Z-Truyen Local`.
3. **Duyệt & Tải Sách**:
   - Mở **OPDS Browser** -> Chọn **Z-Truyen Local**.
   - Bạn sẽ thấy toàn bộ danh mục:
     - 🌟 *Truyện Mới Cập Nhật*
     - 👑 *Bảng Xếp Hạng Đọc Nhiều*
     - 📚 *Duyệt Theo Thể Loại*
     - 🔍 *Tìm Kiếm Truyện*
   - Chọn truyện (ví dụ: *Con Đường Bá Chủ*), chọn **Tập 01 (Chương 1 - 50)** và bấm **Download**.
4. **Mở Đọc Trên Màn Hình E-ink Ảo**:
   - File EPUB sẽ tải về thẻ nhớ ảo `./sdcard/` và xuất hiện trong mục **Recent Books / Library**.
   - Mở sách để trải nghiệm giao diện đọc thực tế của màn hình Xteink X3 (792 × 528 pixel), tính năng định dạng font tiếng Việt, footnote và đồng bộ vị trí đọc KOSync!

---

## 🛠️ 4. Cấu Trúc Kỹ Thuật Máy Ảo

- **Môi trường**: Linux WSL2 Ubuntu (WSLg Display Server).
- **Đồ họa**: SDL2 Framebuffer Native Driver (792 × 528, 16-level grayscale emulation).
- **Thư mục thẻ nhớ ảo (SD Card)**: `~/crosspoint-reader/sdcard/` và `~/crosspoint-reader/fs_/`.
- **Mã nguồn Firmware**: [crosspoint-reader/crosspoint-reader](https://github.com/crosspoint-reader/crosspoint-reader).
- **Mã nguồn Simulator Shim**: [uxjulia/crosspoint-simulator](https://github.com/uxjulia/crosspoint-simulator).
