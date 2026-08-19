"""Integration tests for X3 enhancements: Top Sources, Chapter Streaming, Folder Storage, and Cover Proxy."""

import time
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.cache.object_storage import storage
from app.api.opds_builder import format_chapter_title, OpdsBuilder
from app.domain.models import Story, ChapterSummary


@pytest.mark.asyncio
async def test_opds_root_sources_at_top():
    """Verify OPDS root feed matches user layout with Continue Reading, Select Source, and Categories."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds")
        assert resp.status_code == 200
        text = resp.text

        assert "Chọn Nguồn Truyện" in text
        assert "Nguồn Hiện Tại" in text
        assert "Truyện Mới Cập Nhật" in text
        assert "Truyện Hot" in text
        assert "Truyện Hoàn Thành" in text
        assert "Thể Loại Truyện" in text

        # With last read
        from app.cache.metadata_repo import repo
        repo.set_last_read("storyaclick", "muc-than-ky", "Mục Thần Ký", 5)

        resp2 = await client.get("/opds")
        assert resp2.status_code == 200
        assert "Đọc Tiếp: Mục Thần Ký" in resp2.text
        assert "/opds/book/storyaclick/muc-than-ky/chapters?sort=asc" in resp2.text


@pytest.mark.asyncio
async def test_opds_dedicated_source_feed():
    """Verify dedicated feed for a specific source has clean titles."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/source/storyaclick")
        assert resp.status_code == 200
        assert "Storya" in resp.text
        assert "/opds/hot?source=storyaclick" in resp.text
        # Ensure clean titles without redundant source suffix in entries
        assert "⚡ Truyện Mới Cập Nhật" in resp.text
        assert "🔥 Truyện Hot &amp; Đọc Nhiều" in resp.text


@pytest.mark.asyncio
async def test_opds_book_multiple_acquisition_methods():
    """Verify story detail feed provides multiple acquisition methods: single-chapter, volumes, all."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/book/conduongbachu/main")
        assert resp.status_code == 200
        text = resp.text

        # Check options
        assert "Đọc Từng Chương" in text
        assert "Chương 1" in text
        assert "Trọn Bộ" in text
        assert "Tập 01" in text


@pytest.mark.asyncio
async def test_cover_proxy_endpoint():
    """Verify cover proxy endpoint returns valid JPEG image for E-ink."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/cover/conduongbachu/main")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert len(resp.content) > 100
        assert resp.content[:2] == b"\xff\xd8"


def test_story_subfolder_organization():
    """Verify ObjectStorage organizes EPUBs in story subfolders."""
    test_data = b"PK\x03\x04testepubcontent"
    filename = "ztruyen_storyaclick_muc-than-ky_v01.epub"
    saved_path = storage.save_epub(filename, test_data, story_slug="muc-than-ky")

    assert saved_path.is_file()
    assert "muc-than-ky" in str(saved_path.parent)
    assert storage.has_epub(filename, story_slug="muc-than-ky")


def test_chapter_title_format_clean_syntax():
    """Verify chapter titles are formatted as 'Chương {order}_{tên chương}' cleanly."""
    # Case 1: Standard with colon
    assert format_chapter_title(1, "Chương 1: Tiết tử", "Mục Thần Ký") == "Chương 1_Tiết tử"
    # Case 2: With hyphen
    assert format_chapter_title(2, "Chương 2 - Khởi đầu mới", "Mục Thần Ký") == "Chương 2_Khởi đầu mới"
    # Case 3: Only chapter title without number
    assert format_chapter_title(3, "Đại chiến Thần Ma", "Mục Thần Ký") == "Chương 3_Đại chiến Thần Ma"
    # Case 4: Redundant story title prefix
    assert format_chapter_title(4, "Mục Thần Ký — Chương 4: Bí ẩn", "Mục Thần Ký") == "Chương 4_Bí ẩn"
    # Case 5: Bare chapter
    assert format_chapter_title(5, "Chương 5", "Mục Thần Ký") == "Chương 5"


@pytest.mark.asyncio
async def test_opds_chapter_range_groups_and_pagination():
    """Verify long stories (>50 chapters) show 50-chapter range blocks and paginate properly."""
    from tests.integration.test_opds import MockStoryaAdapter
    from app.sources.registry import registry
    registry.register(MockStoryaAdapter())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # 1. Accessing story chapter root shows Range Groups (e.g. pham-nhan-tu-tien has 60 chapters)
        resp_root = await client.get("/opds/book/storyaclick/pham-nhan-tu-tien/chapters?sort=asc")
        assert resp_root.status_code == 200
        text = resp_root.text
        assert "Chọn Khối Chương" in text
        assert "Chương 1 - 50" in text
        assert "Chương 51 - 60" in text

        # 2. Accessing range 1-50 shows individual chapters with clean syntax
        resp_range1 = await client.get("/opds/book/storyaclick/pham-nhan-tu-tien/chapters?start=1&limit=50&sort=asc")
        assert resp_range1.status_code == 200
        assert "rel=\"next\"" in resp_range1.text  # Has link to next 50 chapters
        assert "Chương 1" in resp_range1.text
        assert "Chương 50" in resp_range1.text

        # 3. Accessing range 51-60 has link back to previous
        resp_range2 = await client.get("/opds/book/storyaclick/pham-nhan-tu-tien/chapters?start=51&limit=50&sort=asc")
        assert resp_range2.status_code == 200
        assert "rel=\"previous\"" in resp_range2.text
        assert "Chương 51" in resp_range2.text
        assert "Chương 60" in resp_range2.text


@pytest.mark.asyncio
async def test_fast_cache_speed_on_back_navigation():
    """Verify instant response time (<10ms) for cached OPDS navigation."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        # First call primes cache
        await client.get("/opds/hot?source=storyaclick")

        # Second call should be instant from in-memory cache
        start_time = time.monotonic()
        resp = await client.get("/opds/hot?source=storyaclick")
        elapsed = time.monotonic() - start_time

        assert resp.status_code == 200
        # In-memory cache should respond in < 0.05 seconds
        assert elapsed < 0.05
