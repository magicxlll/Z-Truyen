# Task 9 Report: EPUB Builder

## Completed

Created `ztruyen_backend/epub_builder.py` with the following functionality:

### Functions Implemented

1. **`build_epub(chapter, book_title, author, cover_url=None) -> bytes`**
   - Creates EPUB bytes from ChapterContent
   - Uses ebooklib library
   - Returns bytes for direct serving

2. **`build_epub_sync(chapter, book_title, author, cover_url=None) -> bytes`**
   - Synchronous version of build_epub
   - Downloads cover image synchronously when needed

3. **`create_epub_metadata(book_title, author, chapter_title)`**
   - Creates metadata Dublin Core items
   - Creates guide and NCX navigation items
   - Returns tuple of (metadata_item, guide_item, ncx_item)

4. **`add_cover_image(book, cover_url)`**
   - Downloads cover image from URL
   - Resizes if needed (max 800x1200)
   - Handles errors gracefully

### EPUB Structure

```
mimetype
META-INF/container.xml
OEBPS/
  content.opf      # Package document
  nav.xhtml         # Navigation document (EPUB 3)
  style.css         # CSS stylesheet
  text/
    chapter.xhtml   # Chapter content (clean XHTML)
  images/
    cover.jpg       # Cover image (optional)
```

### Supporting Functions

- `sanitize_filename()` - Sanitizes text for filenames
- `generate_epub_filename()` - Creates filename in format `ztruyen__<source>__<book_id>__<chapter_order>.epub`
- `clean_html_content()` - Sanitizes HTML by removing scripts, styles, unwanted tags
- `convert_to_xhtml()` - Converts HTML to valid XHTML with UTF-8 encoding
- `resize_image()` - Resizes images to max 800x1200 for E-ink devices
- `fetch_cover_image()` - Async download of cover images

### Content Handling

- HTML sanitization (removes script, style, iframe, video, etc.)
- UTF-8 encoding throughout
- Vietnamese language support (xml:lang="vi")
- XHTML conversion with proper DOCTYPE

### Dependencies Updated

Added to `ztruyen_backend/pyproject.toml`:
- `Pillow>=10.0.0` (ebooklib already present)

### Files Modified

- `ztruyen_backend/epub_builder.py` - Created (new file)
- `ztruyen_backend/pyproject.toml` - Updated (added Pillow dependency)
