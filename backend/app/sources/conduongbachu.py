"""Source Adapter for Con Đường Bá Chủ (WordPress REST API)."""

import re
import html
from typing import Any
from selectolax.parser import HTMLParser
from app.fetcher.client import http_client, HttpClient
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent, GenreItem
from app.domain.ids import build_story_id
from app.domain.sanitizer import sanitize_chapter_html
from app.logging import log_scraper_event, logger

PREDEFINED_STORIES = [
    {
        "slug": "main",
        "cat_id": 3,
        "title": "Con Đường Bá Chủ (Chính Truyện)",
        "url": "https://conduongbachu.com/",
        "cover_url": "https://conduongbachu.com/wp-content/uploads/2024/12/20355-con-duong-ba-chu_cover_large.webp",
        "description": "Tác phẩm tiên hiệp, kiếm hiệp, huyền huyễn đình đám Con Đường Bá Chủ của tác giả Akay Hậu.",
    },
    {
        "slug": "bat-hu-than-chien",
        "cat_id": 12,
        "title": "Ngoại Truyện: Bất Hủ Thần Chiến",
        "url": "https://conduongbachu.com/ngoai-truyen/",
        "cover_url": "https://conduongbachu.com/wp-content/uploads/2025/04/conduongbachu-ngoai-truyen-268x400.jpg",
        "description": "Phần ngoại truyện Bất Hủ Thần Chiến mở rộng thế giới Con Đường Bá Chủ.",
    },
    {
        "slug": "van-dao-than-chu",
        "cat_id": 14,
        "title": "Ngoại Truyện: Vạn Đạo Thần Chủ",
        "url": "https://conduongbachu.com/ngoai-truyen-van-dao-than-chu/",
        "cover_url": "https://conduongbachu.com/wp-content/uploads/2025/04/conduongbachu-ngoai-truyen-268x400.jpg",
        "description": "Phần ngoại truyện Vạn Đạo Thần Chủ thuộc vũ trụ Con Đường Bá Chủ.",
    },
    {
        "slug": "chua-te-chi-lo",
        "cat_id": 15,
        "title": "Ngoại Truyện: Chúa Tể Chi Lộ",
        "url": "https://conduongbachu.com/ngoai-truyen-chua-te-chi-lo/",
        "cover_url": "https://conduongbachu.com/wp-content/uploads/2025/04/conduongbachu-ngoai-truyen-268x400.jpg",
        "description": "Phần ngoại truyện Chúa Tể Chi Lộ thuộc vũ trụ Con Đường Bá Chủ.",
    },
]


class ConDuongBaChuAdapter:
    """Scraper adapter for ConDuongBaChu.com using WordPress REST API."""

    id: str = "conduongbachu"
    name: str = "Con Đường Bá Chủ"
    base_url: str = "https://conduongbachu.com"
    supports_login: bool = False

    def __init__(self, client: HttpClient | None = None) -> None:
        self.client = client or http_client
        self._cached_chapters: dict[str, list[ChapterSummary]] = {}

    def _get_story_config(self, story_slug: str) -> dict[str, Any]:
        for s in PREDEFINED_STORIES:
            if s["slug"] == story_slug:
                return s
        return PREDEFINED_STORIES[0]

    @staticmethod
    def _parse_chapter_number(title: str, url: str) -> int:
        match = (
            re.search(r"(?:chương|chuong)\s*(\d+)", title, re.IGNORECASE)
            or re.search(r"^(\d+)\s*[:\-.]", title)
            or re.search(r"/chuong-(\d+)", url)
            or re.search(r"/(\d+)-", url)
        )
        return int(match.group(1)) if match else 1

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        results: list[StorySummary] = []
        q_lower = query.lower().strip() if query else ""

        for s in PREDEFINED_STORIES:
            if (
                not q_lower
                or q_lower in s["title"].lower()
                or "ba chu" in q_lower
                or "con duong" in q_lower
                or "ngoai truyen" in q_lower
            ):
                results.append(
                    StorySummary(
                        source_id=self.id,
                        slug=s["slug"],
                        title=s["title"],
                        author="Akay Hậu",
                        cover_url=s["cover_url"],
                    )
                )
        return results

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        return await self.search("", page)

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        return await self.search("", page)

    async def get_genres(self) -> list[GenreItem]:
        return [
            GenreItem(
                id=s["slug"],
                name=s["title"],
                slug=s["slug"],
                url=s["url"],
            )
            for s in PREDEFINED_STORIES
        ]

    async def get_story_detail(self, story_slug: str) -> Story:
        config = self._get_story_config(story_slug)
        total_chaps = len(self._cached_chapters[story_slug]) if story_slug in self._cached_chapters else 0

        if total_chaps == 0:
            try:
                cat_resp = await self.client.get(f"{self.base_url}/wp-json/wp/v2/categories/{config['cat_id']}")
                if cat_resp.status_code == 200:
                    total_chaps = cat_resp.json().get("count", 0)
            except Exception as e:
                logger.warning(f"Could not fetch category count for {story_slug}: {e}")
                total_chaps = 3752 if story_slug == "main" else 30

        return Story(
            id=build_story_id(self.id, story_slug),
            source_id=self.id,
            slug=story_slug,
            title=config["title"],
            author="Akay Hậu",
            description=config["description"],
            cover_url=config["cover_url"],
            status="Hoàn thành / Đang cập nhật",
            genres=["Tiên Hiệp", "Huyền Huyễn", "Bá Chủ", "Ngoại Truyện"],
            total_chapters=total_chaps,
        )

    async def list_chapters(
        self, story_slug: str, page: int = 1, page_size: int = 100
    ) -> tuple[list[ChapterSummary], int]:
        all_chaps = await self.get_all_chapters(story_slug)
        total_pages = max(1, (len(all_chaps) + page_size - 1) // page_size)
        start = (page - 1) * page_size
        end = start + page_size
        return all_chaps[start:end], total_pages

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        if story_slug in self._cached_chapters:
            return self._cached_chapters[story_slug]

        config = self._get_story_config(story_slug)
        cat_id = config["cat_id"]

        all_chapters: list[ChapterSummary] = []
        page = 1
        max_pages = 50

        while page <= max_pages:
            url = (
                f"{self.base_url}/wp-json/wp/v2/posts"
                f"?categories={cat_id}&per_page=100&_fields=link,title,slug&page={page}&order=asc&orderby=date"
            )
            log_scraper_event(self.id, f"Fetching WP page {page} for category {cat_id}")
            resp = await self.client.get(url, headers={"Accept": "application/json"})

            if resp.status_code == 400 or resp.status_code == 404:
                break
            if resp.status_code != 200:
                raise RuntimeError(f"WordPress API error HTTP {resp.status_code} for category {cat_id}")

            posts = resp.json()
            if not posts or not isinstance(posts, list):
                break

            for post in posts:
                raw_title = post.get("title", {}).get("rendered", "")
                title = html.unescape(raw_title).strip()
                link = post.get("link", "")
                chap_slug = post.get("slug") or (link.rstrip("/").split("/")[-1] if link else "")
                order = self._parse_chapter_number(title, link)

                all_chapters.append(
                    ChapterSummary(
                        order=order,
                        title=title,
                        slug=chap_slug,
                        url=link,
                        is_vip=False,
                    )
                )

            total_wp_pages_header = resp.headers.get("x-wp-totalpages")
            if total_wp_pages_header and total_wp_pages_header.isdigit():
                if page >= int(total_wp_pages_header):
                    break
            elif len(posts) < 100:
                break

            page += 1

        # Cache in memory
        self._cached_chapters[story_slug] = all_chapters
        return all_chapters

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        url = f"{self.base_url}/{chap_slug}/"
        target_title = None
        if story_slug in self._cached_chapters:
            target_chap = next(
                (c for c in self._cached_chapters[story_slug] if c.slug == chap_slug or f"chuong-{c.order}" == chap_slug),
                None,
            )
            if target_chap:
                url = target_chap.url
                target_title = target_chap.title

        resp = await self.client.get(url)

        tree = HTMLParser(resp.text)
        title_node = tree.css_first("h1.entry-title, h1")
        title = title_node.text(strip=True) if title_node else (target_chap.title if target_chap else chap_slug)

        content_node = tree.css_first(".entry-content, #content, article")
        raw_html = content_node.html if content_node else resp.text
        clean_xhtml = sanitize_chapter_html(raw_html)

        order = self._parse_chapter_number(title, url)

        return ChapterContent(
            source_id=self.id,
            story_slug=story_slug,
            chap_slug=chap_slug,
            title=title,
            order=order,
            content_html=clean_xhtml,
            original_url=url,
        )

    async def login(self, username: str, password: str) -> bool:
        return True
