"""Source Adapter for Storya.click (JSON REST API)."""

import asyncio
from typing import Any
from urllib.parse import quote_plus
from app.fetcher.client import http_client, HttpClient
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent, GenreItem
from app.domain.ids import build_story_id
from app.domain.sanitizer import sanitize_chapter_html
from app.logging import log_scraper_event, logger


class StoryaClickAdapter:
    """Scraper adapter communicating with Storya.click v1 REST API."""

    id: str = "storyaclick"
    name: str = "Storya"
    base_url: str = "https://storya.click"
    api_base: str = "https://storya.click/api/v1"
    supports_login: bool = False

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or http_client

    def _fix_cover_url(self, cover: str | None) -> str | None:
        if not cover:
            return None
        if cover.startswith("/"):
            return f"{self.base_url}{cover}"
        return cover

    async def _api_get(self, endpoint: str) -> dict[str, Any]:
        url = f"{self.api_base}{endpoint}"
        log_scraper_event(self.id, f"GET {url}")
        resp = await self.client.get(url, headers={"Accept": "application/json"})
        if resp.status_code >= 400:
            raise RuntimeError(f"Storya API returned HTTP {resp.status_code} for {endpoint}")
        return resp.json()

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        if not query or not query.strip():
            return await self.get_latest(page)

        from app.domain.sanitizer import remove_accents
        from app.domain.ids import slugify

        q_clean = query.strip()
        encoded = quote_plus(q_clean)
        results: list[StorySummary] = []
        seen_slugs: set[str] = set()

        # 1. Direct API search
        try:
            data = await self._api_get(f"/stories/search?q={encoded}")
            items = data.get("data", []) if isinstance(data, dict) else []
            for item in items:
                slug = item.get("slug") or ""
                if slug and slug not in seen_slugs:
                    seen_slugs.add(slug)
                    results.append(
                        StorySummary(
                            source_id=self.id,
                            slug=slug,
                            title=item.get("title") or "Chưa có tiêu đề",
                            author=item.get("author", {}).get("name", "Đang cập nhật") if isinstance(item.get("author"), dict) else "Đang cập nhật",
                            cover_url=self._fix_cover_url(item.get("coverUrl")),
                        )
                    )
        except Exception as e:
            logger.debug(f"[Storya] Search API failed for '{query}': {e}")

        # 2. If unaccented or returned few results, try direct slug lookup (e.g. muc-than-ky)
        candidate_slug = slugify(q_clean)
        if candidate_slug and candidate_slug not in seen_slugs:
            try:
                data = await self._api_get(f"/stories/{candidate_slug}")
                item = data.get("data") if isinstance(data, dict) else None
                if item and isinstance(item, dict):
                    slug = item.get("slug") or candidate_slug
                    if slug not in seen_slugs:
                        seen_slugs.add(slug)
                        results.insert(
                            0,
                            StorySummary(
                                source_id=self.id,
                                slug=slug,
                                title=item.get("title") or candidate_slug,
                                author=item.get("author", {}).get("name", "Đang cập nhật") if isinstance(item.get("author"), dict) else "Đang cập nhật",
                                cover_url=self._fix_cover_url(item.get("coverUrl")),
                            ),
                        )
            except Exception:
                pass

        return results

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        data = await self._api_get(f"/stories/hot?page={page}&limit=20")
        items = data.get("data", [])
        results: list[StorySummary] = []
        for item in items:
            results.append(
                StorySummary(
                    source_id=self.id,
                    slug=item.get("slug") or "",
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=item.get("author", {}).get("name", "Đang cập nhật") if isinstance(item.get("author"), dict) else "Đang cập nhật",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                )
            )
        return results

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        data = await self._api_get(f"/stories?page={page}&limit=20")
        items = data.get("data", [])
        results: list[StorySummary] = []
        for item in items:
            results.append(
                StorySummary(
                    source_id=self.id,
                    slug=item.get("slug") or "",
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=item.get("author", {}).get("name", "Đang cập nhật") if isinstance(item.get("author"), dict) else "Đang cập nhật",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                )
            )
        return results

    async def get_completed(self, page: int = 1) -> list[StorySummary]:
        data = await self._api_get(f"/stories?status=COMPLETED&page={page}&limit=20")
        items = data.get("data", [])
        results: list[StorySummary] = []
        for item in items:
            results.append(
                StorySummary(
                    source_id=self.id,
                    slug=item.get("slug") or "",
                    title=item.get("title") or "Chưa có tiêu đề",
                    author=item.get("author", {}).get("name", "Đang cập nhật") if isinstance(item.get("author"), dict) else "Đang cập nhật",
                    cover_url=self._fix_cover_url(item.get("coverUrl")),
                )
            )
        return results

    async def get_genres(self) -> list[GenreItem]:
        data = await self._api_get("/genres")
        items = data.get("data", [])
        genres: list[GenreItem] = []
        for item in items:
            name = item.get("name")
            slug = item.get("slug")
            if name and slug:
                genres.append(
                    GenreItem(
                        id=str(item.get("id", slug)),
                        name=name,
                        slug=slug,
                        url=f"{self.base_url}/the-loai/{slug}",
                    )
                )
        return genres

    async def get_story_detail(self, story_slug: str) -> Story:
        data = await self._api_get(f"/stories/{story_slug}")
        d = data.get("data", {})
        author = "Đang cập nhật"
        if isinstance(d.get("author"), dict):
            author = d.get("author", {}).get("name", "Đang cập nhật")
        elif isinstance(d.get("author"), str):
            author = d.get("author")

        genres: list[str] = []
        for g in d.get("genres", []):
            if isinstance(g, dict) and "name" in g:
                genres.append(g["name"])
            elif isinstance(g, str):
                genres.append(g)

        status = "Hoàn thành" if d.get("status") == "COMPLETED" else "Đang cập nhật"
        desc = d.get("description") or d.get("rewrittenDescription") or ""

        return Story(
            id=build_story_id(self.id, story_slug),
            source_id=self.id,
            slug=story_slug,
            title=d.get("title") or story_slug,
            author=author,
            description=desc,
            cover_url=self._fix_cover_url(d.get("coverUrl")),
            status=status,
            genres=genres,
            total_chapters=d.get("totalChapters", 0),
        )

    async def list_chapters(
        self, story_slug: str, page: int = 1, page_size: int = 100
    ) -> tuple[list[ChapterSummary], int]:
        data = await self._api_get(
            f"/chapters/story/{story_slug}?page={page}&limit={page_size}&minimal=true"
        )
        items = data.get("data", [])
        meta = data.get("meta", {})
        total_pages = meta.get("totalPages", 1)

        chapters: list[ChapterSummary] = []
        for item in items:
            order = item.get("order", 1)
            chap_slug = item.get("slug") or f"chuong-{order}"
            chapters.append(
                ChapterSummary(
                    order=order,
                    title=item.get("title") or f"Chương {order}",
                    slug=chap_slug,
                    url=f"{self.base_url}/truyen/{story_slug}/{chap_slug}",
                    is_vip=bool(item.get("isVip", False)),
                )
            )
        return chapters, total_pages

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        first_page, total_pages = await self.list_chapters(story_slug, page=1, page_size=100)
        all_chapters = list(first_page)

        if total_pages > 1:
            sem = asyncio.Semaphore(10)

            async def fetch_page(p: int) -> list[ChapterSummary]:
                async with sem:
                    page_chaps, _ = await self.list_chapters(story_slug, page=p, page_size=100)
                    return page_chaps

            page_results = await asyncio.gather(*(fetch_page(p) for p in range(2, total_pages + 1)))
            for page_chaps in page_results:
                all_chapters.extend(page_chaps)

        all_chapters.sort(key=lambda c: c.order)
        return all_chapters

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        data = await self._api_get(f"/chapters/{story_slug}/{chap_slug}")
        item = data.get("data", {})
        raw_content = (
            item.get("rewrittenContent")
            or item.get("content")
            or item.get("rawContent")
            or ""
        )
        clean_xhtml = sanitize_chapter_html(raw_content)

        return ChapterContent(
            source_id=self.id,
            story_slug=story_slug,
            chap_slug=chap_slug,
            title=item.get("title") or f"Chương {item.get('order', '')}",
            order=item.get("order", 1),
            content_html=clean_xhtml,
            original_url=f"{self.base_url}/truyen/{story_slug}/{chap_slug}",
        )

    async def login(self, username: str, password: str) -> bool:
        return True
