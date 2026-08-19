"""Patch crosspoint-reader firmware to auto-create story subfolders and open reader on download complete."""

import sys
from pathlib import Path


def patch_downloader():
    path = Path("/root/crosspoint-reader/src/activities/browser/OpdsBookBrowserActivity.cpp")
    if not path.is_file():
        print(f"File not found: {path}")
        return

    content = path.read_text(encoding="utf-8")

    # 1. Folder creation
    target1 = 'const char* folder = SETTINGS.opdsDownloadFolder;'
    replacement1 = '''// Base folder: default to /books
  std::string folder = "/books";
  if (SETTINGS.opdsDownloadFolder[0] != '\\0') {
    folder = SETTINGS.opdsDownloadFolder;
    if (folder.empty() || folder[0] != '/') folder = "/" + folder;
  }
  if (!Storage.exists(folder.c_str())) {
    Storage.mkdir(folder.c_str());
  }

  // Create clean subfolder for the story
  if (!book.author.empty() && book.author != "Đang cập nhật") {
    std::string storyName = book.author;
    const size_t sepPos = storyName.find(" • ");
    if (sepPos != std::string::npos) {
      storyName = storyName.substr(0, sepPos);
    }
    std::string cleanStoryFolder = folder + "/" + StringUtils::sanitizeFilename(storyName, 60);
    if (Storage.exists(cleanStoryFolder.c_str()) || Storage.mkdir(cleanStoryFolder.c_str())) {
      folder = cleanStoryFolder;
    }
  }

  std::string filename;
  filename.reserve(96);
  filename += folder;
  filename += '/';
  filename += opdsBookFilename(book.author, book.title, static_cast<OpdsFilenameFormat>(SETTINGS.opdsFilenameFormat));'''

    # Find the block from target1 until filename += opdsBookFilename...
    idx1 = content.find(target1)
    if idx1 != -1:
        end_marker = 'filename += opdsBookFilename(book.author, book.title, static_cast<OpdsFilenameFormat>(SETTINGS.opdsFilenameFormat));'
        idx1_end = content.find(end_marker, idx1)
        if idx1_end != -1:
            full_old_block = content[idx1:idx1_end + len(end_marker)]
            content = content.replace(full_old_block, replacement1)
            print("Successfully patched download folder logic!")

    # 2. Auto open reader on complete
    target2 = '''  if (result == HttpDownloader::OK) {
    clearBookCache(filename);
    state = BrowserState::BROWSING;
  }'''
    replacement2 = '''  if (result == HttpDownloader::OK) {
    clearBookCache(filename);
    state = BrowserState::BROWSING;
    onSelectBook(filename);
    return;
  }'''
    if target2 in content:
        content = content.replace(target2, replacement2)
        print("Successfully patched auto open reader logic!")

    path.write_text(content, encoding="utf-8")
    print("Saved patched file.")


if __name__ == "__main__":
    patch_downloader()
