# Task 7 Report: Source Adapter Base Class

## Summary
Successfully created the source adapter base class and utilities for the Z-Truyen X3 project.

## Files Created

### 1. `ztruyen_backend/sources/base.py`
The main base module containing:

**Data Classes:**
- `BookSummary` - Minimal book/story summary for catalog and search listings
- `Chapter` - Chapter metadata for table of contents
- `ChapterContent` - Full chapter content with HTML for reading and EPUB compilation

**Protocol:**
- `SourceAdapter` - Protocol defining the interface for all source adapters with methods:
  - `search(query, page)` - Search books by keyword
  - `get_book(book_id)` - Fetch detailed metadata for a single book
  - `list_chapters(book_id, page)` - Fetch paginated chapter list
  - `get_chapter_content(chapter)` - Fetch raw HTML content of a chapter

**Base Class:**
- `BaseSource` - Optional helper class providing common functionality:
  - `_fix_cover_url()` - Handle relative URLs for cover images
  - `_build_book_id()` - Build composite book IDs
  - `_build_chapter_id()` - Build composite chapter IDs

**Utility Functions:**
- `build_book_id()` - Build composite book ID from source and book identifiers
- `build_chapter_id()` - Build composite chapter ID from source, book, and chapter identifiers
- `build_chapter_id_from_order()` - Build chapter ID using order number (for sources without slugs)
- `normalize_url()` - Normalize URLs handling relative paths and common variations
- `extract_id_from_url()` - Extract identifier from URL using regex pattern
- `generate_stable_hash()` - Generate stable MD5 hash from string parts
- `parse_page_param()` - Extract page number from URL query parameters

### 2. `ztruyen_backend/sources/__init__.py`
Package initialization file that exports all public symbols for easy imports.

## Usage Example
```python
from ztruyen_backend.sources import BaseSource, BookSummary, build_book_id

class MySourceAdapter(BaseSource):
    id = "mysource"
    name = "My Source"
    base_url = "https://example.com"

    async def search(self, query: str, page: int = 1) -> list[BookSummary]:
        # Implement search logic
        ...

    # ... implement other required methods
```

## ID Format Convention
- Book IDs: `{source_id}:{source_book_id}` (e.g., `storyaclick:dao-hai-tac`)
- Chapter IDs: `{source_id}:{source_book_id}:{source_chapter_id}` (e.g., `storyaclick:dao-hai-tac:chapter-1`)
- Chapter IDs (by order): `{source_id}:{source_book_id}:c{order:04d}` (e.g., `storyaclick:dao-hai-tac:c0005`)
