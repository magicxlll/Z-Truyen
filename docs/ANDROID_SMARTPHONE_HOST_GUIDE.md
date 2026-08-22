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
2. **X3 không kết nối được khi dùng Hotspot (Điện thoại phát Wi-Fi)**:
   - **Băng tần 2.4 GHz (Bắt buộc)**: Chip Wi-Fi ESP32 trên X3 **chỉ hỗ trợ 2.4 GHz**, không hỗ trợ 5.0 GHz. Vào *Cài đặt Hotspot trên điện thoại* $\rightarrow$ *Băng tần AP* $\rightarrow$ Chọn **2.4 GHz** (Tắt tùy chọn Wi-Fi 6).
   - **Bảo mật WPA2**: Vào cài đặt Hotspot $\rightarrow$ *Bảo mật* $\rightarrow$ Chọn **WPA2-Personal** (tránh chọn WPA3 hoặc WPA3-SAE khiến ESP32 lỗi bắt tay).
   - **Địa chỉ OPDS khi dùng Hotspot**: Android chặn gói tin mDNS qua Hotspot nên **không thể dùng `ztruyen.local`**. Bạn phải nhập trực tiếp IP hiển thị tại mục `[CHẾ ĐỘ HOTSPOT DI ĐỘNG]` trong Termux (ví dụ: `http://192.168.43.1:8080/opds` hoặc IP Gateway cấp cho X3).
   - **Tắt VPN / AdGuard**: Tắt các app 1.1.1.1 WARP, AdGuard, VPN trên điện thoại vì chúng có thể chặn cổng 8080 từ Hotspot.
   - **Thứ tự bật**: Bật 4G & Hotspot **trước**, sau đó mới mở Termux gõ `ztruyen`.

3. **X3 không tìm thấy tên miền `ztruyen.local` khi dùng Wi-Fi gia đình (LAN)**:
   - Nếu router Wi-Fi chặn mDNS broadcast, hãy nhập trực tiếp địa chỉ IP hiển thị tại mục `[CHẾ ĐỘ WI-FI GIA ĐÌNH]` trên màn hình Termux (ví dụ `http://192.168.1.15:8080/opds`).
