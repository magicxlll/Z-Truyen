"""Integration tests for X3 enhancements: Top Sources, Chapter Streaming, Folder Storage, and Cover Proxy."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.cache.object_storage import storage


@pytest.mark.asyncio
async def test_opds_root_sources_at_top():
    """Verify OPDS root feed matches user layout with Continue Reading, Select Source, and Categories."""
    # 1. Without last read
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

        # 2. With last read
        from app.cache.metadata_repo import repo
        repo.set_last_read("storyaclick", "muc-than-ky", "Mục Thần Ký", 5)
        
        resp2 = await client.get("/opds")
        assert resp2.status_code == 200
        assert "Đọc Tiếp: Mục Thần Ký" in resp2.text
        assert "/opds/book/storyaclick/muc-than-ky/chapters?sort=asc" in resp2.text


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
