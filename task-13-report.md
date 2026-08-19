# Task 13: ConDuongBaChu Source Adapter - Report

## Summary
Successfully implemented the `ConDuongBaChuAdapter` for conduongbachu.com WordPress REST API.

## Deliverables

### 1. Created `/ztruyen_backend/sources/conduongbachu.py`

**Class:** `ConDuongBaChuAdapter(BaseSource)`

**Features:**
- WordPress REST API integration at `https://conduongbachu.com/wp-json/wp/v2`
- Hardcoded STORIES list with 4 novels (main story + 3 spinoffs)
- Chapter filtering by "Chương" in title or "/chuong-" in URL
- Chapter number parsing from title/URL patterns
- Content extraction from WordPress `<div class="entry-content">`
- Proper HTTP headers (Referer, User-Agent)

**STORIES Table:**
| ID | Title | Cat ID |
|----|-------|--------|
| main | Con Đường Bá Chủ (Chính Truyện) | 3 |
| bat-hu-than-chien | Ngoại Truyện: Bất Hủ Thần Chiến | 12 |
| van-dao-than-chu | Ngoại Truyện: Vạn Đạo Thần Chủ | 14 |
| chua-te-chi-lo | Ngoại Truyện: Chúa Tể Chi Lộ | 15 |

**Implemented Methods:**
- `search(query, page)` - Returns empty list (no search support)
- `list_books(page)` - Returns all 4 books in the series
- `get_book(book_id)` - Returns BookSummary for a specific book
- `list_chapters(book_id, page)` - Returns paginated chapter list
- `get_chapter_content(chapter)` - Returns HTML content from chapter page
- `close()` - Closes HTTP client

**ID Format:**
- Book ID: `conduongbachu:<story_id>` (e.g., `conduongbachu:main`)
- Chapter ID: `conduongbachu:<story_id>:<chapter_num>` (e.g., `conduongbachu:main:123`)

### 2. Updated `/ztruyen_backend/sources/__init__.py`

Added exports:
- `ConDuongBaChuAdapter`
- `create_conduongbachu_adapter`
- `STORIES`

## Implementation Notes

1. **No Search Support:** This source is dedicated to a single novel series, so `search()` returns empty list. Use `list_books()` instead.

2. **Chapter Detection:** Chapters are identified by:
   - "Chương" keyword in post title
   - "/chuong-" pattern in URL

3. **Chapter Number Parsing:** Extracts number from:
   - Title: "Chương 123: Tiêu Đề"
   - URL: `/chuong-123/`

4. **Content Extraction:** Fetches chapter page directly and extracts content from `<div class="entry-content">`. Falls back to WordPress REST API if direct fetch fails.

## Files Modified/Created
- `/ztruyen_backend/sources/conduongbachu.py` (NEW)
- `/ztruyen_backend/sources/__init__.py` (MODIFIED)
