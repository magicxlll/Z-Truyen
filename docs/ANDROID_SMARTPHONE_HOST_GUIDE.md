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

#### 👉 Cách A (Khuyên dùng - Nhanh nhất): Copy file ZIP
1. File **`ztruyen-android.zip`** đã được tạo sẵn ở thư mục gốc dự án trên máy tính.
2. Gửi file `ztruyen-android.zip` sang điện thoại (qua dây cáp USB, Zalo, Google Drive, hoặc Quick Share).
3. Mở app **Termux** trên điện thoại và cấp quyền truy cập bộ nhớ:
   ```bash
   termux-setup-storage
   ```
   *(Bấm Cho phép / Allow khi điện thoại hỏi)*.
4. Giải nén và chuyển vào thư mục làm việc:
   ```bash
   # Cài đặt unzip nếu chưa có
   pkg install -y unzip
   
   # Giải nén từ thư mục Download của điện thoại
   mkdir -p ~/ztruyen
   unzip /sdcard/Download/ztruyen-android.zip -d ~/ztruyen
   ```

#### 👉 Cách B: Clone trực tiếp từ Git (nếu bạn có đưa code lên GitHub)
Trong Termux chạy:
```bash
pkg install -y git
git clone <URL_REPO_CỦA_BẠN> ~/ztruyen
```

### Bước 3: Chạy script cài đặt tự động 1 lệnh
Trong app Termux, gõ lệnh sau:
```bash
cd ~/ztruyen
bash android/setup-termux.sh
```
*Script sẽ tự động cấu hình Python, cài đặt các thư viện cần thiết (FastAPI, Zeroconf, EbookLib...) và tạo phím tắt lệnh `ztruyen`.*

---

## 🚀 3. Hướng Dẫn Sử Dụng Hằng Ngày

Bất cứ khi nào bạn muốn máy đọc sách X3 tải truyện:

### Bước 1: Mở Server trên điện thoại
Mở app **Termux** và chỉ cần gõ:
```bash
ztruyen
```
Màn hình Termux sẽ hiển thị thông báo máy chủ đang hoạt động kèm các địa chỉ kết nối:
- `http://ztruyen.local:8080/opds` (mDNS)
- `http://192.168.43.1:8080/opds` (Khi bật Hotspot)
- `http://<IP_WIFI>:8080/opds` (Khi dùng Wi-Fi nhà)

### Bước 2: Kết nối & Tải truyện trên Xteink X3
1. Bật Wi-Fi trên máy X3 (kết nối vào Hotspot điện thoại hoặc Wi-Fi nhà).
2. Mở mục **OPDS Browser** trên CrossPoint.
3. Nhập địa chỉ: `http://ztruyen.local:8080/opds` (hoặc `http://192.168.43.1:8080/opds`).
4. Tìm kiếm truyện, chọn tập và bấm **Download**.

### Bước 3: Tắt Server
Sau khi tải xong sách về X3, trên màn hình Termux bạn chỉ cần nhấn **`Ctrl + C`** để tắt server và giải phóng tài nguyên pin điện thoại.

---

## 🛠️ 4. Xử Lý Sự Cố Thường Gặp (Troubleshooting)

1. **X3 không tìm thấy tên miền `ztruyen.local`**:
   - Nếu router Wi-Fi chặn mDNS broadcast giữa các thiết bị con, bạn chỉ cần nhập trực tiếp địa chỉ IP hiển thị trên màn hình Termux (ví dụ `http://192.168.1.15:8080/opds`).
   - Nếu bạn phát Hotspot từ điện thoại, địa chỉ luôn luôn cố định là `http://192.168.43.1:8080/opds` (đảm bảo 100% kết nối thành công).
2. **Termux bị Android tắt khi tắt màn hình**:
   - Script `start-server.sh` đã tự động kích hoạt `termux-wake-lock`. Bạn hãy vào Cài đặt điện thoại -> *Ứng dụng Termux* -> *Pin* -> Chọn **Không giới hạn (Unrestricted)**.
