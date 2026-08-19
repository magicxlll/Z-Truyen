"""End-to-end validation matching the 5 Quickstart scenarios from quickstart.md."""

import io
import pytest
from httpx import AsyncClient, ASGITransport
from ebooklib import epub
from app.main import app
from app.sources.registry import registry
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent


class QuickstartMockAdapter:
    id = "conduongbachu"
    name = "Con Đường Bá Chủ"
    base_url = "https://conduongbachu.com"
    supports_login = False
    client = None

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        return [
            StorySummary(
                source_id=self.id,
                slug="main",
                title="Con Đường Bá Chủ (Chính Truyện)",
                author="Akay Hậu",
                cover_url="https://conduongbachu.com/cover.jpg",
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
            title="Con Đường Bá Chủ (Chính Truyện)",
            author="Akay Hậu",
            description="Tác phẩm tiên hiệp, kiếm hiệp, huyền huyễn đình đám.",
            total_chapters=50,
        )

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        return [
            ChapterSummary(
                order=i,
                title=f"Chương {i}: Bá Khí Đằng Đằng {i}",
                slug=f"chuong-{i}",
                url=f"https://conduongbachu.com/chuong-{i}/",
            )
            for i in range(1, 51)
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
            title=f"Chương {num}: Bá Khí Đằng Đằng",
            order=int(num),
            content_html=f'<p id="p-1">Lạc Nam vung tay dời non lấp biển tại chương {num}.</p>',
            original_url=f"https://conduongbachu.com/chuong-{num}/",
        )

    async def login(self, username: str, password: str) -> bool:
        return True


@pytest.fixture(autouse=True)
def setup_scenario_adapter():
    registry.register(QuickstartMockAdapter())


@pytest.mark.asyncio
async def test_scenario_1_healthcheck() -> None:
    """Kịch Bản 1: Kiểm Tra Healthcheck & API Cơ Bản"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/healthz")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_scenario_2_opds_root_feed() -> None:
    """Kịch Bản 2: Kiểm Tra OPDS Root Feed"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/opds", headers={"Accept": "application/atom+xml"})
        assert res.status_code == 200
        assert "application/atom+xml" in res.headers["content-type"]
        assert "🔥 Truyện Hot &amp; Đọc Nhiều" in res.text
        assert "⚡ Truyện Mới Cập Nhật" in res.text
        assert "search?q={searchTerms}" in res.text


@pytest.mark.asyncio
async def test_scenario_3_search_stories() -> None:
    """Kịch Bản 3: Kiểm Tra Cào Truyện & Tìm Kiếm Đa Nguồn"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/opds/search?q=con+duong+ba+chu")
        assert res.status_code == 200
        assert "Con Đường Bá Chủ" in res.text

        res_filtered = await client.get("/opds/search?q=con+duong&source=conduongbachu")
        assert res_filtered.status_code == 200
        assert "Con Đường Bá Chủ" in res_filtered.text


@pytest.mark.asyncio
async def test_scenario_4_and_epub_validation() -> None:
    """Kịch Bản 4 & Validation EPUB: Kiểm Tra Tạo File EPUB Volume Gom Chương & Tính hợp lệ EPUB"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        download_url = "/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_v01.epub"
        res = await client.get(download_url)
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/epub+zip"
        assert "X-KOSync-SHA1" in res.headers

        epub_bytes = res.content
        assert len(epub_bytes) > 0
        assert len(epub_bytes) < 1024 * 1024  # Less than 1MB

        # Validate EPUB structure against standards
        book = epub.read_epub(io.BytesIO(epub_bytes))
        assert book.get_metadata("DC", "language")[0][0] == "vi"
        assert "Con Đường Bá Chủ" in book.get_metadata("DC", "title")[0][0]
        assert "Akay Hậu" in book.get_metadata("DC", "creator")[0][0]

        # Verify all 50 chapters are present in spine & items
        items = list(book.get_items())
        chap_items = [i for i in items if i.file_name.startswith("chapter_")]
        assert len(chap_items) == 50

        # Verify paragraph IDs in first chapter
        first_chap_content = chap_items[0].get_content().decode("utf-8")
        assert '<p id="p-1">' in first_chap_content
        assert "Lạc Nam" in first_chap_content


@pytest.mark.asyncio
async def test_scenario_5_x3_crossvi_opds_flow() -> None:
    """Kịch Bản 5: Mô Phỏng Chu Trình Đọc Của Xteink X3 (CrossVi 1.1.2)"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. X3 opens OPDS root
        r_root = await client.get("/opds")
        assert r_root.status_code == 200

        # 2. X3 browses story detail & volumes
        r_detail = await client.get("/opds/book/conduongbachu/main")
        assert r_detail.status_code == 200
        assert "ztruyen_conduongbachu_main_v01.epub" in r_detail.text

        # 3. X3 triggers download for Volume 1
        r_dl = await client.get("/opds/download/conduongbachu/main/ztruyen_conduongbachu_main_v01.epub")
        assert r_dl.status_code == 200
        assert len(r_dl.content) > 1000
