# Hướng Dẫn Biến Smartphone Android Thành Pocket Host Server Cho Xteink X3

Tài liệu này hướng dẫn chi tiết cách cài đặt và biến chiếc điện thoại **Android** của bạn thành một **Máy chủ truyện bỏ túi (Pocket Host Server)** di động, cho phép máy đọc sách **Xteink X3** tải và đọc truyện mọi lúc mọi nơi mà không cần máy tính Mac Mini hay PC cố định.

---

## 🌟 1. Lợi Ích & Nguyên Lý Hoạt Động

- **Cực kỳ di động**: Điện thoại luôn ở bên bạn. Bạn có thể tải truyện mới về X3 ở bất kỳ đâu (ở nhà, quán cafe, đi du lịch, trên xe).
- **Linh hoạt 2 chế độ kết nối**:
  1. *Khi ở nhà*: Cả điện thoại và X3 cùng kết nối vào Wi-Fi gia đình.
  2. *Khi ra ngoài*: Điện thoại bật **Điểm phát sóng di động (Wi-Fi Hotspot)** -> X3 bắt Wi-Fi từ điện thoại.
- **Tự động nhận diện (mDNS)**: Bạn chỉ cần lưu duy nhất 1 địa chỉ trên máy X3:
  👉 **`http://ztruyen.local:8080/opds`** (hoặc `http://192.168.43.1:8080/opds`).
- **Tiết kiệm pin 100%**: Khi nào cần tải truyện mới mở Termux gõ `ztruyen`, tải xong nhấn `Ctrl + C` để tắt server ngay, không hao pin ngầm.

---

## 📥 2. Cài Đặt Trên Điện Thoại Android (Chỉ Cần Làm 1 Lần)

### Bước 1: Cài đặt ứng dụng Termux
> ⚠️ **Lưu ý quan trọng**: Không tải Termux trên Google Play Store (bản này đã cũ và ngừng cập nhật). Hãy tải bản mới nhất từ **F-Droid** hoặc **GitHub**:
> - Link tải trực tiếp file APK từ GitHub: [Termux Release APK](https://github.com/termux/termux-app/releases/latest) (chọn file `termux-app_..._arm64-v8a.apk`).

### Bước 2: Đưa mã nguồn Z-Truyen vào điện thoại
Có 2 cách đơn giản:

#### 👉 Cách A (Khuyên dùng - Chuẩn xác & Cập nhật nhanh nhất): Clone từ GitHub
Trong Termux chạy:
```bash
pkg install -y git
git clone https://github.com/magicxlll/Z-Truyen.git ~/ztruyen
cd ~/ztruyen && bash android/setup-termux.sh
```

#### 👉 Cách B: Copy file ZIP offline
1. File **`ztruyen-android.zip`** đã được tạo sẵn ở thư mục gốc dự án trên máy tính.
2. Gửi file `ztruyen-android.zip` sang điện thoại.
3. Mở app **Termux** và chạy:
   ```bash
   termux-setup-storage
   pkg install -y unzip
   mkdir -p ~/ztruyen
   unzip /sdcard/Download/ztruyen-android.zip -d ~/ztruyen
   cd ~/ztruyen && bash android/setup-termux.sh
   ```

---

## 🚀 3. Hướng Dẫn Sử Dụng Hằng Ngày

### ⚡ 1. Khởi động Server (Khi muốn tải truyện cho X3)
Mở app **Termux** và gõ:
```bash
ztruyen
```

### 🔄 2. Cập nhật phiên bản mới nhất từ GitHub (Khi có bản vá / tính năng mới)
Trong Termux chỉ cần gõ:
```bash
ztruyen-update
```
*(Hệ thống sẽ tự động đồng bộ code mới nhất và mở lại Server trong 1 giây, hoàn toàn không sợ lỗi xung đột file).*

### ⏹️ 3. Tắt Server
Sau khi tải xong sách về máy X3, trên màn hình Termux bạn chỉ cần nhấn **`Ctrl + C`** để tắt server và giải phóng tài nguyên pin điện thoại.

---

## 🛠️ 4. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **Termux bị đứng / dừng hoạt động khi tắt màn hình điện thoại**:
   - **Kéo thanh thông báo Android từ đỉnh màn hình xuống** $\rightarrow$ Tìm thông báo của Termux $\rightarrow$ Bấm vào nút **`Acquire wakelock`** (thông báo chuyển sang `Termux: (wake lock held)`).
   - Vào *Cài đặt điện thoại* $\rightarrow$ *Ứng dụng* $\rightarrow$ *Termux* $\rightarrow$ *Pin* $\rightarrow$ Chọn **Không giới hạn (Unrestricted)**.
   - Mở màn hình đa nhiệm $\rightarrow$ Giữ cửa sổ Termux $\rightarrow$ Bấm **Ổ Khóa 🔒** để khóa ứng dụng.
2. **X3 không tìm thấy tên miền `ztruyen.local`**:
   - Nếu router Wi-Fi chặn mDNS broadcast, bạn hãy nhập trực tiếp địa chỉ IP hiển thị trên màn hình Termux (ví dụ `http://192.168.1.22:8080/opds`).
   - Nếu bạn phát Hotspot từ điện thoại, địa chỉ luôn luôn cố định là `http://192.168.43.1:8080/opds` (đảm bảo 100% kết nối thành công).
