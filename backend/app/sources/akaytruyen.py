"""Source Adapter for AkayTruyen.com (Laravel HTML + VIP Auth)."""

import re
import html
from typing import Any
from urllib.parse import quote_plus
from selectolax.parser import HTMLParser
from app.fetcher.client import http_client, HttpClient
from app.fetcher.session import session_manager, SessionManager
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent, GenreItem
from app.domain.ids import build_story_id
from app.domain.sanitizer import sanitize_chapter_html
from app.logging import log_scraper_event, logger


class AkayTruyenAdapter:
    """Scraper adapter for AkayTruyen.com."""

    id: str = "akaytruyen"
    name: str = "AkayTruyen"
    base_url: str = "https://akaytruyen.com"
    supports_login: bool = True

    def __init__(
        self,
        client: HttpClient | None = None,
        sess_mgr: SessionManager | None = None,
    ) -> None:
        self.client = client or http_client
        self.session_manager = sess_mgr or session_manager

    def _get_headers(self) -> dict[str, str]:
        return {
            "Referer": f"{self.base_url}/",
            "Accept": "text/html,application/xhtml+xml,application/json,*/*",
        }

    def _parse_story_anchors(self, html_text: str) -> list[StorySummary]:
        tree = HTMLParser(html_text)
        stories_map: dict[str, StorySummary] = {}

        for a in tree.css("a"):
            href = a.attributes.get("href", "")
            if not href or "/truyen/" not in href:
                continue

            clean_href = href.split("?")[0].split("#")[0].rstrip("/")
            slug = clean_href.split("/")[-1]
            if not slug:
                continue

            img = a.css_first("img")
            cover_url = None
            if img:
                cover_url = img.attributes.get("data-src") or img.attributes.get("src")
                if cover_url and cover_url.startswith("/"):
                    cover_url = f"{self.base_url}{cover_url}"

            title = a.text(strip=True)
            if img and not title:
                title = img.attributes.get("alt", "")

            title = re.sub(r"\s+(Full|Hot|New|Đang viết)\s*$", "", title, flags=re.IGNORECASE).strip()

            if slug in stories_map:
                if cover_url and not stories_map[slug].cover_url:
                    stories_map[slug].cover_url = cover_url
                if title and len(title) > len(stories_map[slug].title):
                    stories_map[slug].title = title
            else:
                if title and not title.startswith("Thể loại"):
                    stories_map[slug] = StorySummary(
                        source_id=self.id,
                        slug=slug,
                        title=title,
                        cover_url=cover_url,
                    )

        return list(stories_map.values())

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        if not query or not query.strip():
            return await self.get_latest(page)

        encoded = quote_plus(query.strip())
        url = f"{self.base_url}/tim-kiem?keyword={encoded}"
        log_scraper_event(self.id, f"Search query: '{query}'")
        cookies = self.session_manager.get_cookies(self.id)
        resp = await self.client.get(url, headers=self._get_headers(), cookies=cookies)
        return self._parse_story_anchors(resp.text)

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        cookies = self.session_manager.get_cookies(self.id)
        resp = await self.client.get(f"{self.base_url}/", headers=self._get_headers(), cookies=cookies)
        tree = HTMLParser(resp.text)
        hot_section = tree.css_first(".section-stories-hot")
        if hot_section:
            return self._parse_story_anchors(hot_section.html or "")
        return self._parse_story_anchors(resp.text)[:20]

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        cookies = self.session_manager.get_cookies(self.id)
        resp = await self.client.get(f"{self.base_url}/", headers=self._get_headers(), cookies=cookies)
        tree = HTMLParser(resp.text)
        new_section = tree.css_first(".section-stories-new")
        if new_section:
            return self._parse_story_anchors(new_section.html or "")
        return self._parse_story_anchors(resp.text)[:20]

    async def get_completed(self, page: int = 1) -> list[StorySummary]:
        cookies = self.session_manager.get_cookies(self.id)
        url = f"{self.base_url}/danh-sach/truyen-full?page={page}"
        resp = await self.client.get(url, headers=self._get_headers(), cookies=cookies)
        results = self._parse_story_anchors(resp.text)
        if not results:
            return await self.get_latest(page)
        return results[:20]

    async def get_genres(self) -> list[GenreItem]:
        cookies = self.session_manager.get_cookies(self.id)
        resp = await self.client.get(f"{self.base_url}/", headers=self._get_headers(), cookies=cookies)
        tree = HTMLParser(resp.text)
        genres: list[GenreItem] = []
        for a in tree.css("a[href*='/the-loai/']"):
            href = a.attributes.get("href", "")
            name = a.text(strip=True)
            slug = href.split("?")[0].split("#")[0].rstrip("/").split("/")[-1]
            if name and slug and not any(g.slug == slug for g in genres):
                genres.append(
                    GenreItem(
                        id=slug,
                        name=name,
                        slug=slug,
                        url=f"{self.base_url}/the-loai/{slug}",
                    )
                )
        return genres

    async def get_story_detail(self, story_slug: str) -> Story:
        url = f"{self.base_url}/truyen/{story_slug}"
        cookies = self.session_manager.get_cookies(self.id)
        resp = await self.client.get(url, headers=self._get_headers(), cookies=cookies)
        tree = HTMLParser(resp.text)

        title_node = tree.css_first("h1, .story-title, .title-story")
        title = title_node.text(strip=True) if title_node else story_slug

        desc_node = tree.css_first(".desc, [itemprop='description'], .story-description")
        desc = desc_node.text(strip=True) if desc_node else ""

        author_node = tree.css_first("[itemprop='author'], .author a, .author")
        author = author_node.text(strip=True) if author_node else "Đang cập nhật"

        img_node = tree.css_first(".story-thumb img, .book-cover img, img.cover")
        cover_url = None
        if img_node:
            cover_url = img_node.attributes.get("data-src") or img_node.attributes.get("src")
            if cover_url and cover_url.startswith("/"):
                cover_url = f"{self.base_url}{cover_url}"

        genres = [a.text(strip=True) for a in tree.css("a[href*='/the-loai/']") if a.text(strip=True)]

        return Story(
            id=build_story_id(self.id, story_slug),
            source_id=self.id,
            slug=story_slug,
            title=title,
            author=author,
            description=desc,
            cover_url=cover_url,
            status="Đang cập nhật",
            genres=genres,
        )

    async def list_chapters(
        self, story_slug: str, page: int = 1, page_size: int = 100
    ) -> tuple[list[ChapterSummary], int]:
        cookies = self.session_manager.get_cookies(self.id)
        page_url = f"{self.base_url}/truyen/{story_slug}?page={page}"
        resp = await self.client.get(page_url, headers=self._get_headers(), cookies=cookies)

        html_content = resp.text if resp.status_code == 200 else ""
        tree = HTMLParser(html_content) if html_content else None
        chapters: list[ChapterSummary] = []
        seen_urls: set[str] = set()

        def parse_anchors(doc_tree: HTMLParser) -> list[ChapterSummary]:
            chaps = []
            for a in doc_tree.css("a"):
                href = a.attributes.get("href", "")
                if not href:
                    continue
                clean_url = href.split("?")[0].split("#")[0].rstrip("/")
                if f"/{story_slug}/" not in clean_url or clean_url in seen_urls:
                    continue

                seen_urls.add(clean_url)
                chap_slug = clean_url.split("/")[-1]
                num_node = a.css_first(".chapter-number")
                title_node = a.css_first(".chapter-title")

                if num_node and title_node:
                    chap_title = f"{num_node.text(strip=True)}: {title_node.text(strip=True)}"
                else:
                    chap_title = a.text(strip=True) or a.attributes.get("title") or "Chương"

                order_match = re.search(r"(\d+)", chap_title) or re.search(r"(\d+)", chap_slug)
                order = int(order_match.group(1)) if order_match else (len(chapters) + len(chaps) + 1)

                chaps.append(
                    ChapterSummary(
                        order=order,
                        title=chap_title,
                        slug=chap_slug,
                        url=clean_url if clean_url.startswith("http") else f"{self.base_url}{clean_url}",
                    )
                )
            return chaps

        if tree:
            chapters = parse_anchors(tree)

        if not chapters:
            # Fallback to search-chapters endpoint
            endpoint_url = f"{self.base_url}/truyen/{story_slug}/search-chapters?search=&page={page}"
            resp = await self.client.get(endpoint_url, headers=self._get_headers(), cookies=cookies)
            if resp.status_code == 200:
                try:
                    data = resp.json()
                    fb_html = data.get("html", "") if isinstance(data, dict) else resp.text
                except Exception:
                    fb_html = resp.text
                if fb_html:
                    tree = HTMLParser(fb_html)
                    chapters = parse_anchors(tree)

        total_pages = 1
        if tree:
            # Estimate total pages from pagination jump-input or page query links
            for inp in tree.css("input.jump-input"):
                max_p = inp.attributes.get("max")
                if max_p and max_p.isdigit():
                    total_pages = max(total_pages, int(max_p))

            for page_a in tree.css(".pagination a, ul.pagination li a, .page-numbers a"):
                p_text = page_a.text(strip=True)
                if p_text.isdigit():
                    total_pages = max(total_pages, int(p_text))
                href = page_a.attributes.get("href", "")
                match = re.search(r"[?&]page=(\d+)", href)
                if match:
                    total_pages = max(total_pages, int(match.group(1)))

        return chapters, total_pages

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        first_page, total_pages = await self.list_chapters(story_slug, page=1)
        all_chapters = list(first_page)

        for p in range(2, total_pages + 1):
            page_chaps, _ = await self.list_chapters(story_slug, page=p)
            all_chapters.extend(page_chaps)

        # Sort chapters by natural order
        all_chapters.sort(key=lambda c: c.order)
        return all_chapters

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        cookies = self.session_manager.get_cookies(self.id)
        
        # 1. Try standard akaytruyen chapter URL: /{story_slug}/{chap_slug}
        url = f"{self.base_url}/{story_slug}/{chap_slug}"
        resp = await self.client.get(url, headers=self._get_headers(), cookies=cookies)
        
        # 2. Fallback to /truyen/{story_slug}/{chap_slug} if 404
        if resp.status_code == 404 or "404 Not Found" in resp.text:
            alt_url = f"{self.base_url}/truyen/{story_slug}/{chap_slug}"
            resp = await self.client.get(alt_url, headers=self._get_headers(), cookies=cookies)
            if resp.status_code == 200 and "404 Not Found" not in resp.text:
                url = alt_url

        if resp.status_code != 200 or "404 Not Found" in resp.text:
            raise ValueError(f"Không tìm thấy chương '{chap_slug}' trên AkayTruyen (HTTP {resp.status_code})")

        tree = HTMLParser(resp.text)
        if tree.css_first(".access-denied-container") or "Chương này dành cho tài khoản VIP" in resp.text:
            raise PermissionError("Chương VIP bị khóa. Hãy đăng nhập tài khoản AkayTruyen.")
        title_node = tree.css_first("h1.custom-text, h1, h2, .chapter-title, .title-chap")
        title = title_node.text(strip=True) if title_node else chap_slug

        content_node = (
            tree.css_first("#chapter-content")
            or tree.css_first(".chapter-content")
            or tree.css_first("#chapter-c")
            or tree.css_first(".content-chap")
            or tree.css_first(".reading-content")
        )

        if not content_node:
            raise ValueError(f"Không tìm thấy khối văn bản chương '{chap_slug}' từ {url}")

        raw_html = content_node.html or ""
        clean_xhtml = sanitize_chapter_html(raw_html)

        order_match = re.search(r"(\d+)", title) or re.search(r"(\d+)", chap_slug)
        order = int(order_match.group(1)) if order_match else 1

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
        if not username or not password:
            return False

        login_url = f"{self.base_url}/login"
        resp = await self.client.get(login_url, headers=self._get_headers())
        token_match = re.search(r'name="_token"\s+value="([^"]+)"', resp.text)
        if not token_match:
            return False

        csrf_token = token_match.group(1)
        post_data = {
            "_token": csrf_token,
            "email": username,
            "password": password,
            "remember": "1",
        }

        login_resp = await self.client.post(
            login_url,
            data=post_data,
            headers={**self._get_headers(), "Content-Type": "application/x-www-form-urlencoded"},
        )

        new_cookies = dict(login_resp.cookies)
        if new_cookies:
            self.session_manager.update_cookies(self.id, new_cookies)
            self.session_manager.set_credential(self.id, username, password)
            return True

        return False
