"""Source Adapter for ConDuongBaChu.com (WordPress REST API).

This adapter communicates with ConDuongBaChu.com WordPress REST API to fetch
chapters and content for the "Con Đường Bá Chủ" novel series and its spinoffs.

Note: This is a dedicated source for a single novel series. No dynamic search is available.
"""

from __future__ import annotations

import re
from typing import Any, Optional

import httpx

from sources.base import (
    BaseSource,
    BookSummary,
    Chapter,
    ChapterContent,
)


# Hardcoded stories - this site only serves Con Duong Ba Chu and spinoffs
STORIES = [
    {
        "id": "main",
        "cat_id": 3,
        "title": "Con Đường Bá Chủ (Chính Truyện)",
        "slug": "chapter-truyen",
        "author": "Quân Phượng Linh",
    },
    {
        "id": "bat-hu-than-chien",
        "cat_id": 12,
        "title": "Ngoại Truyện: Bất Hủ Thần Chiến",
        "slug": "ngoai-truyen",
        "author": "Quân Phượng Linh",
    },
    {
        "id": "van-dao-than-chu",
        "cat_id": 14,
        "title": "Ngoại Truyện: Vạn Đạo Thần Chủ",
        "slug": "ngoai-truyen-van-dao-than-chu",
        "author": "Quân Phượng Linh",
    },
    {
        "id": "chua-te-chi-lo",
        "cat_id": 15,
        "title": "Ngoại Truyện: Chúa Tể Chi Lộ",
        "slug": "ngoai-truyen-chua-te-chi-lo",
        "author": "Quân Phượng Linh",
    },
]


class ConDuongBaChuAdapter(BaseSource):
    """Source adapter for ConDuongBaChu.com using WordPress REST API."""

    id: str = "conduongbachu"
    name: str = "Con Đường Bá Chủ"
    base_url: str = "https://conduongbachu.com"
    api_base: str = "https://conduongbachu.com/wp-json/wp/v2"

    # HTTP headers for requests
    _headers: dict[str, str] = {
        "Referer": "https://conduongbachu.com/",
        "Accept": "text/html,application/xhtml+xml,application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    }

    def __init__(self) -> None:
        """Initialize the ConDuongBaChu adapter."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers=self._headers,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _get_story_by_id(self, story_id: str) -> Optional[dict[str, Any]]:
        """Get story metadata by story ID.

        Args:
            story_id: Story identifier (e.g., 'main', 'bat-hu-than-chien')

        Returns:
            Story dict or None if not found
        """
        for story in STORIES:
            if story["id"] == story_id:
                return story
        return None

    async def _fetch_posts(
        self, cat_id: int, page: int = 1, per_page: int = 100
    ) -> list[dict[str, Any]]:
        """Fetch posts from WordPress REST API.

        Args:
            cat_id: WordPress category ID
            page: Page number (1-indexed)
            per_page: Number of posts per page (max 100)

        Returns:
            List of post objects from WordPress API
        """
        client = await self._get_client()
        url = (
            f"{self.api_base}/posts"
            f"?categories={cat_id}"
            f"&per_page={per_page}"
            f"&page={page}"
            f"&order=asc"
            f"&orderby=date"
        )
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            return []

    def _is_chapter_post(self, post: dict[str, Any]) -> bool:
        """Check if a post is a chapter (not info page).

        A post is considered a chapter if:
        - Title contains "Chương"
        - URL contains "/chuong-"

        Args:
            post: WordPress post object

        Returns:
            True if post is a chapter
        """
        title = post.get("title", {}).get("rendered", "")
        link = post.get("link", "")

        if "Chương" in title:
            return True
        if "/chuong-" in link:
            return True

        return False

    def _parse_chapter_number(self, post: dict[str, Any]) -> Optional[int]:
        """Parse chapter number from post title or URL.

        Args:
            post: WordPress post object

        Returns:
            Chapter number or None if cannot parse
        """
        title = post.get("title", {}).get("rendered", "")
        link = post.get("link", "")

        # Try to extract from title: "Chương 123: Tiêu Đề" or "Chương 1234"
        title_match = re.search(r"Chương\s+(\d+)", title)
        if title_match:
            return int(title_match.group(1))

        # Try to extract from URL: /chuong-123/
        url_match = re.search(r"/chuong-(\d+)/?", link)
        if url_match:
            return int(url_match.group(1))

        return None

    async def search(self, query: str, page: int = 1) -> list[BookSummary]:
        """Search is not supported on this source.

        This source only contains the Con Đường Bá Chủ series.
        Search returns empty list - use list_books() instead.

        Args:
            query: Search keyword (ignored)
            page: Page number (ignored)

        Returns:
            Empty list (no search functionality)
        """
        # This source doesn't support search - it's dedicated to one series
        return []

    async def list_books(self, page: int = 1) -> list[BookSummary]:
        """List all available books in the series.

        Args:
            page: Page number (1-indexed)

        Returns:
            List of BookSummary for all books in the series
        """
        results = []
        for story in STORIES:
            story_id = story["id"]
            results.append(
                BookSummary(
                    id=self._build_book_id(story_id),
                    title=story["title"],
                    author=story.get("author", "Quân Phượng Linh"),
                    summary="",
                    cover_url=None,
                    source_id=self.id,
                    url=f"{self.base_url}/{story['slug']}",
                )
            )
        return results

    async def get_book(self, book_id: str) -> BookSummary:
        """Fetch detailed metadata for a single book.

        Args:
            book_id: Book identifier in format 'conduongbachu:<story_id>'

        Returns:
            BookSummary with metadata

        Raises:
            ValueError: If book_id format is invalid or story not found
        """
        prefix = f"{self.id}:"
        if not book_id.startswith(prefix):
            raise ValueError(
                f"Invalid book_id format: {book_id}. Expected format: '{prefix}<story_id>'"
            )

        story_id = book_id[len(prefix):]
        story = self._get_story_by_id(story_id)

        if story is None:
            raise ValueError(f"Story not found: {story_id}")

        return BookSummary(
            id=self._build_book_id(story_id),
            title=story["title"],
            author=story.get("author", "Quân Phượng Linh"),
            summary="",
            cover_url=None,
            source_id=self.id,
            url=f"{self.base_url}/{story['slug']}",
        )

    async def list_chapters(self, book_id: str, page: int = 1, max_pages: int = 3) -> list[Chapter]:
        """Fetch paginated chapter list for a book.

        Args:
            book_id: Book identifier in format 'conduongbachu:<story_id>'
            page: Page number (1-indexed)
            max_pages: Maximum number of pages to fetch (default 3 = 300 chapters max)

        Returns:
            List of Chapter metadata
        """
        prefix = f"{self.id}:"
        if not book_id.startswith(prefix):
            return []
        story_id = book_id[len(prefix):]

        story = self._get_story_by_id(story_id)
        if story is None:
            return []

        cat_id = story["cat_id"]

        # Fetch chapters (limited to max_pages to prevent timeouts)
        all_posts = []
        current_page = 1
        while current_page <= max_pages:
            posts = await self._fetch_posts(cat_id, page=current_page)
            if not posts:
                break
            all_posts.extend(posts)

            # WordPress REST API returns empty list when no more pages
            if len(posts) < 100:
                break
            current_page += 1

        # If this is page 1 and we have more pages, note total count
        total_chapters = len(all_posts)

        chapters = []
        order = 0
        for post in all_posts:
            if not self._is_chapter_post(post):
                continue

            chapter_num = self._parse_chapter_number(post)
            if chapter_num is None:
                continue

            order += 1

            title = post.get("title", {}).get("rendered", "")
            link = post.get("link", "")

            # Clean HTML from title
            clean_title = re.sub(r"<[^>]+>", "", title).strip()

            chapters.append(
                Chapter(
                    id=self._build_chapter_id(story_id, str(chapter_num)),
                    title=clean_title,
                    order=order,
                    book_id=book_id,
                    url=link,
                )
            )

        # Sort by chapter number
        chapters.sort(key=lambda c: self._parse_chapter_order(c.id))

        return chapters

    def _parse_chapter_order(self, chapter_id: str) -> int:
        """Parse chapter order from chapter ID.

        Args:
            chapter_id: Chapter identifier in format 'conduongbachu:<story_id>:<chapter_num>'

        Returns:
            Chapter number
        """
        parts = chapter_id.split(":")
        if len(parts) >= 3:
            try:
                return int(parts[2])
            except ValueError:
                pass
        return 0

    async def get_chapter_content(self, chapter: Chapter) -> ChapterContent:
        """Fetch raw HTML content of a single chapter.

        Args:
            chapter: Chapter object with id and url

        Returns:
            ChapterContent with HTML content

        Raises:
            ValueError: If chapter.id format is invalid or chapter not found
        """
        parts = chapter.id.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid chapter.id format: {chapter.id}. "
                f"Expected format: 'conduongbachu:<story_id>:<chapter_num>'"
            )

        story_id = parts[1]
        chapter_num = parts[2]

        # Fetch from WordPress REST API - more reliable than scraping
        story = self._get_story_by_id(story_id)
        content = ""

        if story:
            # Try to find the specific chapter in API response
            # The API returns chapters ordered by date
            posts = await self._fetch_posts(story["cat_id"], per_page=100)
            for post in posts:
                post_chapter_num = self._parse_chapter_number(post)
                if post_chapter_num == int(chapter_num):
                    content = post.get("content", {}).get("rendered", "")
                    break

        # Fallback: try direct URL with correct format (e.g., /chuong-1234-title/)
        if not content:
            # Fetch from the link stored in chapter if available
            if chapter.url:
                client = await self._get_client()
                try:
                    resp = await client.get(chapter.url)
                    resp.raise_for_status()
                    content = self._extract_entry_content(resp.text)
                except httpx.HTTPStatusError:
                    pass

        return ChapterContent(
            id=chapter.id,
            title=chapter.title,
            content=content or "",
            book_id=chapter.book_id,
            chapter_order=int(chapter_num) if chapter_num.isdigit() else chapter.order,
        )

    def _extract_entry_content(self, html: str) -> str:
        """Extract content from WordPress entry-content div.

        Args:
            html: HTML page content

        Returns:
            Extracted content or empty string
        """
        # Match <div class="entry-content">...</div>
        pattern = r'<div\s+class="entry-content"[^>]*>(.*?)</div>'
        match = re.search(pattern, html, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""


# Convenience factory function
def create_conduongbachu_adapter() -> ConDuongBaChuAdapter:
    """Create a new ConDuongBaChu adapter instance.

    Returns:
        New ConDuongBaChuAdapter instance
    """
    return ConDuongBaChuAdapter()
