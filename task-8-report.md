# Task 8 Report: Storya.click Source Adapter

## Summary
Successfully implemented the StoryaAdapter class for the storya.click source.

## Deliverables

### 1. Created `ztruyen_backend/sources/storya.py`

The adapter implements the following interface:

| Method | Description |
|--------|-------------|
| `search(query, page)` | Search stories by keyword |
| `list_books(page)` | List latest stories |
| `get_book(book_id)` | Fetch detailed metadata |
| `list_chapters(book_id, page)` | Fetch chapter list |
| `get_chapter_content(chapter)` | Fetch chapter content |
| `get_genres()` | Fetch genre categories |
| `get_stories_by_genre(genre_slug, page)` | Fetch stories by genre |

### 2. Updated `ztruyen_backend/sources/__init__.py`

Added exports:
- `StoryaAdapter` - The adapter class
- `create_storya_adapter` - Factory function

## Implementation Details

### ID Format
- Book ID: `storya:<slug>` (e.g., `storya:van-tuong-son-ha`)
- Chapter ID: `storya:<book_slug>:<chapter_slug>` (e.g., `storya:van-tuong-son-ha:chuong-1`)

### HTTP Client
- Uses `httpx.AsyncClient` for async HTTP requests
- Includes proper headers: `Accept: application/json`, `User-Agent`
- 30-second timeout
- Proper cleanup via `close()` method

### Content Priority
The adapter uses `rewrittenContent` preferentially for chapter content (as specified), falling back to `content` then `rawContent`.

### Error Handling
- Returns empty lists on HTTP errors for search/list operations
- Raises `httpx.HTTPStatusError` for single-item fetches
- Validates ID formats with clear error messages

## Files Modified/Created
- `ztruyen_backend/sources/storya.py` - New adapter (195 lines)
- `ztruyen_backend/sources/__init__.py` - Updated exports
