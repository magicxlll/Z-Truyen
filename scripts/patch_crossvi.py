#!/usr/bin/env python3
"""
Patch CrossVi codebase for 64-bit desktop simulator compatibility.
Fixes:
1. HttpDownloader.cpp: 64-bit integer overflow in response size check.
   On 64-bit hosts, static_cast<int64_t>(std::numeric_limits<size_t>::max()) evaluates to -1,
   causing all HTTP responses to trigger 'response exceeds size limit' error.
2. OpdsBookBrowserActivity.cpp: Normalize opdsDownloadFolder so that folders without leading
   slash (e.g. 'books') are normalized to '/books', avoiding 'Unsafe download folder rejected'.
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
    
    # Check if buggy code exists
    buggy_pattern = "if (contentLength > static_cast<int64_t>(std::numeric_limits<size_t>::max()) ||"
    fixed_pattern = "if (contentLength > 0 && static_cast<uint64_t>(contentLength) > sink.maxBytes) {"

    if fixed_pattern in content:
        print("[OK] HttpDownloader.cpp already patched.")
        return True

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
    if "normalized: %s" in content:
        print("[OK] OpdsBookBrowserActivity.cpp already patched.")
        return True

    old_block = """  const char* folder = SETTINGS.opdsDownloadFolder;  // "" => SD root
  bool haveFolder = folder[0] != '\\0';
  const std::string folderPath = haveFolder ? folder : "/";
  if (!UploadPathGuard::isSafeAbsolutePath(folderPath.c_str())) {
    LOG_ERR("OPDS", "Unsafe download folder rejected: %s", folder);
    state = BrowserState::ERROR;
    errorMessage = tr(STR_DOWNLOAD_FAILED);
    requestUpdate();
    return;
  }
  if (haveFolder && !Storage.exists(folder) && !Storage.mkdir(folder)) {
    // exists()-guard first: mkdir's return-on-existing is unconfirmed, and every
    // existing caller checks exists() before mkdir. On real failure, fall back
    // to SD root so the download is never lost.
    LOG_ERR("OPDS", "mkdir failed for %s, using SD root", folder);
    haveFolder = false;
  }

  // downloadToFile() needs a std::string, and titles are unbounded (a fixed
  // char[] would truncate). Cold path (a multi-second download follows), so one
  // reserve'd, in-place-appended owning string is the right call.
  std::string filename;
  filename.reserve(96);
  if (haveFolder) filename += folder;
  filename += '/';
  filename += opdsBookFilename(book.author, book.title, static_cast<OpdsFilenameFormat>(SETTINGS.opdsFilenameFormat));"""

    new_block = """  const char* folder = SETTINGS.opdsDownloadFolder;  // "" => SD root
  bool haveFolder = folder[0] != '\\0';
  std::string folderPath = "/";
  if (haveFolder) {
    folderPath = (folder[0] == '/') ? folder : ("/" + std::string(folder));
  }
  if (!UploadPathGuard::isSafeAbsolutePath(folderPath.c_str())) {
    LOG_ERR("OPDS", "Unsafe download folder rejected: %s (normalized: %s)", folder, folderPath.c_str());
    state = BrowserState::ERROR;
    errorMessage = tr(STR_DOWNLOAD_FAILED);
    requestUpdate();
    return;
  }
  if (haveFolder && !Storage.exists(folderPath.c_str()) && !Storage.mkdir(folderPath.c_str())) {
    LOG_ERR("OPDS", "mkdir failed for %s, using SD root", folderPath.c_str());
    haveFolder = false;
  }

  std::string filename;
  filename.reserve(96);
  if (haveFolder) {
    filename += folderPath;
    if (filename.back() != '/') filename += '/';
  } else {
    filename += '/';
  }
  filename += opdsBookFilename(book.author, book.title, static_cast<OpdsFilenameFormat>(SETTINGS.opdsFilenameFormat));"""

    if old_block in content:
        patched = content.replace(old_block, new_block)
        browser_file.write_text(patched, encoding="utf-8")
        print("[SUCCESS] Patched opdsDownloadFolder normalization in OpdsBookBrowserActivity.cpp")
        return True
    return False


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
