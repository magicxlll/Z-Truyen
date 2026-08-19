"""Source Adapter for Storya.click (JSON REST API).

This adapter communicates with Storya.click v1 REST API to fetch
stories, chapters, and content for the Z-Truyen X3 project.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Optional

import httpx

from sources.base import (
    BaseSource,
    BookSummary,
    Chapter,
    ChapterContent,
)


class StoryaAdapter(BaseSource):
    """Source adapter for Storya.click using the JSON REST API."""

    id: str = "storya"
    name: str = "Storya"
    base_url: str = "https://storya.click"
    api_base: str = "https://storya.click/api/v1"

    def __init__(self) -> None:
        """Initialize the Storya adapter."""
        super().__init__()
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Accept": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _api_get(self, endpoint: str) -> dict[str, Any]:
        """Make an API request to the Storya endpoint.

        Args:
            endpoint: API endpoint path (e.g., '/stories/search?q=...')

        Returns:
            Parsed JSON response dict

        Raises:
            httpx.HTTPStatusError: If the API returns an error status code
        """
        url = f"{self.api_base}{endpoint}"
        client = await self._get_client()
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

    def _parse_author(self, author: Any) -> str:
        """Extract author name from various author field formats."""
        if isinstance(author, dict):
            return author.get("name", "Đang cập nhật")
        if isinstance(author, str):
            return author
        return "Đang cập nhật"

    def _parse_genres(self, genres: Any) -> list[str]:
        """Extract genre names from various genres field formats."""
        result = []
        if not genres:
            return result
        for g in genres:
            if isinstance(g, dict) and "name" in g:
                result.append(g["name"])
            elif isinstance(g, str):
                result.append(g)
        return result

    async def search(self, query: str, page: int = 1) -> list[BookSummary]:
        """Search stories by keyword.

        Args:
            query: Search keyword
            page: Page number (1-indexed)

        Returns:
            List of BookSummary matching the query
        """
        if not query or not query.strip():
            return await self.list_books(page)

        encoded_query = query.strip().replace(" ", "+")
        try:
            data = await self._api_get(f"/stories/search?q={encoded_query}")
        except httpx.HTTPStatusError:
            return []

        items = data.get("data", [])
        results = []
        for item in items:
            slug = item.get("slug") or ""
            if not slug:
                continue

            results.append(
                BookSummary(
                    id=self._build_book_id(slug),
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=self._parse_author(item.get("author")),
                    summary="",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                    source_id=self.id,
                    url=f"{self.base_url}/truyen/{slug}",
                )
            )
        return results

    async def list_books(self, page: int = 1) -> list[BookSummary]:
        """List latest stories.

        Args:
            page: Page number (1-indexed)

        Returns:
            List of BookSummary for latest stories
        """
        try:
            data = await self._api_get(f"/stories?page={page}&limit=20")
        except httpx.HTTPStatusError:
            return []

        items = data.get("data", [])
        results = []
        for item in items:
            slug = item.get("slug") or ""
            if not slug:
                continue

            results.append(
                BookSummary(
                    id=self._build_book_id(slug),
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=self._parse_author(item.get("author")),
                    summary="",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                    source_id=self.id,
                    url=f"{self.base_url}/truyen/{slug}",
                )
            )
        return results

    async def get_book(self, book_id: str) -> BookSummary:
        """Fetch detailed metadata for a single book.

        Args:
            book_id: Book identifier in format 'storya:<slug>'

        Returns:
            BookSummary with full metadata

        Raises:
            ValueError: If book_id format is invalid
        """
        prefix = f"{self.id}:"
        if not book_id.startswith(prefix):
            raise ValueError(f"Invalid book_id format: {book_id}. Expected format: '{prefix}<slug>'")

        slug = book_id[len(prefix):]
        if not slug:
            raise ValueError("Book ID is empty after prefix")

        data = await self._api_get(f"/stories/{slug}")
        d = data.get("data", {})

        return BookSummary(
            id=self._build_book_id(slug),
            title=d.get("title") or slug,
            author=self._parse_author(d.get("author")),
            summary=d.get("rewrittenDescription") or d.get("description") or "",
            cover_url=self._fix_cover_url(d.get("coverUrl")),
            source_id=self.id,
            url=f"{self.base_url}/truyen/{slug}",
        )

    async def list_chapters(self, book_id: str, page: int = 1) -> list[Chapter]:
        """Fetch paginated chapter list for a book.

        Args:
            book_id: Book identifier in format 'storya:<slug>'
            page: Page number (1-indexed)

        Returns:
            List of Chapter metadata
        """
        prefix = f"{self.id}:"
        if not book_id.startswith(prefix):
            return []
        slug = book_id[len(prefix):]
        if not slug:
            return []

        try:
            data = await self._api_get(
                f"/chapters/story/{slug}?page={page}&limit=100&minimal=true"
            )
        except httpx.HTTPStatusError:
            return []

        items = data.get("data", [])
        chapters = []
        for item in items:
            order = item.get("order", 1)
            chap_slug = item.get("slug") or f"chuong-{order}"

            chapters.append(
                Chapter(
                    id=self._build_chapter_id(slug, chap_slug),
                    title=item.get("title") or f"Chương {order}",
                    order=order,
                    book_id=book_id,
                    url=f"{self.base_url}/truyen/{slug}/{chap_slug}",
                )
            )
        return chapters

    async def get_chapter_content(self, chapter: Chapter) -> ChapterContent:
        """Fetch raw HTML content of a single chapter.

        Args:
            chapter: Chapter object with book_id and id

        Returns:
            ChapterContent with HTML content

        Raises:
            ValueError: If chapter.id format is invalid
        """
        parts = chapter.id.split(":")
        if len(parts) != 3:
            raise ValueError(
                f"Invalid chapter.id format: {chapter.id}. "
                f"Expected format: 'storya:<book_slug>:<chapter_slug>'"
            )

        story_slug = parts[1]
        chap_slug = parts[2]

        data = await self._api_get(f"/chapters/{story_slug}/{chap_slug}")
        item = data.get("data", {})

        # Use rewrittenContent preferentially - this is clean text
        content = (
            item.get("rewrittenContent")
            or item.get("content")
            or item.get("rawContent")
            or ""
        )

        return ChapterContent(
            id=chapter.id,
            title=item.get("title") or chapter.title,
            content=content,
            book_id=chapter.book_id,
            chapter_order=item.get("order", chapter.order),
        )

    async def get_genres(self) -> list[dict[str, str]]:
        """Fetch list of genre categories.

        Returns:
            List of dicts with 'id', 'name', 'slug', 'url' keys
        """
        try:
            data = await self._api_get("/genres")
        except httpx.HTTPStatusError:
            return []

        items = data.get("data", [])
        genres = []
        for item in items:
            name = item.get("name")
            slug = item.get("slug")
            if name and slug:
                genres.append({
                    "id": str(item.get("id", slug)),
                    "name": name,
                    "slug": slug,
                    "url": f"{self.base_url}/the-loai/{slug}",
                })
        return genres

    async def get_stories_by_genre(self, genre_slug: str, page: int = 1) -> list[BookSummary]:
        """Fetch stories by genre.

        Args:
            genre_slug: Genre slug identifier
            page: Page number (1-indexed)

        Returns:
            List of BookSummary for stories in the genre
        """
        try:
            data = await self._api_get(f"/genres/slug/{genre_slug}?page={page}&limit=20")
        except httpx.HTTPStatusError:
            return []

        items = data.get("data", [])
        results = []
        for item in items:
            slug = item.get("slug") or ""
            if not slug:
                continue

            results.append(
                BookSummary(
                    id=self._build_book_id(slug),
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=self._parse_author(item.get("author")),
                    summary="",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                    source_id=self.id,
                    url=f"{self.base_url}/truyen/{slug}",
                )
            )
        return results


# Convenience factory function
def create_storya_adapter() -> StoryaAdapter:
    """Create a new Storya adapter instance.

    Returns:
        New StoryaAdapter instance
    """
    return StoryaAdapter()
