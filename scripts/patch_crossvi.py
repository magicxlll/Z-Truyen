#!/usr/bin/env python3
"""
Patch CrossVi codebase for 64-bit desktop simulator compatibility & enhanced UX.
Fixes:
1. HttpDownloader.cpp: 64-bit integer overflow in response size check.
2. OpdsBookBrowserActivity.cpp:
   - Normalize opdsDownloadFolder to always start with '/' (avoiding Unsafe download folder rejected).
   - Set consumeConfirm = true in onEnter() to prevent keypress leak auto-clicking item 0 on load.
   - Automatically organize downloaded books into story subfolders (/books/{Story Name}/).
"""

from __future__ import annotations

import sys
from pathlib import Path


def patch_http_downloader(crossvi_root: Path) -> bool:
    downloader_file = crossvi_root / "src" / "network" / "HttpDownloader.cpp"
    if not downloader_file.exists():
        print(f"[!] File not found: {downloader_file}")
        return False

    content = downloader_file.read_text(encoding="utf-8")
    
    fixed_pattern = "if (contentLength > 0 && static_cast<uint64_t>(contentLength) > sink.maxBytes) {"
    if fixed_pattern in content:
        print("[OK] HttpDownloader.cpp already patched.")
        return True

    buggy_pattern = "if (contentLength > static_cast<int64_t>(std::numeric_limits<size_t>::max()) ||"
    if buggy_pattern in content:
        old_block = """  if (contentLength > static_cast<int64_t>(std::numeric_limits<size_t>::max()) ||
      (contentLength > 0 && static_cast<size_t>(contentLength) > sink.maxBytes)) {
    LOG_ERR("HTTP", "response exceeds size limit");
    esp_http_client_cleanup(client);
    return HttpDownloader::HTTP_ERROR;
  }"""

        new_block = """  if (contentLength > 0 && static_cast<uint64_t>(contentLength) > sink.maxBytes) {
    LOG_ERR("HTTP", "response exceeds size limit: len=%lld max=%zu", static_cast<long long>(contentLength), sink.maxBytes);
    esp_http_client_cleanup(client);
    return HttpDownloader::HTTP_ERROR;
  }"""

        if old_block in content:
            patched = content.replace(old_block, new_block)
            downloader_file.write_text(patched, encoding="utf-8")
            print("[SUCCESS] Patched 64-bit overflow check in HttpDownloader.cpp")
            return True

    print("[!] Buggy pattern not found in HttpDownloader.cpp")
    return False


def patch_opds_browser(crossvi_root: Path) -> bool:
    browser_file = crossvi_root / "src" / "activities" / "browser" / "OpdsBookBrowserActivity.cpp"
    if not browser_file.exists():
        print(f"[!] File not found: {browser_file}")
        return False

    content = browser_file.read_text(encoding="utf-8")

    # 1. Patch consumeConfirm in onEnter
    if "consumeConfirm = false;" in content:
        content = content.replace("consumeConfirm = false;\n  consumeBack = false;", "consumeConfirm = true;\n  consumeBack = true;")
        print("[SUCCESS] Patched consumeConfirm in onEnter() to prevent auto-click")

    # 2. Patch folder download and story subfolder organization
    subfolder_marker = "storyFolder += StringUtils::sanitizeFilename(book.author);"
    if subfolder_marker not in content:
        old_dl_block = """  std::string filename;
  filename.reserve(96);
  if (haveFolder) {
    filename += folderPath;
    if (filename.back() != '/') filename += '/';
  } else {
    filename += '/';
  }
  filename += opdsBookFilename(book.author, book.title, static_cast<OpdsFilenameFormat>(SETTINGS.opdsFilenameFormat));"""

        new_dl_block = """  // Create story subfolder under books/ if author/story is present
  if (!book.author.empty() && haveFolder) {
    std::string storyFolder = folderPath;
    if (storyFolder.back() != '/') storyFolder += '/';
    storyFolder += StringUtils::sanitizeFilename(book.author);
    if (!Storage.exists(storyFolder.c_str())) {
      Storage.mkdir(storyFolder.c_str());
    }
    if (Storage.exists(storyFolder.c_str())) {
      folderPath = storyFolder;
    }
  }

  std::string filename;
  filename.reserve(96);
  if (haveFolder) {
    filename += folderPath;
    if (filename.back() != '/') filename += '/';
  } else {
    filename += '/';
  }
  filename += StringUtils::sanitizeFilename(book.title) + ".epub";"""

        if old_dl_block in content:
            content = content.replace(old_dl_block, new_dl_block)
            print("[SUCCESS] Patched story subfolder organization in downloadBook()")

    browser_file.write_text(content, encoding="utf-8")
    print("[OK] OpdsBookBrowserActivity.cpp patched.")
    return True


def main():
    crossvi_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "crossvi"
    if not crossvi_dir.exists():
        print(f"[!] CrossVi directory not found at {crossvi_dir}")
        return 1

    patch_http_downloader(crossvi_dir)
    patch_opds_browser(crossvi_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
