"""Integration tests for X3 enhancements: Top Sources, Chapter Streaming, Folder Storage, and Cover Proxy."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.cache.object_storage import storage


@pytest.mark.asyncio
async def test_opds_root_sources_at_top():
    """Verify OPDS root feed places Source selection on top and has no technical jargon."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds")
        assert resp.status_code == 200
        text = resp.text

        # Verify sources section is at top before categories
        idx_sources = text.find("Chọn Nguồn Truyện")
        idx_hot = text.find("Truyện Hot")
        assert idx_sources != -1
        assert idx_hot != -1
        assert idx_sources < idx_hot

        # Verify no technical jargon like 'nguồn cào'
        assert "nguồn cào" not in text.lower()
        assert "Kho Truyện: Storya" in text
        assert "Kho Truyện: Con Đường Bá Chủ" in text


@pytest.mark.asyncio
async def test_opds_dedicated_source_feed():
    """Verify dedicated feed for a specific source."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/source/storyaclick")
        assert resp.status_code == 200
        assert "Storya" in resp.text
        assert "/opds/hot?source=storyaclick" in resp.text


@pytest.mark.asyncio
async def test_opds_book_multiple_acquisition_methods():
    """Verify story detail feed provides multiple acquisition methods: single-chapter, volumes, all."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/book/conduongbachu/main")
        assert resp.status_code == 200
        text = resp.text

        # Check options
        assert "Đọc Từng Chương" in text
        assert "Đọc Ngay Chương 1" in text
        assert "Tải Trọn Bộ" in text
        assert "Tập 01" in text
        assert "/opds/cover/conduongbachu/main" in text


@pytest.mark.asyncio
async def test_cover_proxy_endpoint():
    """Verify cover proxy endpoint returns valid JPEG image for E-ink."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as client:
        resp = await client.get("/opds/cover/conduongbachu/main")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/jpeg"
        assert len(resp.content) > 100
        # Check JPEG magic bytes: 0xFF 0xD8
        assert resp.content[:2] == b"\xff\xd8"


def test_story_subfolder_organization():
    """Verify ObjectStorage organizes EPUBs in story subfolders."""
    test_data = b"PK\x03\x04testepubcontent"
    filename = "ztruyen_storyaclick_muc-than-ky_v01.epub"
    saved_path = storage.save_epub(filename, test_data, story_slug="muc-than-ky")

    assert saved_path.is_file()
    assert "muc-than-ky" in str(saved_path.parent)
    assert storage.has_epub(filename, story_slug="muc-than-ky")
