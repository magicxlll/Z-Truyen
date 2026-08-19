"""Integration tests for OPDS 1.2 catalog feeds and EPUB download gateway."""

import io
import pytest
import httpx
from ebooklib import epub
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.sources.registry import registry
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent


class MockStoryaAdapter:
    id = "storyaclick"
    name = "Storya"
    base_url = "https://storya.click"
    supports_login = False
    client = None

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        return [
            StorySummary(
                source_id=self.id,
                slug="pham-nhan-tu-tien",
                title="Phàm Nhân Tu Tiên",
                author="Vong Ngữ",
                cover_url="https://storya.click/covers/pntt.jpg",
            )
        ]

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        return await self.search("", page)

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        return await self.search("", page)

    async def get_genres(self) -> list:
        return []

    async def get_story_detail(self, story_slug: str) -> Story:
        return Story(
            id=f"{self.id}:{story_slug}",
            source_id=self.id,
            slug=story_slug,
            title="Phàm Nhân Tu Tiên",
            author="Vong Ngữ",
            description="Truyện tiên hiệp kể về thiếu niên bình phàm Hàn Lập.",
            cover_url="https://storya.click/covers/pntt.jpg",
            total_chapters=60,
        )

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        return [
            ChapterSummary(
                order=i,
                title=f"Chương {i}: Hàn Lập tu tiên {i}",
                slug=f"chuong-{i}",
                url=f"https://storya.click/truyen/{story_slug}/chuong-{i}",
            )
            for i in range(1, 61)
        ]

    async def list_chapters(self, story_slug: str, page: int = 1, page_size: int = 100) -> tuple[list[ChapterSummary], int]:
        all_chaps = await self.get_all_chapters(story_slug)
        return all_chaps, 1

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        num = chap_slug.replace("chuong-", "")
        return ChapterContent(
            source_id=self.id,
            story_slug=story_slug,
            chap_slug=chap_slug,
            title=f"Chương {num}",
            order=int(num),
            content_html=f'<p id="p-1">Nội dung chương {num} với dấu tiếng Việt chuẩn xác.</p>',
            original_url=f"https://storya.click/truyen/{story_slug}/{chap_slug}",
        )

    async def login(self, username: str, password: str) -> bool:
        return True


@pytest.fixture(autouse=True)
def setup_mock_source():
    mock_adapter = MockStoryaAdapter()
    registry.register(mock_adapter)


@pytest.mark.asyncio
async def test_opds_root_feed() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/opds")
        assert response.status_code == 200
        assert "application/atom+xml" in response.headers["content-type"]
        body = response.text
        assert "urn:ztruyen:catalog:root" in body
        assert "search?q={searchTerms}" in body
        assert "/opds/hot" in body
        assert "/opds/latest" in body
        assert "/opds/sources" in body


@pytest.mark.asyncio
async def test_opds_hot_and_latest() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp_hot = await client.get("/opds/hot")
        assert resp_hot.status_code == 200
        assert "urn:ztruyen:category:hot" in resp_hot.text
        assert "Phàm Nhân Tu Tiên" in resp_hot.text

        resp_latest = await client.get("/opds/latest")
        assert resp_latest.status_code == 200
        assert "urn:ztruyen:category:latest" in resp_latest.text


@pytest.mark.asyncio
async def test_opds_search() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/opds/search?q=pham+nhan")
        assert response.status_code == 200
        assert "Phàm Nhân Tu Tiên" in response.text
        assert "/opds/book/storyaclick/pham-nhan-tu-tien" in response.text


@pytest.mark.asyncio
async def test_opds_book_details_and_volumes() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/opds/book/storyaclick/pham-nhan-tu-tien")
        assert response.status_code == 200
        body = response.text
        assert "urn:ztruyen:book:storyaclick:pham-nhan-tu-tien" in body
        assert "Tập 01" in body
        assert "Tập 02" in body
        assert "ztruyen_storyaclick_pham-nhan-tu-tien_v01.epub" in body
        assert "ztruyen_storyaclick_pham-nhan-tu-tien_v02.epub" in body


@pytest.mark.asyncio
async def test_opds_download_epub_gateway() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Download Volume 1 (Ch 1 - 50)
        url = "/opds/download/storyaclick/pham-nhan-tu-tien/ztruyen_storyaclick_pham-nhan-tu-tien_v01.epub"
        response = await client.get(url)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/epub+zip"
        assert "X-KOSync-SHA1" in response.headers

        # Verify EPUB integrity
        epub_data = response.content
        assert len(epub_data) > 0
        book = epub.read_epub(io.BytesIO(epub_data))
        assert "Phàm Nhân Tu Tiên" in book.get_metadata("DC", "title")[0][0]
        assert "Vong Ngữ" in book.get_metadata("DC", "creator")[0][0]

        # Verify cached second call
        cached_response = await client.get(url)
        assert cached_response.status_code == 200
        assert cached_response.headers["X-KOSync-SHA1"] == response.headers["X-KOSync-SHA1"]
