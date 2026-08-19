"""Unit tests for foundational models, IDs, sanitizer and SQLite storage."""

import pytest
from app.domain.models import Story, Chapter, VolumeBundle, Source
from app.domain.ids import (
    slugify,
    build_story_id,
    build_chapter_id,
    build_volume_id,
    build_volume_filename,
    build_chapter_filename,
)
from app.domain.sanitizer import sanitize_chapter_html, clean_vietnamese_text
from app.cache.database import init_db
from app.cache.metadata_repo import MetadataRepository
from app.cache.object_storage import ObjectStorage


def test_slugify() -> None:
    assert slugify("Con Đường Bá Chủ") == "con-duong-ba-chu"
    assert slugify("Đấu Phá Khung Thương!") == "dau-pha-khung-thuong"
    assert slugify("Story & Multi-Word Slug") == "story-multi-word-slug"


def test_id_and_filename_builders() -> None:
    assert build_story_id("conduongbachu", "main") == "conduongbachu:main"
    assert build_chapter_id("storya", "pham-nhan-tu-tien", "chap-1") == "storya:pham-nhan-tu-tien:chap-1"
    assert build_volume_id("akaytruyen", "vu-dong-can-khon", 1) == "akaytruyen:vu-dong-can-khon:v01"
    assert (
        build_volume_filename("conduongbachu", "main", 1)
        == "ztruyen_conduongbachu_main_v01.epub"
    )
    assert (
        build_chapter_filename("conduongbachu", "main", 1)
        == "ztruyen_conduongbachu_main_c0001.epub"
    )


def test_vietnamese_sanitizer() -> None:
    raw_html = """
    <div>
        <script>alert('xss');</script>
        <p>Chương 1: Khởi đầu mới</p>
        <br/>
        <p>Đây là đoạn văn thứ nhất đầy đủ dấu tiếng Việt: Tiên Hiệp &amp; Huyền Huyễn.</p>
        <p>Nguồn: Truyện Full</p>
        <p>Ủng hộ dịch giả tại momo 123456</p>
        <p>Đoạn văn kết thúc câu chuyện.</p>
    </div>
    """
    xhtml = sanitize_chapter_html(raw_html)
    assert '<p id="p-1">Chương 1: Khởi đầu mới</p>' in xhtml
    assert '<p id="p-2">Đây là đoạn văn thứ nhất đầy đủ dấu tiếng Việt: Tiên Hiệp &amp; Huyền Huyễn.</p>' in xhtml
    assert '<p id="p-3">Đoạn văn kết thúc câu chuyện.</p>' in xhtml
    assert "alert" not in xhtml
    assert "Nguồn: Truyện Full" not in xhtml
    assert "Ủng hộ dịch giả" not in xhtml


def test_metadata_repo_and_storage(tmp_path) -> None:
    db_file = tmp_path / "test.db"
    init_db(db_file)
    repo = MetadataRepository(db_file)

    source = Source(id="testsource", name="Test Source", base_url="https://test.com", adapter_type="json_api")
    repo.upsert_source(source)
    fetched_source = repo.get_source("testsource")
    assert fetched_source is not None
    assert fetched_source.name == "Test Source"

    story = Story(
        id="testsource:slug1",
        source_id="testsource",
        slug="slug1",
        title="Truyện Thử Nghiệm",
        author="Tác Giả A",
        genres=["Tiên Hiệp", "Huyền Huyễn"],
    )
    repo.upsert_story(story)
    fetched_story = repo.get_story("testsource", "slug1")
    assert fetched_story is not None
    assert fetched_story.title == "Truyện Thử Nghiệm"
    assert "Tiên Hiệp" in fetched_story.genres

    # Test Object Storage
    storage = ObjectStorage(epub_dir=tmp_path / "epubs", cover_dir=tmp_path / "covers")
    test_bytes = b"sample epub binary content"
    saved_path = storage.save_epub("test.epub", test_bytes)
    assert saved_path.exists()
    assert storage.has_epub("test.epub")
    assert storage.get_epub("test.epub") == test_bytes
    assert storage.calculate_sha1(test_bytes) == storage.calculate_file_sha1(saved_path)
