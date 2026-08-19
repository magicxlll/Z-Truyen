"""Unit tests for EPUB builder, templates, and Volume Bundler."""

import pytest
import io
from ebooklib import epub
from app.domain.models import Chapter, StorySummary, Story, ChapterSummary, ChapterContent
from app.epub.builder import EpubBuilder
from app.epub.bundler import VolumeBundler
from app.epub.template import EPUB_CSS
from app.cache.metadata_repo import MetadataRepository
from app.cache.object_storage import ObjectStorage
from app.sources.registry import SourceRegistry


def test_epub_builder_generates_valid_book() -> None:
    chapters = [
        Chapter(
            id="test:slug:c1",
            story_id="test:slug",
            order_num=1,
            title="Chương 1: Mở Đầu",
            original_url="http://test.com/c1",
            content_clean='<p id="p-1">Đoạn văn mở đầu cuốn sách.</p><p id="p-2">Đoạn thứ hai đầy đủ dấu tiếng Việt.</p>',
        ),
        Chapter(
            id="test:slug:c2",
            story_id="test:slug",
            order_num=2,
            title="Chương 2: Tiến Bước",
            original_url="http://test.com/c2",
            content_clean='<p id="p-1">Đoạn văn chương hai.</p>',
        ),
    ]

    builder = EpubBuilder()
    epub_bytes, sha1 = builder.build(
        identifier="urn:ztruyen:test:slug:v01",
        title="Truyện Thử Nghiệm",
        author="Tác Giả Mẫu",
        source_name="Test Source",
        volume_title="Tập 01 (Chương 1-2)",
        chapters=chapters,
    )

    assert len(epub_bytes) > 0
    assert len(sha1) == 40  # SHA-1 hex string length

    # Read back with ebooklib to verify valid EPUB structure
    book = epub.read_epub(io.BytesIO(epub_bytes))
    assert book.get_metadata("DC", "title")[0][0] == "Truyện Thử Nghiệm - Tập 01 (Chương 1-2)"
    assert book.get_metadata("DC", "creator")[0][0] == "Tác Giả Mẫu"
    assert book.get_metadata("DC", "language")[0][0] == "vi"

    # Verify items exist (nav, title page, 2 chapters, style.css)
    items = list(book.get_items())
    file_names = [item.file_name for item in items]
    assert "style.css" in file_names
    assert "title_page.xhtml" in file_names
    assert "chapter_0001.xhtml" in file_names
    assert "chapter_0002.xhtml" in file_names


@pytest.mark.asyncio
async def test_volume_bundler_flow(tmp_path) -> None:
    db_file = tmp_path / "test_bundler.db"
    repo = MetadataRepository(db_file)
    storage = ObjectStorage(epub_dir=tmp_path / "epubs", cover_dir=tmp_path / "covers")

    class MockAdapter:
        id = "mocksource"
        name = "Mock Source"
        base_url = "https://mock.com"
        supports_login = False
        client = None

        async def get_story_detail(self, story_slug: str) -> Story:
            return Story(
                id=f"{self.id}:{story_slug}",
                source_id=self.id,
                slug=story_slug,
                title="Đại Chúa Tể",
                author="Thiên Tằm Thổ Đậu",
                total_chapters=105,
            )

        async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
            return [
                ChapterSummary(
                    order=i,
                    title=f"Chương {i}",
                    slug=f"chuong-{i}",
                    url=f"https://mock.com/{i}",
                )
                for i in range(1, 106)
            ]

        async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
            num = chap_slug.replace("chuong-", "")
            return ChapterContent(
                source_id=self.id,
                story_slug=story_slug,
                chap_slug=chap_slug,
                title=f"Chương {num}",
                order=int(num),
                content_html=f'<p id="p-1">Nội dung chương số {num}.</p>',
                original_url=f"https://mock.com/{num}",
            )

    registry = SourceRegistry()
    registry.register(MockAdapter())

    bundler = VolumeBundler(
        metadata_repo=repo,
        object_storage=storage,
        source_registry=registry,
        chapters_per_volume=50,
    )

    # Test slice calculations: 105 chapters -> 3 volumes (50, 50, 5)
    slices = bundler.calculate_volume_slices(105)
    assert len(slices) == 3
    assert slices[0] == {"vol_index": 1, "start_order": 1, "end_order": 50, "count": 50}
    assert slices[1] == {"vol_index": 2, "start_order": 51, "end_order": 100, "count": 50}
    assert slices[2] == {"vol_index": 3, "start_order": 101, "end_order": 105, "count": 5}

    # Build Volume 1
    path_vol1, sha1_vol1 = await bundler.get_or_build_volume("mocksource", "dai-chua-te", 1)
    assert path_vol1.exists()
    assert path_vol1.name == "ztruyen_mocksource_dai-chua-te_v01.epub"
    assert len(sha1_vol1) == 40

    # Verify cached retrieval
    cached_path, cached_sha1 = await bundler.get_or_build_volume("mocksource", "dai-chua-te", 1)
    assert cached_path == path_vol1
    assert cached_sha1 == sha1_vol1
