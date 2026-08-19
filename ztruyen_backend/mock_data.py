"""Mock catalog data for Phase A-1 validation."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class MockChapter:
    id: str
    title: str
    order: int
    book_id: str


@dataclass
class MockBook:
    id: str
    title: str
    author: str
    summary: str
    cover_url: Optional[str]
    source_id: str
    chapters: list[MockChapter]


MOCK_BOOKS = [
    MockBook(
        id="storya:cdb-main-001",
        title="Con Đường Bá Chủ (Chính Truyện)",
        author="Akay Hau",
        summary="Truyện tiên hiệp huyền huyễn kể về Con Đường Bá Chủ. Một tác phẩm đặc sắc với nội dung hấp dẫn, lôi cuốn người đọc từ đầu đến cuối.",
        cover_url=None,
        source_id="storya",
        chapters=[
            MockChapter(id="storya:cdb-main-001:chuong-1", title="Chương 1: Khởi Nguyên", order=1, book_id="storya:cdb-main-001"),
            MockChapter(id="storya:cdb-main-001:chuong-2", title="Chương 2: Bước Đầu Tu Luyện", order=2, book_id="storya:cdb-main-001"),
            MockChapter(id="storya:cdb-main-001:chuong-3", title="Chương 3: Linh Khí Đại Đế", order=3, book_id="storya:cdb-main-001"),
        ],
    ),
    MockBook(
        id="storya:van-tuong-son-ha",
        title="Vạn Tượng Sơn Hà",
        author="Huyency",
        summary="Một thế giới tu luyện rộng lớn với vô số bí ẩn chờ được khám phá.",
        cover_url=None,
        source_id="storya",
        chapters=[
            MockChapter(id="storya:van-tuong-son-ha:chuong-1", title="Chương 1: Khai Thiên", order=1, book_id="storya:van-tuong-son-ha"),
        ],
    ),
]
