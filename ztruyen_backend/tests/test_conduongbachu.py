"""Tests for ConDuongBaChu adapter and multi-source routing."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sources.conduongbachu import ConDuongBaChuAdapter, STORIES
from sources.base import BookSummary, Chapter, ChapterContent
from sources.storya import StoryaAdapter


# =============================================================================
# Test Data Fixtures
# =============================================================================

@pytest.fixture
def sample_wordpress_posts() -> list[dict]:
    """Sample WordPress REST API posts response."""
    return [
        {
            "id": 1001,
            "title": {"rendered": "Chương 1: Khởi Đầu"},
            "link": "https://conduongbachu.com/chapter-truyen/chuong-1/",
            "content": {"rendered": "<p>Nội dung chương 1.</p>"},
            "date": "2024-01-01T00:00:00"
        },
        {
            "id": 1002,
            "title": {"rendered": "Chương 2: Thử Thách"},
            "link": "https://conduongbachu.com/chapter-truyen/chuong-2/",
            "content": {"rendered": "<p>Nội dung chương 2.</p>"},
            "date": "2024-01-02T00:00:00"
        },
        {
            "id": 1003,
            "title": {"rendered": "Thông Tin Truyen"},
            "link": "https://conduongbachu.com/chapter-truyen/thong-tin/",
            "content": {"rendered": "<p>Thông tin về truyện.</p>"},
            "date": "2024-01-01T00:00:00"
        },
        {
            "id": 1004,
            "title": {"rendered": "Chương 3: Trở Lại"},
            "link": "https://conduongbachu.com/chapter-truyen/chuong-3/",
            "content": {"rendered": "<p>Nội dung chương 3.</p>"},
            "date": "2024-01-03T00:00:00"
        },
    ]


@pytest.fixture
def sample_chapter_html() -> str:
    """Sample chapter page HTML content."""
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Con Duong Ba Chu</title></head>
    <body>
        <article>
            <h1 class="entry-title">Chương 1: Khởi Đầu</h1>
            <div class="entry-content">
                <p>Đây là nội dung chương 1.</p>
                <p>Tiếp tục với nội dung tiếp theo.</p>
                <p>Và một đoạn nữa.</p>
            </div>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def sample_conduongbachu_book() -> BookSummary:
    """Sample ConDuongBaChu book for routing tests."""
    return BookSummary(
        id="conduongbachu:main",
        title="Con Đường Bá Chủ (Chính Truyện)",
        author="Quân Phượng Linh",
        summary="",
        cover_url=None,
        source_id="conduongbachu",
        url="https://conduongbachu.com/chapter-truyen"
    )


@pytest.fixture
def sample_storya_book() -> BookSummary:
    """Sample Storya book for routing tests."""
    return BookSummary(
        id="storya:test-book",
        title="Test Story",
        author="Test Author",
        summary="A test story",
        cover_url="https://cdn.storya.click/cover.jpg",
        source_id="storya",
        url="https://storya.click/truyen/test-book"
    )


@pytest.fixture
def sample_conduongbachu_chapter() -> Chapter:
    """Sample ConDuongBaChu chapter."""
    return Chapter(
        id="conduongbachu:main:1",
        title="Chương 1: Khởi Đầu",
        order=1,
        book_id="conduongbachu:main",
        url="https://conduongbachu.com/chapter-truyen/chuong-1/"
    )


# =============================================================================
# Test Classes
# =============================================================================

class TestConDuongBaChuAdapter:
    """Tests for ConDuongBaChuAdapter class."""

    def test_adapter_creation(self) -> None:
        """Verify adapter can be created."""
        adapter = ConDuongBaChuAdapter()

        assert adapter.id == "conduongbachu"
        assert adapter.name == "Con Đường Bá Chủ"
        assert adapter.base_url == "https://conduongbachu.com"
        assert adapter.api_base == "https://conduongbachu.com/wp-json/wp/v2"
        assert adapter._client is None

    def test_adapter_has_required_headers(self) -> None:
        """Verify adapter has required HTTP headers."""
        adapter = ConDuongBaChuAdapter()
        headers = adapter._headers

        assert "Referer" in headers
        assert "conduongbachu.com" in headers["Referer"]
        assert "Accept" in headers
        assert "User-Agent" in headers

    def test_adapter_id_constant(self) -> None:
        """Verify adapter ID is correct."""
        adapter = ConDuongBaChuAdapter()
        assert adapter.id == "conduongbachu"

    @pytest.mark.asyncio
    async def test_adapter_close_when_client_exists(self) -> None:
        """Verify close() cleans up client properly."""
        adapter = ConDuongBaChuAdapter()
        client = await adapter._get_client()
        assert adapter._client is not None

        await adapter.close()
        assert adapter._client is None

    @pytest.mark.asyncio
    async def test_adapter_close_when_no_client(self) -> None:
        """Verify close() handles no client gracefully."""
        adapter = ConDuongBaChuAdapter()
        assert adapter._client is None

        # Should not raise any error
        await adapter.close()
        assert adapter._client is None


class TestConDuongBaChuListBooks:
    """Tests for list_books functionality."""

    def test_stories_count(self) -> None:
        """Verify there are 4 novels in the series."""
        assert len(STORIES) == 4

    def test_stories_have_required_fields(self) -> None:
        """Verify all stories have required fields."""
        for story in STORIES:
            assert "id" in story
            assert "cat_id" in story
            assert "title" in story
            assert "slug" in story
            assert "author" in story

    def test_stories_have_unique_ids(self) -> None:
        """Verify all story IDs are unique."""
        story_ids = [s["id"] for s in STORIES]
        assert len(story_ids) == len(set(story_ids))

    def test_stories_expected_ids(self) -> None:
        """Verify expected story IDs exist."""
        story_ids = [s["id"] for s in STORIES]
        expected_ids = ["main", "bat-hu-than-chien", "van-dao-than-chu", "chua-te-chi-lo"]
        for expected_id in expected_ids:
            assert expected_id in story_ids

    @pytest.mark.asyncio
    async def test_list_books_returns_all_books(self) -> None:
        """Verify list_books returns all 4 novels."""
        adapter = ConDuongBaChuAdapter()
        books = await adapter.list_books()

        assert len(books) == 4

    @pytest.mark.asyncio
    async def test_list_books_all_have_correct_source_id(self) -> None:
        """Verify all books have conduongbachu source_id."""
        adapter = ConDuongBaChuAdapter()
        books = await adapter.list_books()

        for book in books:
            assert book.source_id == "conduongbachu"

    @pytest.mark.asyncio
    async def test_list_books_contains_main_story(self) -> None:
        """Verify main story is in the list."""
        adapter = ConDuongBaChuAdapter()
        books = await adapter.list_books()

        book_ids = [b.id for b in books]
        assert "conduongbachu:main" in book_ids

        main_book = next(b for b in books if b.id == "conduongbachu:main")
        assert "Con Đường Bá Chủ" in main_book.title

    @pytest.mark.asyncio
    async def test_list_books_contains_spinnoffs(self) -> None:
        """Verify spin-off stories are in the list."""
        adapter = ConDuongBaChuAdapter()
        books = await adapter.list_books()

        book_ids = [b.id for b in books]

        # Check spin-offs exist
        assert "conduongbachu:bat-hu-than-chien" in book_ids
        assert "conduongbachu:van-dao-than-chu" in book_ids
        assert "conduongbachu:chua-te-chi-lo" in book_ids

    @pytest.mark.asyncio
    async def test_list_books_page_parameter(self) -> None:
        """Verify list_books handles page parameter (ignored but accepted)."""
        adapter = ConDuongBaChuAdapter()

        # Page parameter should not affect results (single-page source)
        books_page1 = await adapter.list_books(page=1)
        books_page2 = await adapter.list_books(page=2)

        assert books_page1 == books_page2


class TestConDuongBaChuIDGeneration:
    """Tests for ID generation and parsing."""

    def test_build_book_id(self) -> None:
        """Test ID generation for books."""
        adapter = ConDuongBaChuAdapter()

        book_id = adapter._build_book_id("main")
        assert book_id == "conduongbachu:main"

        book_id = adapter._build_book_id("bat-hu-than-chien")
        assert book_id == "conduongbachu:bat-hu-than-chien"

    def test_build_chapter_id(self) -> None:
        """Test chapter ID generation."""
        adapter = ConDuongBaChuAdapter()

        chapter_id = adapter._build_chapter_id("main", "1")
        assert chapter_id == "conduongbachu:main:1"

        chapter_id = adapter._build_chapter_id("bat-hu-than-chien", "42")
        assert chapter_id == "conduongbachu:bat-hu-than-chien:42"

    def test_parse_book_id(self) -> None:
        """Test extracting story_id from book ID."""
        adapter = ConDuongBaChuAdapter()

        # Test via get_book method
        book = adapter._get_story_by_id("main")
        assert book is not None
        assert book["id"] == "main"

        book = adapter._get_story_by_id("bat-hu-than-chien")
        assert book is not None
        assert book["id"] == "bat-hu-than-chien"

    def test_parse_invalid_book_id(self) -> None:
        """Test that invalid book ID returns None."""
        adapter = ConDuongBaChuAdapter()

        book = adapter._get_story_by_id("nonexistent")
        assert book is None

    @pytest.mark.asyncio
    async def test_get_book_valid_id(self) -> None:
        """Test get_book with valid book ID."""
        adapter = ConDuongBaChuAdapter()

        book = await adapter.get_book("conduongbachu:main")
        assert book.id == "conduongbachu:main"
        assert book.title == "Con Đường Bá Chủ (Chính Truyện)"
        assert book.author == "Quân Phượng Linh"

    @pytest.mark.asyncio
    async def test_get_book_invalid_prefix(self) -> None:
        """Test get_book with wrong prefix raises ValueError."""
        adapter = ConDuongBaChuAdapter()

        with pytest.raises(ValueError, match="Invalid book_id format"):
            await adapter.get_book("storya:main")

    @pytest.mark.asyncio
    async def test_get_book_unknown_story(self) -> None:
        """Test get_book with unknown story raises ValueError."""
        adapter = ConDuongBaChuAdapter()

        with pytest.raises(ValueError, match="Story not found"):
            await adapter.get_book("conduongbachu:unknown-story")


class TestConDuongBaChuChapterDetection:
    """Tests for chapter detection logic."""

    def test_is_chapter_post_with_chuong_in_title(self) -> None:
        """Test chapter detection when 'Chương' is in title."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Chương 1: Khởi Đầu"},
            "link": "https://example.com/some-page/"
        }
        assert adapter._is_chapter_post(post) is True

    def test_is_chapter_post_with_chuong_in_url(self) -> None:
        """Test chapter detection when '/chuong-' is in URL."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Some Other Page"},
            "link": "https://example.com/chuong-42/"
        }
        assert adapter._is_chapter_post(post) is True

    def test_is_chapter_post_not_chapter(self) -> None:
        """Test non-chapter post is not detected as chapter."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Thông Tin Truyen"},
            "link": "https://example.com/thong-tin/"
        }
        assert adapter._is_chapter_post(post) is False

    def test_is_chapter_post_empty_title(self) -> None:
        """Test chapter detection with empty title."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": ""},
            "link": "https://example.com/chuong-1/"
        }
        assert adapter._is_chapter_post(post) is True

    def test_is_chapter_post_missing_fields(self) -> None:
        """Test chapter detection with missing fields."""
        adapter = ConDuongBaChuAdapter()

        # Missing title - should return False (no "Chương" keyword)
        post = {"link": "https://example.com/page/"}
        assert adapter._is_chapter_post(post) is False

        # Missing link but has "Chương" in title - should return True
        # The implementation checks title first
        post = {"title": {"rendered": "Chương 1"}}
        assert adapter._is_chapter_post(post) is True

    def test_parse_chapter_number_from_title(self) -> None:
        """Test parsing chapter number from title."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Chương 123: Tiêu Đề"},
            "link": "https://example.com/page/"
        }
        assert adapter._parse_chapter_number(post) == 123

    def test_parse_chapter_number_from_url(self) -> None:
        """Test parsing chapter number from URL."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Some Title"},
            "link": "https://example.com/chapter-truyen/chuong-456/"
        }
        assert adapter._parse_chapter_number(post) == 456

    def test_parse_chapter_number_prefers_title(self) -> None:
        """Test that title is preferred over URL for parsing."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Chương 100"},
            "link": "https://example.com/chuong-200/"
        }
        # Title is parsed first
        assert adapter._parse_chapter_number(post) == 100

    def test_parse_chapter_number_invalid(self) -> None:
        """Test parsing with no valid chapter number."""
        adapter = ConDuongBaChuAdapter()

        post = {
            "title": {"rendered": "Thông Tin"},
            "link": "https://example.com/about/"
        }
        assert adapter._parse_chapter_number(post) is None

    def test_parse_chapter_order(self) -> None:
        """Test parsing chapter order from chapter ID."""
        adapter = ConDuongBaChuAdapter()

        chapter_id = "conduongbachu:main:42"
        assert adapter._parse_chapter_order(chapter_id) == 42

        chapter_id = "conduongbachu:bat-hu-than-chien:1"
        assert adapter._parse_chapter_order(chapter_id) == 1

    def test_parse_chapter_order_invalid(self) -> None:
        """Test parsing chapter order with invalid ID."""
        adapter = ConDuongBaChuAdapter()

        chapter_id = "invalid"
        assert adapter._parse_chapter_order(chapter_id) == 0

        chapter_id = "conduongbachu:main:abc"
        assert adapter._parse_chapter_order(chapter_id) == 0


class TestConDuongBaChuAPI:
    """Tests for ConDuongBaChuAdapter API methods with mocked HTTP responses."""

    @pytest.mark.asyncio
    async def test_list_chapters_returns_chapters_only(
        self,
        sample_wordpress_posts: list[dict]
    ) -> None:
        """Test WordPress API parsing returns only chapters."""
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_wordpress_posts

            chapters = await adapter.list_chapters("conduongbachu:main")

            # Should return 3 chapters, not the "Thông Tin Truyen" post
            assert len(chapters) == 3

            # Verify chapters are in order
            assert chapters[0].title == "Chương 1: Khởi Đầu"
            assert chapters[1].title == "Chương 2: Thử Thách"
            assert chapters[2].title == "Chương 3: Trở Lại"

    @pytest.mark.asyncio
    async def test_list_chapters_invalid_book_id(self) -> None:
        """Test list_chapters with invalid book ID returns empty list."""
        adapter = ConDuongBaChuAdapter()

        chapters = await adapter.list_chapters("storya:some-book")
        assert chapters == []

    @pytest.mark.asyncio
    async def test_list_chapters_unknown_story(self) -> None:
        """Test list_chapters with unknown story returns empty list."""
        adapter = ConDuongBaChuAdapter()

        chapters = await adapter.list_chapters("conduongbachu:unknown-story")
        assert chapters == []

    @pytest.mark.asyncio
    async def test_list_chapters_chapter_ids(
        self,
        sample_wordpress_posts: list[dict]
    ) -> None:
        """Test chapter IDs are correctly formatted."""
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_wordpress_posts

            chapters = await adapter.list_chapters("conduongbachu:main")

            # Check chapter IDs
            assert chapters[0].id == "conduongbachu:main:1"
            assert chapters[1].id == "conduongbachu:main:2"
            assert chapters[2].id == "conduongbachu:main:3"

    @pytest.mark.asyncio
    async def test_list_chapters_book_id_reference(
        self,
        sample_wordpress_posts: list[dict]
    ) -> None:
        """Test chapters reference the correct book_id."""
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_wordpress_posts

            chapters = await adapter.list_chapters("conduongbachu:bat-hu-than-chien")

            # All chapters should reference the bat-hu-than-chien book
            for chapter in chapters:
                assert chapter.book_id == "conduongbachu:bat-hu-than-chien"

    @pytest.mark.asyncio
    async def test_list_chapters_handles_empty_response(self) -> None:
        """Test list_chapters handles empty API response."""
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            chapters = await adapter.list_chapters("conduongbachu:main")
            assert chapters == []

    @pytest.mark.asyncio
    async def test_get_chapter_content_uses_direct_url(
        self,
        sample_chapter_html: str
    ) -> None:
        """Test chapter content is fetched from direct URL."""
        adapter = ConDuongBaChuAdapter()
        chapter = Chapter(
            id="conduongbachu:main:1",
            title="Chương 1",
            order=1,
            book_id="conduongbachu:main",
            url="https://conduongbachu.com/chapter-truyen/chuong-1/"
        )

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = sample_chapter_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            content = await adapter.get_chapter_content(chapter)

            # Verify it tries to fetch from direct chapter URL
            call_args = mock_client.get.call_args[0][0]
            assert "chuong-1" in call_args
            # Content should be extracted (entry-content div content)
            assert len(content.content) > 0

    @pytest.mark.asyncio
    async def test_get_chapter_content_extracts_entry_content(
        self,
        sample_chapter_html: str
    ) -> None:
        """Test entry-content is correctly extracted."""
        adapter = ConDuongBaChuAdapter()
        chapter = Chapter(
            id="conduongbachu:main:42",
            title="Chương 42",
            order=42,
            book_id="conduongbachu:main",
            url="https://conduongbachu.com/chapter-truyen/chuong-42/"
        )

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = sample_chapter_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            content = await adapter.get_chapter_content(chapter)

            # Content should be extracted (entry-content div content)
            assert len(content.content) > 0
            assert "Đây là nội dung" in content.content

    @pytest.mark.asyncio
    async def test_get_chapter_content_invalid_id_format(self) -> None:
        """Test chapter content with invalid ID format raises ValueError."""
        adapter = ConDuongBaChuAdapter()
        chapter = Chapter(
            id="invalid-id",
            title="Chapter",
            order=1,
            book_id="conduongbachu:main",
            url="https://example.com"
        )

        with pytest.raises(ValueError, match="Invalid chapter.id format"):
            await adapter.get_chapter_content(chapter)

    @pytest.mark.asyncio
    async def test_get_chapter_content_includes_book_id(
        self,
        sample_chapter_html: str
    ) -> None:
        """Test chapter content includes correct book_id."""
        adapter = ConDuongBaChuAdapter()
        chapter = Chapter(
            id="conduongbachu:bat-hu-than-chien:10",
            title="Chương 10",
            order=10,
            book_id="conduongbachu:bat-hu-than-chien",
            url="https://conduongbachu.com/ngoai-truyen/chuong-10/"
        )

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.text = sample_chapter_html
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            content = await adapter.get_chapter_content(chapter)

            assert content.book_id == "conduongbachu:bat-hu-than-chien"

    @pytest.mark.asyncio
    async def test_fetch_posts_pagination(
        self,
        sample_wordpress_posts: list[dict]
    ) -> None:
        """Test _fetch_posts handles pagination correctly."""
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = sample_wordpress_posts[:2]  # Less than 100
            mock_response.raise_for_status = MagicMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            posts = await adapter._fetch_posts(cat_id=3)

            assert len(posts) == 2
            # Verify pagination params in URL
            call_args = str(mock_client.get.call_args)
            assert "categories=3" in call_args
            assert "per_page=100" in call_args
            assert "order=asc" in call_args

    @pytest.mark.asyncio
    async def test_fetch_posts_handles_error(self) -> None:
        """Test _fetch_posts handles HTTP errors gracefully."""
        import httpx
        adapter = ConDuongBaChuAdapter()

        with patch.object(adapter, '_get_client') as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            ))
            mock_get_client.return_value = mock_client

            posts = await adapter._fetch_posts(cat_id=999)
            assert posts == []


class TestConDuongBaChuSearch:
    """Tests for search functionality."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_list(self) -> None:
        """Test search is not supported and returns empty list."""
        adapter = ConDuongBaChuAdapter()

        results = await adapter.search("Con Đường Bá Chủ")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_any_query(self) -> None:
        """Test search returns empty regardless of query."""
        adapter = ConDuongBaChuAdapter()

        results = await adapter.search("any query")
        assert results == []

        results = await adapter.search("")
        assert results == []


class TestConDuongBaChuFactory:
    """Tests for factory function."""

    def test_create_conduongbachu_adapter(self) -> None:
        """Test factory function creates correct adapter."""
        from sources.conduongbachu import create_conduongbachu_adapter

        adapter = create_conduongbachu_adapter()
        assert isinstance(adapter, ConDuongBaChuAdapter)
        assert adapter.id == "conduongbachu"


class TestMultiSourceRouting:
    """Tests for multi-source routing functionality."""

    @pytest.mark.asyncio
    async def test_storya_book_routing(self) -> None:
        """Test storya books route correctly."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {
                "data": {
                    "slug": "test-story",
                    "title": "Test Story",
                    "author": {"name": "Test Author"},
                    "rewrittenDescription": "Description",
                    "description": "Desc"
                }
            }

            book = await adapter.get_book("storya:test-story")

            assert book.id == "storya:test-story"
            assert book.source_id == "storya"

    @pytest.mark.asyncio
    async def test_conduongbachu_book_routing(self) -> None:
        """Test ConDuongBaChu books route correctly."""
        adapter = ConDuongBaChuAdapter()

        book = await adapter.get_book("conduongbachu:main")

        assert book.id == "conduongbachu:main"
        assert book.source_id == "conduongbachu"

    @pytest.mark.asyncio
    async def test_mixed_catalog_combines_sources(self) -> None:
        """Test combined OPDS catalog contains books from both sources."""
        from opds_renderer import render_root_catalog

        storya_book = BookSummary(
            id="storya:test-book",
            title="Test Story",
            author="Test Author",
            summary="Summary",
            source_id="storya",
            url="https://storya.click/truyen/test-book"
        )

        conduongbachu_book = BookSummary(
            id="conduongbachu:main",
            title="Con Đường Bá Chủ",
            author="Quân Phượng Linh",
            summary="",
            source_id="conduongbachu",
            url="https://conduongbachu.com/chapter-truyen"
        )

        all_books = [storya_book, conduongbachu_book]
        xml_content = render_root_catalog(all_books, "http://testserver")

        # Both books should appear
        assert "storya:test-book" in xml_content
        assert "conduongbachu:main" in xml_content
        assert "Test Story" in xml_content
        assert "Con Đường Bá Chủ" in xml_content

    def test_storya_id_format(self) -> None:
        """Test storya ID format."""
        adapter = StoryaAdapter()
        book_id = adapter._build_book_id("dao-hai-tac")
        assert book_id == "storya:dao-hai-tac"
        assert book_id.startswith("storya:")

    def test_conduongbachu_id_format(self) -> None:
        """Test ConDuongBaChu ID format."""
        adapter = ConDuongBaChuAdapter()
        book_id = adapter._build_book_id("main")
        assert book_id == "conduongbachu:main"
        assert book_id.startswith("conduongbachu:")

    def test_chapter_ids_distinct_by_source(self) -> None:
        """Test chapter IDs are distinct between sources."""
        storya_adapter = StoryaAdapter()
        cdb_adapter = ConDuongBaChuAdapter()

        storya_chapter = storya_adapter._build_chapter_id("test-book", "chapter-1")
        cdb_chapter = cdb_adapter._build_chapter_id("main", "1")

        assert storya_chapter.startswith("storya:")
        assert cdb_chapter.startswith("conduongbachu:")
        assert storya_chapter != cdb_chapter

    def test_source_id_prefixes_are_unique(self) -> None:
        """Test source ID prefixes are unique."""
        storya_adapter = StoryaAdapter()
        cdb_adapter = ConDuongBaChuAdapter()

        assert storya_adapter.id != cdb_adapter.id
        assert "storya" not in cdb_adapter.id
        assert "conduongbachu" not in storya_adapter.id

    @pytest.mark.asyncio
    async def test_storya_supports_search(self) -> None:
        """Test storya adapter supports search."""
        adapter = StoryaAdapter()

        with patch.object(adapter, '_api_get', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = {"data": []}

            results = await adapter.search("test query")
            assert mock_api.called

    @pytest.mark.asyncio
    async def test_conduongbachu_does_not_support_search(self) -> None:
        """Test ConDuongBaChu adapter does not support search."""
        adapter = ConDuongBaChuAdapter()

        results = await adapter.search("test query")
        assert results == []


class TestConDuongBaChuEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_list_chapters_handles_non_numeric_chapter(self) -> None:
        """Test list_chapters handles posts without numeric chapter."""
        adapter = ConDuongBaChuAdapter()

        posts = [
            {
                "id": 1,
                "title": {"rendered": "Chương ABC: Not Numeric"},
                "link": "https://example.com/chuong-abc/"
            },
            {
                "id": 2,
                "title": {"rendered": "Chương 1: Valid"},
                "link": "https://example.com/chuong-1/"
            }
        ]

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = posts
            chapters = await adapter.list_chapters("conduongbachu:main")

            # Only the numeric chapter should be included
            assert len(chapters) == 1
            assert chapters[0].title == "Chương 1: Valid"

    @pytest.mark.asyncio
    async def test_extract_entry_content_empty_html(self) -> None:
        """Test _extract_entry_content handles missing content."""
        adapter = ConDuongBaChuAdapter()

        html = "<html><body>No entry-content here</body></html>"
        content = adapter._extract_entry_content(html)
        assert content == ""

    @pytest.mark.asyncio
    async def test_extract_entry_content_multiline(self) -> None:
        """Test _extract_entry_content handles multiline content."""
        adapter = ConDuongBaChuAdapter()

        html = '''
        <div class="entry-content">
            <p>First paragraph</p>
            <p>Second paragraph</p>
            <p>Third paragraph</p>
        </div>
        '''
        content = adapter._extract_entry_content(html)
        assert "First paragraph" in content
        assert "Second paragraph" in content
        assert "Third paragraph" in content

    @pytest.mark.asyncio
    async def test_extract_entry_content_with_attributes(self) -> None:
        """Test _extract_entry_content handles div with attributes."""
        adapter = ConDuongBaChuAdapter()

        # Test with exact class="entry-content" and other attributes
        html = '''
        <div class="entry-content" id="content" style="margin:10px">
            <p>Content here</p>
        </div>
        '''
        content = adapter._extract_entry_content(html)
        assert "Content here" in content

        # Test with additional attributes after class
        html_with_attrs = '''
        <div class="entry-content" data-id="123">
            <p>With data attribute</p>
        </div>
        '''
        content = adapter._extract_entry_content(html_with_attrs)
        assert "With data attribute" in content

    @pytest.mark.asyncio
    async def test_title_html_stripping(self) -> None:
        """Test titles have HTML stripped."""
        adapter = ConDuongBaChuAdapter()

        posts = [
            {
                "id": 1,
                "title": {"rendered": "Chương 1: <strong>Tiêu Đề</strong>"},
                "link": "https://example.com/chuong-1/"
            }
        ]

        with patch.object(adapter, '_fetch_posts', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = posts
            chapters = await adapter.list_chapters("conduongbachu:main")

            assert "<strong>" not in chapters[0].title
            assert "Chương 1" in chapters[0].title
            assert "Tiêu Đề" in chapters[0].title
