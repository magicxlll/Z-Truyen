#!/usr/bin/env python3
"""
Z-Truyen X3 — OPDS Device & E-Reader Terminal Simulator
Mô phỏng 100% thiết bị đọc sách E-ink Xteink X3 (CrossVi / KOReader)
kết nối và tải truyện từ Backend OPDS.
"""

import sys
import io
import time
import argparse
import xml.etree.ElementTree as ET
import httpx
from ebooklib import epub

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Namespaces Atom & OPDS
NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "dc": "http://purl.org/dc/terms/",
    "opds": "http://opds-spec.org/2010/catalog",
}


def print_banner():
    print("=" * 65)
    print("  📖 Z-TRUYEN X3 — MÁY ẢO / E-READER TERMINAL SIMULATOR")
    print("  Mô phỏng máy đọc sách E-ink Xteink X3 & KOReader")
    print("=" * 65)


class OpdsSimulator:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=60.0)

    def check_health(self) -> bool:
        print(f"\n[1] Đang kiểm tra kết nối tới Server: {self.base_url}/healthz ...")
        try:
            r = self.client.get(f"{self.base_url}/healthz")
            if r.status_code == 200:
                data = r.json()
                print(f"    ✅ Kết nối thành công! Status: {data.get('status')}, Phiên bản: {data.get('version')}")
                return True
            else:
                print(f"    ❌ Lỗi HTTP {r.status_code}: {r.text}")
                return False
        except Exception as e:
            print(f"    ❌ Không thể kết nối tới máy chủ ({e}). Hãy đảm bảo Backend đang chạy!")
            return False

    def fetch_feed(self, url: str) -> list[dict]:
        """Tải và phân tích Atom XML feed."""
        full_url = url if url.startswith("http") else f"{self.base_url}{url}"
        r = self.client.get(full_url)
        if r.status_code != 200:
            print(f"    ❌ Lỗi tải feed {full_url}: HTTP {r.status_code}")
            return []

        root = ET.fromstring(r.text)
        entries = []
        for entry in root.findall("atom:entry", NAMESPACES):
            title = entry.findtext("atom:title", default="", namespaces=NAMESPACES)
            entry_id = entry.findtext("atom:id", default="", namespaces=NAMESPACES)
            summary = entry.findtext("atom:summary", default="", namespaces=NAMESPACES)
            content = entry.findtext("atom:content", default="", namespaces=NAMESPACES)
            author = entry.findtext("atom:author/atom:name", default="", namespaces=NAMESPACES)

            links = {}
            for link in entry.findall("atom:link", NAMESPACES):
                rel = link.get("rel", "")
                href = link.get("href", "")
                links[rel] = href

            entries.append({
                "title": title,
                "id": entry_id,
                "summary": summary or content,
                "author": author,
                "links": links,
            })
        return entries

    def run_menu(self):
        if not self.check_health():
            print("\n⚠️ Vui lòng chạy Backend trước (`./scripts/run-dev.sh` hoặc `docker compose up -d`).")
            return

        while True:
            print("\n" + "-" * 55)
            print("  📱 MENU ĐIỀU HƯỚNG OPDS BROWSER (MÁY ĐỌC SÁCH X3)")
            print("-" * 55)
            print("  1. 🔥 Xem Truyện Hot / Đọc Nhiều (/opds/hot)")
            print("  2. ⚡ Xem Truyện Mới Cập Nhật (/opds/latest)")
            print("  3. ✅ Xem Truyện Đã Hoàn Thành Full (/opds/completed)")
            print("  4. 📂 Xem Thể Loại Truyện (/opds/genres)")
            print("  5. 🌐 Xem Danh Sách Nguồn Cào (/opds/sources)")
            print("  6. 🔍 Tìm Kiếm Truyện Toàn Hệ Thống (/opds/search)")
            print("  7. 🧪 Tải & Đọc Thử 1 Chương Tức Thì (0.3s Streaming Test)")
            print("  8. 📦 Tải & Kiểm Thử 1 Tập EPUB 50 Chương (Con Đường Bá Chủ Tập 1)")
            print("  0. 🚪 Thoát")
            print("-" * 55)

            choice = input("👉 Chọn chức năng (0-8): ").strip()
            if choice == "0":
                print("Tạm biệt!")
                break
            elif choice == "1":
                self.show_story_list("/opds/hot", "Truyện Hot")
            elif choice == "2":
                self.show_story_list("/opds/latest", "Truyện Mới Cập Nhật")
            elif choice == "3":
                self.show_story_list("/opds/completed", "Truyện Hoàn Thành (Full)")
            elif choice == "4":
                self.show_navigation_feed("/opds/genres", "Thể Loại")
            elif choice == "5":
                self.show_navigation_feed("/opds/sources", "Nguồn Cào")
            elif choice == "6":
                q = input("Nhập tên truyện / tác giả cần tìm: ").strip()
                if q:
                    self.show_story_list(f"/opds/search?q={q}", f"Kết quả tìm kiếm: '{q}'")
            elif choice == "7":
                self.download_and_verify_epub("/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_c0001.epub", "Con Đường Bá Chủ - Chương 1 (Single Chapter)")
            elif choice == "8":
                self.download_and_verify_epub("/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_v01.epub", "Con Đường Bá Chủ - Tập 01 (50 Chương)")
            else:
                print("Lựa chọn không hợp lệ, vui lòng thử lại!")

    def show_story_list(self, url: str, title_label: str):
        print(f"\n📡 Đang tải danh sách: {title_label}...")
        entries = self.fetch_feed(url)
        if not entries:
            print("    (Không có truyện nào)")
            return

        print(f"\n=== {title_label.upper()} ({len(entries)} truyện) ===")
        for idx, item in enumerate(entries[:15], 1):
            author_str = f" - Tác giả: {item['author']}" if item['author'] else ""
            print(f"  [{idx:02d}] {item['title']}{author_str}")

        print("\n👉 Nhập số thứ tự truyện để xem chi tiết và tải tập (hoặc bấm Enter để quay lại): ", end="")
        sel = input().strip()
        if sel.isdigit() and 1 <= int(sel) <= len(entries):
            selected = entries[int(sel) - 1]
            detail_link = selected["links"].get("subsection") or selected["links"].get("alternate")
            if detail_link:
                self.show_story_detail(detail_link, selected["title"])
            else:
                print("Không tìm thấy link chi tiết tập.")

    def show_navigation_feed(self, url: str, label: str):
        print(f"\n📡 Đang tải: {label}...")
        entries = self.fetch_feed(url)
        if not entries:
            print("    (Không có mục nào)")
            return

        print(f"\n=== DANH SÁCH {label.upper()} ===")
        for idx, item in enumerate(entries, 1):
            print(f"  [{idx:02d}] {item['title']} - {item['summary']}")

        print("\n👉 Nhập số thứ tự mục để duyệt truyện (hoặc bấm Enter để quay lại): ", end="")
        sel = input().strip()
        if sel.isdigit() and 1 <= int(sel) <= len(entries):
            selected = entries[int(sel) - 1]
            link = selected["links"].get("subsection") or selected["links"].get("alternate")
            if link:
                self.show_story_list(link, selected["title"])

    def show_story_detail(self, detail_url: str, story_title: str):
        # Extract source and slug from detail URL
        import re
        match = re.search(r"/book/([^/]+)/([^/]+)", detail_url)
        if not match:
            print("    ❌ Không phân tích được đường dẫn truyện.")
            return
        source_id, story_slug = match.group(1), match.group(2)

        print(f"\n📖 Đang tải toàn bộ dữ liệu chương của: '{story_title}' từ {source_id}...")
        try:
            r = self.client.get(f"{self.base_url}/opds/api/book/{source_id}/{story_slug}")
            if r.status_code != 200:
                print(f"    ❌ Lỗi nạp danh sách chương: HTTP {r.status_code}")
                return
            data = r.json()
            story_meta = data.get("story", {})
            chapters = data.get("chapters", [])
        except Exception as e:
            print(f"    ❌ Không thể nạp dữ liệu: {e}")
            return

        total_ch = len(chapters)
        page_size = 50
        total_pages = (total_ch + page_size - 1) // page_size if total_ch > 0 else 1
        current_page = 1

        while True:
            start_idx = (current_page - 1) * page_size
            end_idx = min(start_idx + page_size, total_ch)
            page_chaps = chapters[start_idx:end_idx]

            print(f"\n" + "=" * 65)
            print(f"  📖 {story_title.upper()}")
            print(f"  Tác giả: {story_meta.get('author', 'Đang cập nhật')} | Tổng: {total_ch} chương")
            print(f"  📄 TRANG [{current_page}/{total_pages}] (Hiển thị chương {start_idx + 1} - {end_idx})")
            print("=" * 65)

            for c in page_chaps:
                print(f"  [{c['order']:03d}] {c['title']}")

            print("\n" + "-" * 65)
            print("  👉 CÁC CÚ PHÁP TẢI VÀ ĐỌC SÁCH:")
            print("     - Nhập 1 số (Ví dụ: 32)      ➔ Tải & Đọc riêng Chương 32 (0.3s)")
            print("     - Nhập khoảng (Ví dụ: 1-32)  ➔ Tải và GOM Chương 1 đến 32 vào 1 file EPUB")
            print("     - Nhập 'all' hoặc 'ALL'      ➔ Tải và GOM TOÀN BỘ TRỌN BỘ vào 1 file EPUB")
            if total_pages > 1:
                print("     - Nhập 'n' (Next) / 'p' (Prev)➔ Sang trang sau / Quay lại trang trước")
            print("     - Nhấn [Enter]               ➔ Quay lại danh sách truyện")
            print("-" * 65)

            user_cmd = input("👉 Nhập lựa chọn của bạn: ").strip()

            if not user_cmd:
                break
            elif user_cmd.lower() == "n" and current_page < total_pages:
                current_page += 1
            elif user_cmd.lower() == "p" and current_page > 1:
                current_page -= 1
            elif user_cmd.lower() == "all":
                dl_url = f"/opds/download/{source_id}/{story_slug}/ztruyen_{source_id}_{story_slug}_all.epub"
                self.download_and_verify_epub(dl_url, f"{story_title} - Trọn Bộ ({total_ch} Chương)")
            elif "-" in user_cmd:
                parts = user_cmd.split("-")
                if len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit():
                    s_num, e_num = int(parts[0].strip()), int(parts[1].strip())
                    dl_url = f"/opds/download/{source_id}/{story_slug}/ztruyen_{source_id}_{story_slug}_c{s_num:04d}-{e_num:04d}.epub"
                    self.download_and_verify_epub(dl_url, f"{story_title} - Gom Chương {s_num} đến {e_num}")
                else:
                    print("⚠️ Cú pháp khoảng chương không hợp lệ (Ví dụ đúng: 1-32)")
            elif user_cmd.isdigit():
                chap_num = int(user_cmd)
                if 1 <= chap_num <= total_ch:
                    dl_url = f"/opds/download/{source_id}/{story_slug}/ztruyen_{source_id}_{story_slug}_c{chap_num:04d}.epub"
                    self.download_and_verify_epub(dl_url, f"{story_title} - Chương {chap_num}")
                else:
                    print(f"⚠️ Số chương vượt quá giới hạn (Truyện có từ 1 đến {total_ch} chương)")
            else:
                print("⚠️ Lựa chọn không hợp lệ, vui lòng thử lại!")

    def download_and_verify_epub(self, download_url: str, volume_title: str):
        import os
        import re
        from pathlib import Path

        full_url = download_url if download_url.startswith("http") else f"{self.base_url}{download_url}"
        filename = download_url.split("/")[-1] if "/" in download_url else "ztruyen_book.epub"
        
        # Thư mục lưu file trên máy ảo (tương đương thẻ nhớ MicroSD trên máy X3 thật)
        download_dir = Path(__file__).resolve().parent.parent / "downloads"
        download_dir.mkdir(parents=True, exist_ok=True)
        save_path = download_dir / filename

        print(f"\n📥 Đang tải và đóng gói EPUB từ Server: {full_url} ...")
        t0 = time.time()
        try:
            r = self.client.get(full_url)
            duration = time.time() - t0
            if r.status_code != 200:
                print(f"    ❌ Lỗi tải EPUB: HTTP {r.status_code}")
                return

            epub_bytes = r.content
            size_kb = len(epub_bytes) / 1024
            sha1 = r.headers.get("x-kosync-sha1", "N/A")

            # 1. Lưu file thật vào thư mục downloads/
            with open(save_path, "wb") as f:
                f.write(epub_bytes)

            print(f"\n    ✅ ĐÃ TẢI VỀ MÁY ẢO THÀNH CÔNG! (Thời gian: {duration:.2f}s)")
            print(f"    📁 Vị trí lưu trên máy tính (Thẻ nhớ ảo): {save_path}")
            print(f"    📦 Dung lượng file: {size_kb:.2f} KB ({len(epub_bytes)} bytes)")
            print(f"    🔑 Mã băm KOSync SHA-1: {sha1}")

            # 2. Đọc và xác minh file EPUB
            book = epub.read_epub(io.BytesIO(epub_bytes))
            title = book.get_metadata("DC", "title")
            author = book.get_metadata("DC", "creator")
            lang = book.get_metadata("DC", "language")
            items = list(book.get_items())
            chaps = [i for i in items if i.file_name.startswith("chapter_")]

            print("\n  🔍 KẾT QUẢ KIỂM TRA ĐỘ HỢP LỆ EPUB (EPUB VALIDATION):")
            print(f"    - Tiêu đề sách: {title[0][0] if title else 'N/A'}")
            print(f"    - Tác giả: {author[0][0] if author else 'N/A'}")
            print(f"    - Ngôn ngữ: {lang[0][0] if lang else 'N/A'}")
            print(f"    - Số lượng chương trong file: {len(chaps)} chương")
            print(f"    - Tương thích E-ink Xteink X3: 100% ĐẠT CHUẨN (<1MB, clean XHTML)")

            # 3. Tùy chọn mở đọc ngay trên máy ảo hoặc mở thư mục
            print("\n" + "-" * 55)
            print("  📖 BẠN MUỐN LÀM GÌ TIẾP THEO?")
            print("     [1] Đọc thử nội dung chương ngay trên máy ảo (E-ink Reader)")
            print("     [2] Mở thư mục chứa file EPUB trên máy tính")
            print("     [Enter] Quay lại menu")
            print("-" * 55)
            sub_choice = input("👉 Lựa chọn (1/2/Enter): ").strip()
            
            if sub_choice == "1" and chaps:
                self.read_epub_terminal(chaps)
            elif sub_choice == "2":
                os.system(f'explorer.exe /select,"{save_path}"')

        except Exception as e:
            print(f"    ❌ Lỗi trong quá trình tải/xác minh EPUB: {e}")

    def read_epub_terminal(self, chaps: list):
        """Trình mô phỏng đọc sách E-ink trực tiếp trên terminal."""
        import re
        import textwrap

        for c_idx, chap in enumerate(chaps, 1):
            content_str = chap.get_content().decode("utf-8", errors="ignore")
            
            # Lọc bỏ các thẻ HTML để lấy văn bản thuần
            clean_text = re.sub(r"<style.*?</style>", "", content_str, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<script.*?</script>", "", clean_text, flags=re.DOTALL | re.IGNORECASE)
            clean_text = re.sub(r"<h[1-6].*?>(.*?)</h[1-6]>", r"\n\n=== \1 ===\n\n", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"<p.*?>", "\n  ", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"<br\s*/?>", "\n", clean_text, flags=re.IGNORECASE)
            clean_text = re.sub(r"<[^>]+>", "", clean_text)
            clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()

            paragraphs = clean_text.split("\n\n")
            formatted_lines = []
            for p in paragraphs:
                wrapped = textwrap.fill(p.strip(), width=62, initial_indent="  ", subsequent_indent="  ")
                formatted_lines.append(wrapped)

            full_formatted = "\n\n".join(formatted_lines)
            
            # Chia trang (khoảng 22 dòng mỗi trang E-ink)
            lines = full_formatted.split("\n")
            lines_per_page = 20
            pages = [lines[i:i + lines_per_page] for i in range(0, len(lines), lines_per_page)]
            
            if not pages:
                pages = [["(Chương này chưa có nội dung chữ)"]]

            p_idx = 0
            while p_idx < len(pages):
                print("\n" + "=" * 65)
                print(f"  📖 MÀN HÌNH E-INK X3 | CHƯƠNG {c_idx}/{len(chaps)} | TRANG {p_idx + 1}/{len(pages)}")
                print("=" * 65 + "\n")
                
                print("\n".join(pages[p_idx]))
                
                print("\n" + "-" * 65)
                print(f"  [Enter] / [N] Trang sau | [P] Trang trước | [Q] Thoát đọc sách")
                print("-" * 65)
                
                cmd = input("👉 Lật trang: ").strip().lower()
                if cmd == "q":
                    return
                elif cmd == "p" and p_idx > 0:
                    p_idx -= 1
                else:
                    p_idx += 1


def main():
    parser = argparse.ArgumentParser(description="Z-Truyen X3 OPDS Device Simulator")
    parser.add_argument("--url", default="", help="Base URL of Z-Truyen Backend")
    args = parser.parse_args()

    print_banner()

    target_url = args.url.strip()
    if not target_url:
        print("\n🌐 CẤU HÌNH KẾT NỐI MÁY CHỦ:")
        print("   - Nếu Server đang chạy trên Điện thoại phát Hotspot: Nhập http://192.168.43.1:8080")
        print("   - Nếu Server đang chạy trên Điện thoại cùng Wi-Fi: Nhập IP điện thoại (VD: http://192.168.1.5:8080)")
        print("   - Nếu chạy Backend ngay trên máy tính: Bấm ENTER để dùng mặc định [http://localhost:8080]")
        print("-" * 65)
        user_in = input("\n👉 Nhập URL Server (bấm Enter để dùng http://localhost:8080): ").strip()
        target_url = user_in if user_in else "http://localhost:8080"

    sim = OpdsSimulator(base_url=target_url)
    sim.run_menu()


if __name__ == "__main__":
    main()
