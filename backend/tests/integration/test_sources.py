"""Integration and mock tests for StoryaClick, AkayTruyen, and ConDuongBaChu adapters."""

import pytest
import httpx
from app.sources.storyaclick import StoryaClickAdapter
from app.sources.akaytruyen import AkayTruyenAdapter
from app.sources.conduongbachu import ConDuongBaChuAdapter
from app.sources.registry import create_default_registry
from app.fetcher.client import HttpClient


@pytest.mark.asyncio
async def test_storyaclick_mock_flow() -> None:
    # Mock Storya JSON responses
    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if "/stories/search" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {
                                "title": "Phàm Nhân Tu Tiên",
                                "slug": "pham-nhan-tu-tien",
                                "coverUrl": "/covers/pntt.jpg",
                                "author": {"name": "Vong Ngữ"},
                            }
                        ]
                    },
                )
            elif "/stories/pham-nhan-tu-tien" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "title": "Phàm Nhân Tu Tiên",
                            "slug": "pham-nhan-tu-tien",
                            "description": "Câu chuyện tu tiên của Hàn Lập.",
                            "author": {"name": "Vong Ngữ"},
                            "genres": [{"name": "Tiên Hiệp"}],
                            "status": "COMPLETED",
                            "totalChapters": 2400,
                            "coverUrl": "/covers/pntt.jpg",
                        }
                    },
                )
            elif "/chapters/story/pham-nhan-tu-tien" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "data": [
                            {"order": 1, "title": "Chương 1: Sơn thôn thiếu niên", "slug": "chuong-1"}
                        ],
                        "meta": {"totalPages": 1},
                    },
                )
            elif "/chapters/pham-nhan-tu-tien/chuong-1" in url_str:
                return httpx.Response(
                    200,
                    json={
                        "data": {
                            "order": 1,
                            "title": "Chương 1: Sơn thôn thiếu niên",
                            "content": "<p>Hàn Lập sinh ra tại một thôn làng nghèo khó.</p>",
                        }
                    },
                )
            return httpx.Response(404)

    mock_client = HttpClient()
    mock_client._client = httpx.AsyncClient(transport=MockTransport())
    adapter = StoryaClickAdapter(client=mock_client)

    # 1. Search
    results = await adapter.search("pham nhan")
    assert len(results) == 1
    assert results[0].slug == "pham-nhan-tu-tien"
    assert results[0].title == "Phàm Nhân Tu Tiên"
    assert results[0].cover_url == "https://storya.click/covers/pntt.jpg"

    # 2. Detail
    story = await adapter.get_story_detail("pham-nhan-tu-tien")
    assert story.title == "Phàm Nhân Tu Tiên"
    assert story.author == "Vong Ngữ"
    assert "Tiên Hiệp" in story.genres

    # 3. Chapters
    chapters, total_p = await adapter.list_chapters("pham-nhan-tu-tien")
    assert len(chapters) == 1
    assert chapters[0].slug == "chuong-1"

    # 4. Content
    content = await adapter.get_chapter_content("pham-nhan-tu-tien", "chuong-1")
    assert '<p id="p-1">Hàn Lập sinh ra tại một thôn làng nghèo khó.</p>' in content.content_html


@pytest.mark.asyncio
async def test_akaytruyen_mock_flow() -> None:
    sample_story_html = """
    <html>
        <body>
            <h1 class="story-title">Đấu Phá Thương Khung</h1>
            <div class="desc" itemprop="description">Tiêu Viêm thiên tài suy lạc.</div>
            <div class="author"><a href="#">Thiên Tằm Thổ Đậu</a></div>
            <div class="book-cover"><img src="/covers/dptk.jpg" alt="Đấu Phá Thương Khung"/></div>
            <a href="/the-loai/huyen-huyen">Huyền Huyễn</a>
        </body>
    </html>
    """

    sample_chapters_json = {
        "html": """
        <div>
            <a href="/truyen/dau-pha-thuong-khung/chuong-1">
                <div class="chapter-number">Chương 1</div>
                <div class="chapter-title">Thiên chi kiêu tử</div>
            </a>
        </div>
        """
    }

    sample_chap_html = """
    <html>
        <body>
            <h1 class="custom-text">Chương 1: Thiên chi kiêu tử</h1>
            <div id="chapter-content">
                <p>Năm đó Tiêu Viêm mười lăm tuổi.</p>
                <div class="chapter-nav">Next</div>
            </div>
        </body>
    </html>
    """

    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if "search-chapters" in url_str:
                return httpx.Response(200, json=sample_chapters_json)
            elif "/truyen/dau-pha-thuong-khung/chuong-1" in url_str:
                return httpx.Response(200, text=sample_chap_html)
            elif "/truyen/dau-pha-thuong-khung" in url_str:
                return httpx.Response(200, text=sample_story_html)
            elif "tim-kiem" in url_str or url_str.endswith("akaytruyen.com/"):
                return httpx.Response(
                    200,
                    text='<div class="section-stories-hot"><a href="/truyen/dau-pha-thuong-khung" class="story-title">Đấu Phá Thương Khung</a></div>',
                )
            return httpx.Response(404)

    mock_client = HttpClient()
    mock_client._client = httpx.AsyncClient(transport=MockTransport())
    adapter = AkayTruyenAdapter(client=mock_client)

    # 1. Search
    results = await adapter.search("Dau Pha")
    assert len(results) >= 1
    assert results[0].slug == "dau-pha-thuong-khung"

    # 2. Detail
    story = await adapter.get_story_detail("dau-pha-thuong-khung")
    assert story.title == "Đấu Phá Thương Khung"
    assert story.author == "Thiên Tằm Thổ Đậu"

    # 3. Chapters
    chapters, total_p = await adapter.list_chapters("dau-pha-thuong-khung")
    assert len(chapters) == 1
    assert chapters[0].slug == "chuong-1"

    # 4. Content
    content = await adapter.get_chapter_content("dau-pha-thuong-khung", "chuong-1")
    assert '<p id="p-1">Năm đó Tiêu Viêm mười lăm tuổi.</p>' in content.content_html


@pytest.mark.asyncio
async def test_conduongbachu_mock_flow() -> None:
    posts_json = [
        {
            "id": 101,
            "title": {"rendered": "Chương 1: Lạc Nam Thiếu Gia"},
            "link": "https://conduongbachu.com/chuong-1-lac-nam-thieu-gia/",
            "slug": "chuong-1-lac-nam-thieu-gia",
        }
    ]

    chap_html = """
    <html>
        <body>
            <h1 class="entry-title">Chương 1: Lạc Nam Thiếu Gia</h1>
            <div class="entry-content">
                <p>Lạc Nam tỉnh dậy giữa đại điện xa hoa.</p>
                <div class="post-tts">Audio TTS junk</div>
            </div>
        </body>
    </html>
    """

    class MockTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            url_str = str(request.url)
            if "/wp-json/wp/v2/posts" in url_str:
                return httpx.Response(200, json=posts_json, headers={"x-wp-totalpages": "1", "x-wp-total": "1"})
            elif "chuong-1-lac-nam-thieu-gia" in url_str:
                return httpx.Response(200, text=chap_html)
            return httpx.Response(200, text="<html></html>")

    mock_client = HttpClient()
    mock_client._client = httpx.AsyncClient(transport=MockTransport())
    adapter = ConDuongBaChuAdapter(client=mock_client)

    # 1. Search
    results = await adapter.search("con duong ba chu")
    assert len(results) >= 1
    assert results[0].slug == "main"

    # 2. Detail
    story = await adapter.get_story_detail("main")
    assert "Con Đường Bá Chủ" in story.title
    assert story.author == "Akay Hậu"

    # 3. Chapters
    chapters, total_p = await adapter.list_chapters("main")
    assert len(chapters) == 1
    assert chapters[0].order == 1

    # 4. Content
    content = await adapter.get_chapter_content("main", "chuong-1-lac-nam-thieu-gia")
    assert '<p id="p-1">Lạc Nam tỉnh dậy giữa đại điện xa hoa.</p>' in content.content_html


@pytest.mark.asyncio
async def test_registry_integration() -> None:
    reg = create_default_registry()
    adapters = reg.list_adapters()
    assert len(adapters) == 3
    assert reg.get("storyaclick") is not None
    assert reg.get("akaytruyen") is not None
    assert reg.get("conduongbachu") is not None
