"""Tests for Storya adapter and EPUB builder."""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.storya import StoryaAdapter
from sources.base import BookSummary, Chapter, ChapterContent
import epub_builder


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_search_response() -> dict:
    """Sample search API response."""
    return {
        "data": [
            {
                "slug": "test-story",
                "title": "Test Story Title",
                "author": {"name": "Test Author"},
                "coverUrl": "https://cdn.storya.click/cover.jpg",
            },
            {
                "slug": "another-story",
                "title": "Another Story",
                "author": "Single Author Name",
                "coverUrl": None,
            }
        ]
    }


@pytest.fixture
def sample_book_details_response() -> dict:
    """Sample book details API response."""
    return {
        "data": {
            "slug": "con-duong-ba-chu",
            "title": "Con Đường Bá Chủ",
            "author": {"name": "Tác Giả Nổi Tiếng"},
            "rewrittenDescription": "Một câu chuyện về con đường trở thành bá chủ.",
            "description": "Original description here.",
            "coverUrl": "https://cdn.storya.click/cover-full.jpg",
        }
    }


@pytest.fixture
def sample_chapters_response() -> dict:
    """Sample chapter list API response."""
    return {
        "data": [
            {
                "slug": "chuong-1",
                "title": "Chương 1: Khởi Đầu",
                "order": 1
            },
            {
                "slug": "chuong-2",
                "title": "Chương 2: Thử Thách",
                "order": 2
            },
            {
                "slug": "chuong-3",
                "title": "Chương 3: Trở Lại",
                "order": 3
            }
        ]
    }


@pytest.fixture
def sample_chapter_content_response() -> dict:
    """Sample chapter content API response."""
    return {
        "data": {
            "slug": "chuong-1",
            "title": "Chương 1: Khởi Đầu",
            "order": 1,
            "rewrittenContent": "<p>Đây là nội dung chương 1.</p><p>Tiếp tục câu chuyện.</p>",
            "content": "<p>Raw content here</p>",
            "rawContent": "<p>Very raw content</p>"
        }
    }


@pytest.fixture
def sample_book_summary() -> BookSummary:
    """Sample book summary for EPUB testing."""
    return BookSummary(
        id="storya:test-book",
        title="Test Story",
        author="Test Author",
        summary="A test story summary",
        cover_url="https://example.com/cover.jpg",
        source_id="storya",
        url="https://storya.click/truyen/test-book"
    )


@pytest.fixture
def sample_chapter() -> Chapter:
    """Sample chapter for EPUB testing."""
    return Chapter(
        id="storya:test-book:chapter-1",
        title="Chapter 1: Introduction",
        order=1,
        book_id="storya:test-book",
        url="https://storya.click/truyen/test-book/chapter-1"
    )


@pytest.fixture
def sample_chapter_content() -> ChapterContent:
    """Sample chapter content for EPUB testing."""
    return ChapterContent(
        id="storya:test-book:chapter-1",
        title="Chapter 1: Introduction",
        content="<p>Đây là nội dung chương 1.</p><p>Tiếp tục với nội dung thú vị.</p>",
        book_id="storya:test-book",
        chapter_order=1
    )


# =============================================================================
# Test Classes
# =============================================================================

class TestStoryaAdapter:
    """Tests for StoryaAdapter class."""

    def test_adapter_creation(self) -> None:
        """Verify adapter can be created."""
        adapter = StoryaAdapter()

        assert adapter.id == "storya"
        assert adapter.name == "Storya"
        assert adapter.base_url == "https://storya.click"
        assert adapter.api_base == "https://storya.click/api/v1"
        assert adapter._client is None

    def test_build_book_id(self) -> None:
        """Test ID generation for books."""
        adapter = StoryaAdapter()

        book_id = adapter._build_book_id("dao-hai-tac")
        assert book_id == "storya:dao-hai-tac"

        book_id = adapter._build_book_id("test-story-123")
        assert book_id == "storya:test-story-123"

    def test_build_chapter_id(self) -> None:
        """Test chapter ID generation."""
        adapter = StoryaAdapter()

        chapter_id = adapter._build_chapter_id("dao-hai-tac", "chapter-1")
        assert chapter_id == "storya:dao-hai-tac:chapter-1"

        chapter_id = adapter._build_chapter_id("test-book", "chuong-5")
        assert chapter_id == "storya:test-book:chuong-5"

    @pytest.mark.asyncio
    async def test_parse_book_id(self) -> None:
        """Test extracting book slug from ID."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"data": {"slug": "test-slug"}}
            book = await adapter.get_book("storya:test-slug")
            assert book.id == "storya:test-slug"

    @pytest.mark.asyncio
    async def test_parse_invalid_book_id(self) -> None:
        """Test that invalid book ID raises ValueError."""
        adapter = StoryaAdapter()

        with pytest.raises(ValueError, match="Invalid book_id format"):
            await adapter.get_book("invalid-format")

    @pytest.mark.asyncio
    async def test_parse_empty_book_id(self) -> None:
        """Test that empty book ID raises ValueError."""
        adapter = StoryaAdapter()

        with pytest.raises(ValueError, match="Book ID is empty"):
            await adapter.get_book("storya:")

    def test_fix_cover_url_with_https(self) -> None:
        """Test cover URL fixing with absolute URL."""
        adapter = StoryaAdapter()
        cover = adapter._fix_cover_url("https://example.com/image.jpg")
        assert cover == "https://example.com/image.jpg"

    def test_fix_cover_url_with_protocol_relative(self) -> None:
        """Test cover URL fixing with protocol-relative URL."""
        adapter = StoryaAdapter()
        cover = adapter._fix_cover_url("//cdn.example.com/image.jpg")
        assert cover == "https://cdn.example.com/image.jpg"

    def test_fix_cover_url_with_relative(self) -> None:
        """Test cover URL fixing with relative URL."""
        adapter = StoryaAdapter()
        cover = adapter._fix_cover_url("/images/cover.jpg")
        assert cover == "https://storya.click/images/cover.jpg"

    def test_parse_author_with_dict(self) -> None:
        """Test author parsing with dict format."""
        adapter = StoryaAdapter()
        author = adapter._parse_author({"name": "Tác Giả"})
        assert author == "Tác Giả"

    def test_parse_author_with_string(self) -> None:
        """Test author parsing with string format."""
        adapter = StoryaAdapter()
        author = adapter._parse_author("Tác Giả Đơn")
        assert author == "Tác Giả Đơn"

    def test_parse_author_with_none(self) -> None:
        """Test author parsing with None."""
        adapter = StoryaAdapter()
        author = adapter._parse_author(None)
        assert author == "Đang cập nhật"

    def test_parse_genres_with_dict_list(self) -> None:
        """Test genres parsing with dict list."""
        adapter = StoryaAdapter()
        genres = adapter._parse_genres([
            {"name": "Hành Động"},
            {"name": "Phiêu Lưu"}
        ])
        assert genres == ["Hành Động", "Phiêu Lưu"]

    def test_parse_genres_with_string_list(self) -> None:
        """Test genres parsing with string list."""
        adapter = StoryaAdapter()
        genres = adapter._parse_genres(["Action", "Adventure"])
        assert genres == ["Action", "Adventure"]

    def test_parse_genres_with_empty(self) -> None:
        """Test genres parsing with empty input."""
        adapter = StoryaAdapter()
        genres = adapter._parse_genres(None)
        assert genres == []


class TestStoryaAPI:
    """Tests for StoryaAdapter API methods with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_search_stories(self, sample_search_response: dict) -> None:
        """Test search endpoint parsing."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_search_response

            results = await adapter.search("test")

            assert len(results) == 2
            assert results[0].id == "storya:test-story"
            assert results[0].title == "Test Story Title"
            assert results[0].author == "Test Author"
            assert results[1].author == "Single Author Name"

            mock_api.assert_called_once_with("/stories/search?q=test")

    @pytest.mark.asyncio
    async def test_search_empty_query(self, sample_search_response: dict) -> None:
        """Test search with empty query falls back to list_books."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_search_response

            results = await adapter.search("")

            # Empty query should call list_books
            mock_api.assert_called_once()
            # Verify it was called with stories endpoint (list_books)
            call_args = mock_api.call_args[0][0]
            assert "stories" in call_args

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self) -> None:
        """Test search handles HTTP errors gracefully."""
        import httpx
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )

            results = await adapter.search("nonexistent")

            assert results == []

    @pytest.mark.asyncio
    async def test_get_book_details(self, sample_book_details_response: dict) -> None:
        """Test book details parsing."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_book_details_response

            book = await adapter.get_book("storya:con-duong-ba-chu")

            assert book.id == "storya:con-duong-ba-chu"
            assert book.title == "Con Đường Bá Chủ"
            assert book.author == "Tác Giả Nổi Tiếng"
            assert book.summary == "Một câu chuyện về con đường trở thành bá chủ."
            assert book.source_id == "storya"
            assert book.url == "https://storya.click/truyen/con-duong-ba-chu"

            mock_api.assert_called_once_with("/stories/con-duong-ba-chu")

    @pytest.mark.asyncio
    async def test_get_book_falls_back_to_description(self) -> None:
        """Test book details falls back to description if rewrittenDescription missing."""
        adapter = StoryaAdapter()
        response = {
            "data": {
                "slug": "test-book",
                "title": "Test Book",
                "author": {"name": "Author"},
                "description": "Original description only"
            }
        }

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = response

            book = await adapter.get_book("storya:test-book")

            assert book.summary == "Original description only"

    @pytest.mark.asyncio
    async def test_list_chapters(self, sample_chapters_response: dict) -> None:
        """Test chapter list parsing."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_chapters_response

            chapters = await adapter.list_chapters("storya:test-book")

            assert len(chapters) == 3
            assert chapters[0].id == "storya:test-book:chuong-1"
            assert chapters[0].title == "Chương 1: Khởi Đầu"
            assert chapters[0].order == 1
            assert chapters[0].book_id == "storya:test-book"
            assert chapters[1].order == 2
            assert chapters[2].order == 3

            mock_api.assert_called_once_with(
                "/chapters/story/test-book?page=1&limit=100&minimal=true"
            )

    @pytest.mark.asyncio
    async def test_list_chapters_pagination(self, sample_chapters_response: dict) -> None:
        """Test chapter list with pagination."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_chapters_response

            chapters = await adapter.list_chapters("storya:test-book", page=2)

            mock_api.assert_called_once_with(
                "/chapters/story/test-book?page=2&limit=100&minimal=true"
            )

    @pytest.mark.asyncio
    async def test_list_chapters_invalid_book_id(self) -> None:
        """Test list_chapters with invalid book ID returns empty list."""
        adapter = StoryaAdapter()

        chapters = await adapter.list_chapters("invalid:book:id")

        assert chapters == []

    @pytest.mark.asyncio
    async def test_get_chapter_content(self, sample_chapter_content_response: dict) -> None:
        """Test chapter content parsing."""
        chapter = Chapter(
            id="storya:test-book:chuong-1",
            title="Chương 1",
            order=1,
            book_id="storya:test-book",
            url="https://storya.click/truyen/test-book/chuong-1"
        )
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_chapter_content_response

            content = await adapter.get_chapter_content(chapter)

            assert content.id == "storya:test-book:chuong-1"
            assert content.title == "Chương 1: Khởi Đầu"
            assert content.content == "<p>Đây là nội dung chương 1.</p><p>Tiếp tục câu chuyện.</p>"
            assert content.book_id == "storya:test-book"
            assert content.chapter_order == 1

            mock_api.assert_called_once_with("/chapters/test-book/chuong-1")

    @pytest.mark.asyncio
    async def test_get_chapter_content_prefers_rewritten(self) -> None:
        """Test chapter content prefers rewrittenContent."""
        chapter = Chapter(
            id="storya:test:chapter",
            title="Chapter",
            order=1,
            book_id="storya:test",
            url="https://example.com"
        )
        adapter = StoryaAdapter()
        response = {
            "data": {
                "title": "Chapter",
                "content": "Raw HTML",
                "rewrittenContent": "Clean rewritten text",
                "rawContent": "Very raw"
            }
        }

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = response

            content = await adapter.get_chapter_content(chapter)

            assert content.content == "Clean rewritten text"

    @pytest.mark.asyncio
    async def test_get_chapter_content_invalid_id_format(self) -> None:
        """Test chapter content with invalid ID format raises ValueError."""
        chapter = Chapter(
            id="invalid-id",
            title="Chapter",
            order=1,
            book_id="invalid",
            url="https://example.com"
        )
        adapter = StoryaAdapter()

        with pytest.raises(ValueError, match="Invalid chapter.id format"):
            await adapter.get_chapter_content(chapter)

    @pytest.mark.asyncio
    async def test_list_books(self, sample_search_response: dict) -> None:
        """Test list_books returns book summaries."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = sample_search_response

            books = await adapter.list_books(page=1)

            assert len(books) == 2
            assert books[0].id == "storya:test-story"
            mock_api.assert_called_once_with("/stories?page=1&limit=20")


class TestEPUBBuilder:
    """Tests for EPUB builder functionality."""

    def test_build_epub_basic(
        self,
        sample_chapter_content: ChapterContent,
        sample_book_summary: BookSummary
    ) -> None:
        """Test basic EPUB generation."""
        epub_bytes = epub_builder.build_epub(
            chapter=sample_chapter_content,
            book_title=sample_book_summary.title,
            author=sample_book_summary.author
        )

        # Verify it's a valid EPUB file (ZIP format)
        assert epub_bytes is not None
        assert len(epub_bytes) > 0

        # Verify it's a valid ZIP
        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            # EPUB must contain mimetype file
            assert "mimetype" in zf.namelist()

    def test_epub_has_required_files(
        self,
        sample_chapter_content: ChapterContent
    ) -> None:
        """Verify EPUB structure has required files."""
        epub_bytes = epub_builder.build_epub(
            chapter=sample_chapter_content,
            book_title="Test Book",
            author="Test Author"
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            namelist = zf.namelist()

            # Required EPUB 2/3 files
            assert "mimetype" in namelist
            assert "META-INF/container.xml" in namelist
            assert any("content.opf" in f for f in namelist)
            assert any("nav.xhtml" in f for f in namelist or any("text/chapter.xhtml" in f for f in namelist))
            # CSS file could be in EPUB/ or OEBPS/ subdirectory
            assert any("style.css" in f for f in namelist)

    def test_epub_metadata(
        self,
        sample_chapter_content: ChapterContent
    ) -> None:
        """Verify EPUB metadata is correct."""
        book_title = "Con Đường Bá Chủ"
        author = "Tác Giả Nổi Tiếng"

        epub_bytes = epub_builder.build_epub(
            chapter=sample_chapter_content,
            book_title=book_title,
            author=author
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            # Find content.opf
            content_files = [f for f in zf.namelist() if "content.opf" in f]
            assert len(content_files) > 0

            content_opf = zf.read(content_files[0]).decode("utf-8")

            # Verify metadata in content.opf
            assert book_title in content_opf
            assert author in content_opf
            assert "vi" in content_opf  # Vietnamese language

    def test_epub_charset(self, sample_chapter_content: ChapterContent) -> None:
        """Verify EPUB uses UTF-8 encoding."""
        epub_bytes = epub_builder.build_epub(
            chapter=sample_chapter_content,
            book_title="Test Book",
            author="Test Author"
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            # Check mimetype
            mimetype = zf.read("mimetype").decode("utf-8").strip()
            assert mimetype == "application/epub+zip"

            # Check chapter XHTML has UTF-8 declaration
            chapter_files = [f for f in zf.namelist() if "chapter.xhtml" in f]
            if chapter_files:
                chapter_content = zf.read(chapter_files[0]).decode("utf-8")
                assert "utf-8" in chapter_content.lower() or "UTF-8" in chapter_content

            # Check CSS has UTF-8 declaration
            css_files = [f for f in zf.namelist() if f.endswith(".css")]
            if css_files:
                css_content = zf.read(css_files[0]).decode("utf-8")
                assert "@charset" in css_content
                assert "utf-8" in css_content.lower()

    def test_epub_vietnamese_content(self) -> None:
        """Verify EPUB correctly handles Vietnamese characters."""
        content = ChapterContent(
            id="storya:test:chapter",
            title="Chương 1: Khởi Đầu",
            content="<p>Đây là nội dung tiếng Việt với các ký tự đặc biệt như ă, â, ê, ô, ơ, ư, đ.</p>",
            book_id="storya:test",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="Truyện Tiếng Việt",
            author="Tác Giả Việt Nam"
        )

        # Verify EPUB can be read
        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            chapter_files = [f for f in zf.namelist() if "chapter.xhtml" in f]
            assert len(chapter_files) > 0

            chapter_content = zf.read(chapter_files[0]).decode("utf-8")
            # Verify Vietnamese characters are preserved
            assert "Chương 1" in chapter_content or "Khởi Đầu" in chapter_content

    def test_epub_empty_content(self) -> None:
        """Test EPUB builder handles empty content."""
        content = ChapterContent(
            id="storya:test:chapter",
            title="Empty Chapter",
            content="",
            book_id="storya:test",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="Test Book",
            author="Author"
        )

        assert epub_bytes is not None
        assert len(epub_bytes) > 0

        # Verify it still contains placeholder for empty content
        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            chapter_files = [f for f in zf.namelist() if "chapter.xhtml" in f]
            if chapter_files:
                chapter_content = zf.read(chapter_files[0]).decode("utf-8")
                assert "Không có nội dung" in chapter_content or "[Nội dung" in chapter_content

    def test_epub_with_html_content(self) -> None:
        """Test EPUB builder with HTML content containing various tags."""
        content = ChapterContent(
            id="storya:test:chapter",
            title="HTML Chapter",
            content="""<p>First paragraph.</p>
<p>Second paragraph with <strong>bold</strong> and <em>italic</em>.</p>
<hr/>
<p>After horizontal rule.</p>""",
            book_id="storya:test",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="HTML Test",
            author="Author"
        )

        assert epub_bytes is not None
        assert len(epub_bytes) > 0

    def test_epub_with_script_tags_stripped(self) -> None:
        """Test that script tags are stripped from content."""
        content = ChapterContent(
            id="storya:test:chapter",
            title="Script Test",
            content="""<p>Normal content</p>
<script>alert('xss')</script>
<p>More content</p>""",
            book_id="storya:test",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="Script Test",
            author="Author"
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            chapter_files = [f for f in zf.namelist() if "chapter.xhtml" in f]
            if chapter_files:
                chapter_content = zf.read(chapter_files[0]).decode("utf-8")
                assert "alert" not in chapter_content.lower()

    def test_epub_identifier_format(self) -> None:
        """Test EPUB identifier is correctly formatted."""
        content = ChapterContent(
            id="storya:my-book:chapter-1",
            title="Test Chapter",
            content="<p>Test content</p>",
            book_id="storya:my-book",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="Test Book",
            author="Author"
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            content_files = [f for f in zf.namelist() if "content.opf" in f]
            assert len(content_files) > 0

            content_opf = zf.read(content_files[0]).decode("utf-8")
            # Verify identifier contains the expected format
            assert "ztruyen-storya-my-book-chapter-1" in content_opf

    def test_epub_toc_structure(self) -> None:
        """Test EPUB table of contents structure."""
        content = ChapterContent(
            id="storya:test:chapter",
            title="TOC Test Chapter",
            content="<p>Test content</p>",
            book_id="storya:test",
            chapter_order=1
        )

        epub_bytes = epub_builder.build_epub(
            chapter=content,
            book_title="TOC Test",
            author="Author"
        )

        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            # Check nav.xhtml exists (EPUB 3)
            nav_files = [f for f in zf.namelist() if "nav.xhtml" in f]
            assert len(nav_files) > 0

            nav_content = zf.read(nav_files[0]).decode("utf-8")
            assert "toc" in nav_content.lower() or "mục lục" in nav_content.lower()

    def test_build_epub_sync(
        self,
        sample_chapter_content: ChapterContent
    ) -> None:
        """Test synchronous EPUB build function."""
        epub_bytes = epub_builder.build_epub_sync(
            chapter=sample_chapter_content,
            book_title="Sync Test",
            author="Author"
        )

        assert epub_bytes is not None
        assert len(epub_bytes) > 0

        # Verify it's a valid EPUB
        with zipfile.ZipFile(io.BytesIO(epub_bytes), 'r') as zf:
            assert "mimetype" in zf.namelist()


class TestEPUBBuilderHelpers:
    """Tests for EPUB builder helper functions."""

    def test_sanitize_filename_basic(self) -> None:
        """Test basic filename sanitization."""
        assert epub_builder.sanitize_filename("normal_filename.txt") == "normal_filename.txt"
        assert epub_builder.sanitize_filename("file with spaces.txt") == "file_with_spaces.txt"

    def test_sanitize_filename_special_chars(self) -> None:
        """Test sanitization of special characters."""
        assert epub_builder.sanitize_filename("file<with>special:chars.txt") == "file_with_special_chars.txt"
        assert epub_builder.sanitize_filename("file|with|pipes.txt") == "file_with_pipes.txt"

    def test_sanitize_filename_vietnamese(self) -> None:
        """Test sanitization preserves Vietnamese characters."""
        result = epub_builder.sanitize_filename("truyện_việt_nam")
        assert "truyện" in result or "truyện" in result.lower()

    def test_sanitize_filename_empty(self) -> None:
        """Test sanitization of empty string."""
        assert epub_builder.sanitize_filename("") == "untitled"
        assert epub_builder.sanitize_filename("   ") == "untitled"

    def test_sanitize_filename_truncation(self) -> None:
        """Test filename truncation for long names."""
        long_name = "a" * 150
        result = epub_builder.sanitize_filename(long_name)
        assert len(result) <= 100

    def test_clean_html_content_br_tags(self) -> None:
        """Test HTML cleaning converts <br> to newlines."""
        result = epub_builder.clean_html_content("line1<br>line2<br/>line3")
        assert "\n" in result

    def test_clean_html_content_strips_scripts(self) -> None:
        """Test HTML cleaning removes script tags."""
        result = epub_builder.clean_html_content("<script>bad</script><p>good</p>")
        assert "script" not in result.lower()
        assert "good" in result

    def test_clean_html_content_strips_images(self) -> None:
        """Test HTML cleaning removes img tags."""
        result = epub_builder.clean_html_content("<img src='test.jpg'/><p>content</p>")
        assert "img" not in result.lower()
        assert "content" in result

    def test_clean_html_content_empty_returns_placeholder(self) -> None:
        """Test empty content returns placeholder."""
        result = epub_builder.clean_html_content("")
        assert "[Không có nội dung]" in result

    def test_convert_to_xhtml_structure(self) -> None:
        """Test XHTML conversion adds proper structure."""
        result = epub_builder.convert_to_xhtml("Test content", "Test Title")

        assert '<?xml version="1.0" encoding="utf-8"?>' in result
        assert '<html xmlns="http://www.w3.org/1999/xhtml"' in result
        assert 'xml:lang="vi"' in result
        assert 'lang="vi"' in result
        assert "<title>Test Title</title>" in result
        assert "<h2>Test Title</h2>" in result
        assert "Test content" in result

    def test_escape_xml(self) -> None:
        """Test XML escaping function."""
        assert epub_builder._escape_xml("&") == "&amp;"
        assert epub_builder._escape_xml("<") == "&lt;"
        assert epub_builder._escape_xml(">") == "&gt;"
        assert epub_builder._escape_xml('"') == "&quot;"
        assert epub_builder._escape_xml("'") == "&apos;"

    def test_escape_xml_vietnamese(self) -> None:
        """Test XML escaping with Vietnamese characters."""
        # Vietnamese chars should not be escaped
        result = epub_builder._escape_xml("Tác Giả: Nguyễn Nhật Ánh")
        assert "Tác Giả" in result
        assert "&" not in result  # No ampersand to escape

    def test_generate_epub_filename(self) -> None:
        """Test EPUB filename generation."""
        filename = epub_builder.generate_epub_filename("storya", "test-book", 1)
        assert filename.startswith("ztruyen__")
        assert "storya" in filename
        assert "test-book" in filename
        assert filename.endswith(".epub")

    def test_generate_epub_filename_pads_order(self) -> None:
        """Test EPUB filename pads chapter order."""
        filename1 = epub_builder.generate_epub_filename("storya", "book", 1)
        filename2 = epub_builder.generate_epub_filename("storya", "book", 42)
        filename3 = epub_builder.generate_epub_filename("storya", "book", 100)

        # Check zero-padding
        assert "0001" in filename1
        assert "0042" in filename2
        assert "0100" in filename3

    def test_resize_image_no_resize_needed(self) -> None:
        """Test image resize when dimensions are fine."""
        # Create a small test image (1x1 PNG)
        from PIL import Image
        img_bytes = io.BytesIO()
        small_img = Image.new("RGB", (100, 100), color="red")
        small_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        result = epub_builder.resize_image(img_bytes.getvalue(), 800, 1200)
        assert result == img_bytes.getvalue()

    def test_resize_image_converts_rgba(self) -> None:
        """Test image resize converts RGBA to RGB."""
        from PIL import Image
        img_bytes = io.BytesIO()
        rgba_img = Image.new("RGBA", (100, 100), color=(255, 0, 0, 128))
        rgba_img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        # Should convert to JPEG successfully
        result = epub_builder.resize_image(img_bytes.getvalue(), 800, 1200)
        assert result is not None
