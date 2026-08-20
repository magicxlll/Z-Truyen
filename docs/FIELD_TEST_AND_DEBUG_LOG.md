# 📘 Nhật Ký Xử Lý Sự Cố & Đúc Kết Kinh Nghiệm Triển Khai Thực Tế
**Dự án**: Z-Truyen X3 (Vietnamese Story Backend & OPDS Integration)  
**Tài liệu**: Tổng hợp lỗi, nguyên nhân, cách xử lý và bài học kinh nghiệm từ quá trình cài đặt & kiểm thử thực tế.

---

## 📑 Bảng Tổng Hợp Sự Cố & Tiến Trình Xử Lý

| Mã Lỗi | Thành Phần | Hiện Tượng / Thông Báo Lỗi | Trạng Thái | Ngày Ghi Nhận |
|:---:|---|---|:---:|:---:|
| **BUG-001** | Termux Repo | `Could not connect to mirror.sjtu.edu.cn:443 - connection abort` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-002** | Python/Rust Build | `Failed to build 'pydantic-core' ... Rust not found` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-003** | Android Permissions | `PermissionError: [Errno 13] Permission denied: '.../cache/epubs'` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-004** | Termux Shell | `start-server.sh: ip: command not found` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-005** | Web UI Responsive | Giao diện bị bung chiều ngang trên màn hình điện thoại | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-006** | EPUB Download UX | Nút Tải EPUB không phản hồi do thiếu loading feedback | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-007** | OPDS UI Layout | Tiêu đề chương trên màn hình e-ink X3 bị tràn & cắt thành `...` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-008** | Native Simulator | Biên dịch GCC 15 trên Linux/WSL gặp lỗi narrowing, C23 bool | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-009** | Storya Scraper / Layout | Lỗi thiếu `import asyncio` và tràn tiêu đề chương X3 | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-011** | 64-bit Simulator | Lỗi ép kiểu `size_t::max() -> int64_t = -1` gây `exceeds size limit` | ✅ Đã khắc phục | 2026-08-19 |
| **BUG-012** | AkayTruyen Scraper | Lỗi thiếu ảnh bìa và metadata truyện từ nguồn AkayTruyen | ✅ Đã khắc phục | 2026-08-20 |
| **DEPLOY-001** | Môi trường Android | Cài đặt toàn bộ 26 packages (FastAPI, EbookLib, Zeroconf...) | 🟢 Hoàn tất 100% | 2026-08-19 |
| **RULE-001** | Firmware Integrity | Tuyệt đối tuân thủ 100% Stock Factory Firmware của Xteink X3 | 🟢 Tuân thủ 100% | 2026-08-19 |

---

## 🛠️ Chi Tiết Từng Sự Cố & Giải Pháp Kỹ Thuật

### 1. BUG-001: Lỗi kết nối Mirror Package Manager của Termux
- **Môi trường**: Android Termux (mới cài đặt lần đầu).
- **Hiện tượng**:
  ```text
  Err:1 https://mirror.sjtu.edu.cn/termux/termux-main ...
  Could not connect to mirror.sjtu.edu.cn:443 - connect (103: Software caused connection abort)
  E: Failed to fetch ...
  E: Unable to fetch some archives, maybe run apt-get update or try with --fix-missing?
  ```
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Termux mặc định kết nối tới máy chủ mirror tại Trung Quốc (`mirror.sjtu.edu.cn`).
  - Đường truyền quốc tế từ các nhà mạng Việt Nam tới server này thường bị nghẽn mạng, timeout hoặc ngắt kết nối (`Connection abort`).
- **Cách khắc phục**:
  1. Chạy lệnh: `termux-change-repo`
  2. Tại màn hình 1 (Repositories), nhấn **OK**.
  3. Tại màn hình 2 (Mirrors), chọn **`Mirrors by Grimler`** (châu Âu/Mỹ) hoặc **`Mirrors hosted by Tsinghua`** -> Nhấn **OK**.
- **Đúc kết kinh nghiệm & Khuyến nghị tài liệu**:
  - Nên đưa bước kiểm tra/chuyển đổi repo `termux-change-repo` lên ngay đầu hướng dẫn cài đặt cho người dùng mới.

---

### 2. BUG-002: Lỗi biên dịch `pydantic-core` do thiếu Rust toolchain trên ARM64
- **Môi trường**: Android Termux (Kiến trúc `aarch64` / ARM64, Python 3.14).
- **Hiện tượng**:
  ```text
  Collecting pydantic-core==2.46.4
    Installing build dependencies ... error
    error: subprocess-exited-with-error
    × installing build dependencies for pydantic-core did not run successfully.
    Target triple not supported by rustup: aarch64-unknown-linux-android
    Rust not found, installing into a temporary directory
  ERROR: Failed to build 'pydantic-core' when installing build dependencies for pydantic-core
  ```
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Trên kiến trúc Android `aarch64` với Python 3.14 (phiên bản mới nhất của Termux), PyPI chưa có sẵn pre-built binary wheel (`.whl`).
  - Pip bắt buộc phải tải source tarball (`.tar.gz`) và biên dịch từ mã nguồn.
  - `pydantic-core` được viết bằng **Rust** (sử dụng build tool `maturin`).
  - Khi thiếu trình biên dịch Rust (`rustc` & `cargo`) của hệ điều hành Termux, maturin cố gắng dùng `rustup` nhưng không hỗ trợ trực tiếp target `aarch64-unknown-linux-android`, dẫn tới build failure.
- **Cách khắc phục**:
  1. Cài đặt bộ công cụ biên dịch Rust và Binutils vào Termux:
     ```bash
     pkg install -y rust binutils
     ```
  2. Chạy lại script cài đặt:
     ```bash
     cd ~/ztruyen
     bash android/setup-termux.sh
     ```
- **Cập nhật mã nguồn hệ thống**:
  - Đã cập nhật file [`android/setup-termux.sh`](file:///D:/03_APP/3.%20System/DATA/Antigravity/Z-Truyen/android/setup-termux.sh#L13-L17) bổ sung sẵn gói `rust` và `binutils` trong danh sách cài đặt mặc định:
    ```bash
    pkg install -y python git clang make rust binutils libxml2 libxslt libjpeg-turbo libffi openssl termux-tools
    ```

---

### 3. BUG-003: Lỗi cấp quyền thư mục `Permission denied` khi tạo cache EPUB
- **Môi trường**: Android Termux (Giải nén từ file ZIP hoặc copy từ bộ nhớ máy).
- **Hiện tượng**:
  ```text
  PermissionError: [Errno 13] Permission denied: '/data/data/com.termux/files/home/ztruyen/backend/data/cache/epubs'
  ```
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Khi file ZIP được giải nén hoặc copy từ bộ nhớ chia sẻ `/sdcard`, các thư mục có thể bị gán cờ quyền chỉ đọc (Read-only / `chmod 555`) hoặc thiếu quyền ghi `w`. Khi FastAPI khởi động, `ObjectStorage.ensure_directories()` cố gắng tạo thư mục con `cache/epubs` thì bị hệ điều hành Android từ chối.
- **Cách khắc phục**:
  1. Cấp lại toàn quyền đọc/ghi/thực thi cho thư mục dự án:
     ```bash
     chmod -R u+rwx ~/ztruyen
     ```
  2. Tự động hóa: Đã bổ sung lệnh tự động sửa quyền `chmod -R u+rwx` ngay đầu script `start-server.sh`.

---

### 4. BUG-004: Lỗi lệnh `ip: command not found` trên Termux Shell
- **Môi trường**: Android Termux cơ bản (chưa cài `iproute2`).
- **Hiện tượng**:
  ```text
  start-server.sh: line 32: ip: command not found
  ```
- **Nguyên nhân gốc rễ**: Lệnh `ip` thuộc gói `iproute2` không có sẵn mặc định trên một số bản cài đặt Termux rút gọn.
- **Cách khắc phục**:
  - Cập nhật script `start-server.sh` để kiểm tra có `ip` hoặc `ifconfig` trước khi chạy, tránh văng lỗi trên màn hình.

### 5. BUG-005: Giao diện Web Catalog bị bung chiều ngang trên màn hình điện thoại
- **Môi trường**: Trình duyệt di động (Brave / Chrome trên Android).
- **Hiện tượng**:
  - Modal danh sách tập truyện bị tràn viền phải, nút "Tải EPUB" bị cắt một nửa.
  - Phải dùng tay zoom nhỏ lại mới nhìn được toàn bộ trang.
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Thiếu thẻ `viewport-fit=cover` và `maximum-scale=1.0, user-scalable=no`.
  - Layout `.volume-item` dùng `display: flex; justify-content: space-between` dạng hàng ngang với tiêu đề truyện dài, đẩy nút bấm ra ngoài biên màn hình (< 400px).
- **Cách khắc phục**:
  - Tái cấu trúc CSS mobile-first: Chuyển `.volume-item` trên mobile sang xếp dọc (`flex-direction: column`), nút bấm full-width dễ chạm ngón tay.
  - Thêm `overflow-x: hidden` trên toàn bộ thẻ `html, body`.
  - Tối ưu thanh Quick Nav cuộn ngang mượt mà (`overflow-x: auto; -webkit-overflow-scrolling: touch;`).

---

### 6. BUG-006: Nút "Tải EPUB" không có phản hồi thị giác và cào phân trang chậm
- **Môi trường**: Tải các truyện có số lượng chương lớn (ví dụ: *Vô Địch Thiên Đế* với 3,871 chương).
- **Hiện tượng**: Bấm nút Tải EPUB thì trang đứng im, không thấy tải về hoặc tưởng bị đơ.
- **Nguyên nhân gốc rễ (Root Cause)**:
  1. Thẻ `<a download>` truyền thống không có trạng thái chờ (loading spinner). Trong khi server phải cào và nén 50 chương (mất 5 - 10 giây), trình duyệt không hiển thị tiến trình.
  2. Hàm `get_all_chapters` của scraper `storyaclick` duyệt tuần tự 39 trang danh sách chương khiến thời gian khởi tạo mất thêm 9 giây.
- **Cách khắc phục**:
  1. Chuyển hàm `get_all_chapters` sang tải phân trang **song song** (Concurrent Gather qua Semaphore), rút ngắn thời gian nạp 3,900 chương từ 9s xuống **< 1s**.
  2. Viết lại nút tải trong Web UI bằng JavaScript `startDownload()` tương tác:
     - Khi bấm: Nút lập tức đổi thành `⏳ Đang cào & nén...` và hiện hiệu ứng chờ.
     - Khi nén xong: Tự động kích hoạt tải file `.epub` về máy và đổi nút sang `✅ Đã tải về!`.
     - Nếu có lỗi máy chủ: Tự động bắt mã lỗi và hiển thị cửa sổ thông báo chi tiết (`alert`) thay vì im lặng.

### 7. FEAT-001: Cơ Chế Đọc "Gần Như Online" (Near-Online Streaming & Background Prefetch)
- **Mục tiêu**: Phục vụ việc theo dõi các chương mới cập nhật trên web, tải tức thì (< 0.3s/chương), tự động tải ngầm 3 chương tiếp theo và dọn dẹp 5 chương cũ.
- **Hiện thực**:
  1. **Single-Chapter EPUB Generator**: Tạo file EPUB 1 chương siêu nhẹ (15 - 30KB) để mở đọc ngay.
  2. **Background Prefetch Engine**: Sử dụng `FastAPI BackgroundTasks` để khi người dùng đọc chương $N$, server tự động cào và nén sẵn chương $N+1, N+2, N+3$ vào cache. Khi bấm chương tiếp theo, file có sẵn lập tức với độ trễ 0s!
  3. **Smart Cache Manager**: Tự động dọn dẹp các chương cũ hơn $N-5$ để tránh đầy bộ nhớ điện thoại.
  4. **Volume Bundler**: Vẫn duy trì tùy chọn tải gom tập 50 chương/tập cho mục đích đọc offline đường dài.

### 8. BUG-009: Thiếu `import asyncio` trong `storyaclick.py` khi tải tập/chương phân trang
- **Môi trường**: Backend chạy trên điện thoại Termux hoặc PC khi client yêu cầu tải tập/chương từ nguồn Storya.click (ví dụ: *Mục Thần Ký*, *Xích Tâm Tuần Thiên*).
- **Hiện tượng**: Máy ảo CrossPoint báo lỗi `Download failed`, log server Termux ghi nhận `500 Internal Server Error` với dòng lỗi: `NameError: name 'asyncio' is not defined`.
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Trong hàm `get_all_chapters()` của `storyaclick.py`, tính năng cào phân trang song song sử dụng `asyncio.Semaphore` và `asyncio.gather` nhưng module bị thiếu dòng `import asyncio` ở đầu file.
- **Cách khắc phục**:
  - Thêm `import asyncio` vào đầu `backend/app/sources/storyaclick.py`.
  - Bổ sung unit/integration test `test_storyaclick_mock_flow` kiểm tra trường hợp phân trang `totalPages > 1` gọi `get_all_chapters()`.
  - Cập nhật mã nguồn lên GitHub để Termux kéo về qua lệnh `ztruyen-update`.

---

### 8. PERF-001: Phân Tích Hiện Tượng "Chuyển Sang Termux Tốc Độ Nhanh Hơn Trình Duyệt"
- **Hiện tượng**: Khi thao tác tìm/tải truyện trên trình duyệt điện thoại rồi chuyển sang app Termux thì thấy Termux chạy nhanh hơn là giữ nguyên ở trình duyệt.
- **Nguyên nhân kỹ thuật (Android OS Scheduling & Battery Throttling)**:
  - Trên hệ điều hành Android (MIUI/HyperOS, OneUI, ColorOS), khi trình duyệt (Chrome/Brave) đang ở màn hình trước (Foreground), Android sẽ đưa tiến trình chạy ngầm (Termux) vào chế độ **tiết kiệm pin (cgroup background throttle)**, hạ xung nhịp CPU xuống mức tối thiểu (300 - 600 MHz) và giảm băng thông I/O.
  - Khi người dùng chuyển màn hình sang app Termux -> Termux trở thành Foreground App -> Android lập tức kích hoạt CPU Boost lên xung nhịp tối đa (2.4 - 3.2 GHz) và tăng ưu tiên đa luồng, khiến tác vụ hoàn thành tức thì.
- **Trải nghiệm thực tế với máy đọc sách Xteink X3**:
  - Khi bạn dùng máy X3 kết nối qua Wi-Fi/Hotspot vào điện thoại: Điện thoại không mở trình duyệt nội bộ nữa, app Termux được cấp quyền **"Không giới hạn (Unrestricted)"** và chạy `termux-wake-lock`, kết hợp với kết nối socket TCP trực tiếp sẽ đạt **tốc độ tối đa liên tục**, không bị hệ điều hành Android kìm hãm xung nhịp.

### 9. BUG-007: Lỗi 404 Khi Nhấn Vào Bộ Truyện (Endpoint Path Mismatch)
- **Triệu chứng**: Khi nhấn vào tên truyện (ví dụ: `chung-cuc-truyen-ky`, `lac-hong-than-chu`, `muc-than-ky`), giao diện báo lỗi và Termux ghi log: `GET /opds/api/book/source/slug HTTP/1.1 404 Not Found`. Không xem được danh sách chương và tab gom tập.
- **Nguyên nhân**:
  - Trong `books.py`, endpoint JSON được đăng ký là `@router.get("/api/book/{source_id}/{book_slug}/chapters")` (kèm tiền tố `/opds` thành `/opds/api/book/.../chapters`).
  - Trong khi đó Web UI gọi `/opds/api/book/${source}/${slug}` (thiếu đuôi `/chapters`), dẫn đến không khớp route và FastAPI trả về mã lỗi 404.
- **Khắc phục**:
  1. Thêm đồng thời cả 2 route alias trong `books.py`: `@router.get("/api/book/{source_id}/{book_slug}")` và `@router.get("/api/book/{source_id}/{book_slug}/chapters")`.
  2. Nâng cấp hàm `openStoryDetail()` và `renderVolumesTab()` trong `web.py` với cơ chế tải song song `Promise.allSettled` nạp đồng thời cả danh sách chương lẻ và danh sách tập 50 chương, kèm cơ chế tự động chuyển tab dự phòng (fallback) nếu một trong hai gặp sự cố.

### 10. BUG-008: Android Doze Mode & Background Process Freezing (Cơ Chế Khắc Phục Triệt Để)
- **Triệu chứng**: Khi chuyển sang trình duyệt web hoặc tắt màn hình điện thoại, các yêu cầu tải từ máy đọc sách bị ngưng trệ, chỉ khi mở lại màn hình Termux thì hệ thống mới tiếp tục chạy.
- **Nguyên nhân**: Hệ điều hành Android (Android 12+) tự động kích hoạt Phantom Process Killer và cgroup freezing đối với các ứng dụng nền không đăng ký Foreground Service với WakeLock mức hệ thống.
- **Khắc phục**:
  1. **Acquire WakeLock**: Người dùng kéo thanh thông báo điện thoại xuống $\rightarrow$ Bấm nút `Acquire wakelock` tại thông báo của Termux (trạng thái chuyển thành `Termux: (wake lock held)`).
  2. **Lock in Recent Apps**: Khóa biểu tượng ổ khóa 🔒 cho Termux trong màn hình đa nhiệm.
  3. **Battery Unrestricted**: Chuyển chế độ quản lý pin của Termux sang "Không giới hạn".
  4. **Uvicorn Keep-Alive**: Cấu hình `--timeout-keep-alive 75 --limit-concurrency 100` để giữ luồng socket luôn sẵn sàng.

### 11. BUG-009: Tràn và Cắt Tiêu Đề Chương Thành `...` Trên Màn Hình E-ink X3 (792px)
- **Triệu chứng**: Khi mở danh sách chương trên máy ảo / máy thật X3, các dòng chương bị cắt chữ thành dạng `Vô Địch Thiên Đế — Chương 1: Thiên Đ...`, người đọc không nhìn thấy được tên chương đầy đủ.
- **Nguyên nhân**: Màn hình Xteink X3 có độ phân giải ngang 792px. Nếu đưa chuỗi `{Tên truyện} — Chương {X}: {Tên chương}` vào thẻ `<title>` của Atom OPDS feed, chiều dài vượt quá bề rộng màn hình và firmware CrossPoint tự động cắt ngắn bằng dấu chấm lửng `...`.
- **Khắc phục**:
  1. Trong `opds_builder.py` (`build_book_chapters_feed`), tách biệt hoàn toàn:
     - Thẻ `<title>`: Chỉ chứa tên chương sạch gọn (`Chương X: Tên Chương`).
     - Thẻ `<author>`: Chứa tên truyện (`{Tên Truyện}`).
  2. Firmware CrossPoint sẽ tự động hiển thị Dòng 1 (in đậm, to) là Tên chương đầy đủ, và Dòng 2 (nhỏ bên dưới) là Tên truyện, tạo bố cục cân đối và không bao giờ bị cắt chữ.

### 12. BUG-010: Xung Đột GCC 15 / C23 Khi Biên Dịch Native CrossPoint Simulator Trên WSL
- **Triệu chứng**: Khi build máy ảo `simulator_x3` trên Ubuntu 24.04/Debian (GCC 15), trình biên dịch báo lỗi narrowing conversion (`[-Wnarrowing]`), lỗi C23 bool keyword trong `QRCode/qrcode.h`, và thiếu `memcpy_P` trong `AnimatedGIF`.
- **Khắc phục**:
  1. Thêm cờ `-Wno-narrowing` và `-Dmemcpy_P=memcpy` vào `platformio.local.ini`.
  2. Bọc `typedef unsigned char bool;` trong `QRCode` bằng điều kiện kiểm tra phiên bản chuẩn C23 (`__STDC_VERSION__ < 202311L`).
  3. Bổ sung các stub tương thích (`IDLE_POWER_SAVING_MS`, `combinesGrayscaleBase`) trong thư viện giả lập phần cứng `crosspoint-simulator`.

### 13. BUG-011: Lỗi Tràn Số Nguyên 64-bit Trong `HttpDownloader.cpp` Khi Chạy Simulator Trên macOS
- **Triệu chứng**: Kết nối mạng báo xanh, nhưng khi vào OPDS Browser duyệt server Termux hoặc Localhost thì màn hình máy ảo báo: `Lỗi: Không tải được danh mục` và log terminal ghi nhận `[ERR] [HTTP] response exceeds size limit`.
- **Nguyên nhân gốc rễ (Root Cause)**:
  - Trong hàm `HttpDownloader::runGetSecure()`, dòng kiểm tra kích thước:
    `if (contentLength > static_cast<int64_t>(std::numeric_limits<size_t>::max()) || ...)`
  - Trên vi điều khiển ESP32 (32-bit), `size_t` là 32-bit (`uint32_t::max() = 4294967295`), khi ép sang `int64_t` vẫn là `+4294967295LL`.
  - Trên hệ điều hành 64-bit máy tính (macOS Apple Silicon & Linux x86_64), `size_t` là 64-bit (`uint64_t::max() = 0xFFFFFFFFFFFFFFFF`), khi ép sang số nguyên có dấu `int64_t` sẽ bị tràn bit và trở thành **`-1`**!
  - Kết quả là bất kỳ phản hồi HTTP nào có `contentLength >= 0` đều thỏa mãn điều kiện `contentLength > -1` (luôn luôn `TRUE`), khiến toàn bộ các request tải feed OPDS hoặc sách đều bị hủy ngay lập tức.
- **Khắc phục**:
  - Viết script tự động vá lỗi [`scripts/patch_crossvi.py`](file:///Users/vietph/Library/CloudStorage/GoogleDrive-vietph.eng@gmail.com/Other%20computers/My%20Computer/DATA/Antigravity/Z-Truyen/Z-Truyen/scripts/patch_crossvi.py).
  - Sửa lại điều kiện kiểm tra kích thước thành: `if (contentLength > 0 && static_cast<uint64_t>(contentLength) > sink.maxBytes)`.
  - Tích hợp bước tự động áp dụng bản vá này vào launcher [`run_crossvi_x3.command`](file:///Users/vietph/Library/CloudStorage/GoogleDrive-vietph.eng@gmail.com/Other%20computers/My%20Computer/DATA/Antigravity/Z-Truyen/Z-Truyen/run_crossvi_x3.command).

### 14. BUG-012: Lỗi Mất Ảnh Bìa & Metadata Truyện Từ Nguồn AkayTruyen (Khắc Phục Toàn Diện)
- **Triệu chứng**: Khi tải các truyện từ nguồn AkayTruyen (như *Thiên La*, *Chung Cực Truyền Kỳ*, *Lạc Hồn Thôn Nguyên Quyết*...), tên file tải về bị sai thành chữ cái đầu của slug (ví dụ: `T_Tập 01_chương 1-50.epub`), và màn hình Home/Sleep của X3 không hiển thị ảnh bìa truyện.
- **Nguyên nhân gốc rễ (Root Cause)**:
  1. Trang chi tiết truyện của AkayTruyen sử dụng cấu trúc DOM `<div class="book-3d"><img src="..." alt="...">` kết hợp các thẻ OpenGraph `<meta property="og:image">`, `<meta property="og:title">`, `<meta property="og:book:author">`.
  2. Bộ parser cũ trong `AkayTruyenAdapter.get_story_detail` chỉ tìm kiếm `.story-thumb img, .book-cover img` và `h1`, dẫn tới `cover_url` bị trả về `None`, `title` bị fallback về slug `"thien-la"`, và `author` là `"Đang cập nhật"`.
  3. Khi `cover_url` bị `None`, `bundler.py` và `epub_builder.py` không nhúng được `cover.jpg` vào file EPUB, khiến `generateThumbBmp()` của X3 tạo ra `thumb_226.bmp` rỗng 0 bytes.
- **Cách khắc phục**:
  1. Cập nhật `AkayTruyenAdapter.get_story_detail` trích xuất thông tin đa tầng từ OpenGraph `<meta>` và DOM `.book-3d img`.
  2. Cập nhật `_parse_story_anchors` tự động trích xuất ảnh bìa từ thẻ `img` trong `a` và `a.parent`.
  3. Nâng cấp `cover_service.get_or_create_cover` tự động cập nhật ảnh bìa chất lượng cao khi có `cover_url`.
  4. Đã kiểm tra thực tế: EPUB của *Thiên La* được tạo với ảnh bìa `cover.jpg` 29KB chuẩn E-ink, tên viết tắt chuẩn `TL_Tập 01_chương 1-50.epub`.

### 15. BUG-013: Lỗi Thư Mục Tải Về Trên SDCard Bị Đặt Tên Theo Tác Giả Thay Vì Tên Truyện
- **Triệu chứng**: Khi tải sách trên máy X3, các file EPUB được lưu vào thư mục `SDCard/Books/{Tên Tác Giả}/...` (hoặc `SDCard/Books/Đang cập nhật/...`) thay vì theo đúng tên truyện `SDCard/Books/{Tên Truyện}/...`.
- **Nguyên nhân gốc rễ**:
  - Trong firmware CrossVi / CrossPoint (`OpdsBookBrowserActivity.cpp`), khi người dùng tải một entry sách kiểu `BOOK`, firmware tự động tạo thư mục con dựa trên giá trị của thẻ `<author><name>` trong OPDS feed.
  - Nếu Backend truyền `<author><name>{story.author}</name>` vào feed tải tập/chương, firmware sẽ tạo thư mục theo tác giả.
- **Cách khắc phục**:
  - Trong `backend/app/api/opds_builder.py` (`build_book_volumes_feed` và `build_book_chapters_feed`), gán `<author><name>{story.title}</name>` cho các entry tải file EPUB.
  - Firmware X3 sẽ tự động tạo thư mục con theo đúng tên truyện: `SDCard/Books/{Tên Truyện}/{Tên Viết Tắt}_Tập X_chương A-B.epub`.

### 16. FEAT-001: Tái Cấu Trúc Menu Chính OPDS & Hỗ Trợ Tìm Kiếm Tiếng Việt Không Dấu Cho E-ink
- **Bối cảnh & Yêu cầu**:
  - Giao diện ban đầu hiển thị tràn lan các danh mục của nhiều nguồn truyện khiến người dùng trên màn hình nhỏ E-ink khó thao tác.
  - Bàn phím ảo trên firmware X3 chỉ hỗ trợ ký tự Latin (ASCII), không có bộ gõ tiếng Việt Telex/VNI.
- **Giải pháp triển khai**:
  1. **Menu Chính 8 mục tinh gọn**:
     - `🌐 Chọn Nguồn Truyện`: Vào danh sách nguồn truyện để chuyển đổi.
     - `📚 Nguồn: [Tên Nguồn Hiện Tại]`: Hiển thị nguồn đang kích hoạt.
     - `📖 Đọc Tiếp: [Tên Truyện] (Chương X)`: Dẫn trực tiếp đến danh sách chương truyện tải gần nhất.
     - `⚡ Truyện Mới Cập Nhật`: Lọc theo nguồn hiện tại.
     - `🔥 Truyện Hot & Đọc Nhiều`: Lọc theo nguồn hiện tại.
     - `✅ Truyện Hoàn Thành (Full Trọn Bộ)`: Lọc theo nguồn hiện tại.
     - `📂 Thể Loại Truyện`: Lọc theo nguồn hiện tại.
     - `🔍 Tìm Truyện (Không Dấu & Có Dấu)`: Lọc theo nguồn hiện tại.
  2. **Ghi nhớ nguồn kích hoạt (Active Source)**:
     - Lưu trạng thái vào bảng SQLite `active_source` qua `repo.set_active_source(source_id)` và `repo.get_active_source()`.
  3. **Bộ tìm kiếm tiếng Việt không dấu (`remove_accents`)**:
     - Chuẩn hóa Unicode loại bỏ dấu tiếng Việt, so khớp đa nhánh (direct search, slug search, và unaccented title scoring).
     - Cho phép gõ `muc than ky`, `thien la`, `con duong ba chu` tìm ra đúng tác phẩm ngay lập tức.

### 17. RULE-001: Nguyên Tắc Bất Di Bất Dịch — Giữ 100% Stock Factory Firmware
- **Quy tắc**: Tuyệt đối **KHÔNG** chỉnh sửa hoặc can thiệp vào mã nguồn firmware gốc của CrossPoint Reader / Xteink X3 để đạt được mục đích.
- **Lý do**: Máy đọc sách Xteink X3 vật lý ngoài đời chạy firmware gốc xuất xưởng của nhà sản xuất (hoặc bản flash release chính thức). Người dùng không thể và không nên tùy tiện flash custom firmware vì rủi ro brick máy cao.
- **Giải pháp chuẩn**: Mọi tính năng (danh sách chương, tiếp tục đọc, phân loại danh mục, ảnh bìa, gom tập KOSync) phải được hiện thực hoàn toàn 100% phía **Backend Server OPDS** theo đúng đặc tả Atom / OPDS 1.2 RFC.

---

## 🖥️ 4. Hướng Dẫn Chạy Máy Ảo Xteink X3 Simulator 1-Click Trên Windows Desktop

Để kiểm thử thực tế trải nghiệm duyệt thư viện và đọc sách của Xteink X3 trước khi nạp vào máy thật:

### Cách 1: Chạy Máy Ảo E-Reader Simulator 1-Click (Khuyên dùng)
1. Trên máy tính Windows, mở thư mục dự án `Z-Truyen`.
2. Nhấp đúp chuột vào file **`run_x3_simulator.bat`**.
3. Cửa sổ máy ảo X3 xuất hiện:
   - Nếu bạn muốn kết nối với **Điện thoại Android**: Nhập địa chỉ IP của điện thoại (ví dụ: `http://192.168.43.1:8080` khi phát Hotspot hoặc `http://192.168.1.X:8080` khi chung Wi-Fi).
   - Nếu bạn muốn kết nối với **Backend trên máy tính**: Chỉ cần nhấn `Enter` (dùng mặc định `http://localhost:8080`).
4. Giao diện máy ảo X3 cho phép:
   - Duyệt Truyện Hot, Mới Cập Nhật, Truyện Hoàn Thành.
   - Tìm kiếm truyện toàn hệ thống.
   - **Tải và đọc thử từng chương (Single-Chapter Streaming 0.3s)**.
   - **Tải và kiểm tra độ chuẩn hóa EPUB gom tập (50 chương/tập)** với đầy đủ mã băm KOSync SHA-1.

---

## 🚀 3. Đánh Giá Trải Nghiệm & Đề Xuất Kiến Trúc Cài Đặt 1-Click Cho Người Dùng Cuối

### Vấn đề hiện tại:
- Quá trình biên dịch mã nguồn C/C++/Rust (`pydantic-core`, `selectolax`, `Pillow`, `zeroconf`) trực tiếp trên CPU điện thoại tốn nhiều thời gian (khoảng 3 - 8 phút), gây nóng máy và phụ thuộc vào kết nối repo.
- Thao tác dòng lệnh Termux chỉ phù hợp cho giai đoạn phát triển (Dev/Test), chưa thân thiện với người dùng không chuyên.

### Lộ trình tối ưu hóa (Roadmap to 1-Click):

1. **Giải pháp Cấp 1 (Pre-built Wheels Offline Bundle - Giảm thời gian cài xuống 5 giây)**:
   - Đóng gói toàn bộ các file `.whl` kiến trúc `aarch64` đã biên dịch xong vào thư mục `wheels/` trong file ZIP.
   - Khi cài đặt, pip chỉ cần chạy: `pip install --no-index --find-links=wheels/ -r requirements.txt`.
   - Kết quả: Không cần tải từ mạng, không cần cài `rust/clang/make`, cài đặt hoàn tất ngay tức thì.

2. **Giải pháp Cấp 2 (Android Native App .APK 1-Click - Giải pháp Tối thượng cho End-User)**:
   - Đóng gói toàn bộ Z-Truyen Backend thành 1 file **`ZTruyen-X3.apk`** độc lập (sử dụng Android Foreground Service).
   - Giao diện người dùng:
     - Nút to: **[ BẬT SERVER ]** / **[ TẮT SERVER ]**.
     - Hiển thị địa chỉ mDNS `http://ztruyen.local:8080/opds`, địa chỉ IP và mã QR.
   - Người dùng chỉ cần tải APK -> Cài đặt -> Mở app bấm 1 nút là X3 có thể kết nối ngay, 0% dòng lệnh.

---
*Tài liệu này sẽ tiếp tục được cập nhật tự động sau mỗi lần test thực tế.*
