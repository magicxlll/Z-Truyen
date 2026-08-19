# Contract: Source Adapter Interface Protocol

**Feature**: `001-z-truyen-x3`  
**Date**: 2026-08-18  
**Status**: Stable  

---

## 1. Python Source Adapter Protocol Specification

Mọi Source Adapter (bao gồm `storyaclick`, `akaytruyen`, `conduongbachu` và các nguồn bổ sung trong tương lai) **BẮT BUỘC** phải kế thừa và triển khai đầy đủ các phương thức async trong `SourceAdapter` Protocol:

```python
from typing import Protocol, runtime_checkable
from pydantic import BaseModel
from datetime import datetime

class StorySummary(BaseModel):
    source_id: str
    slug: str
    title: str
    author: str = "Đang cập nhật"
    cover_url: str | None = None
    kind: str = "text"

class StoryDetail(StorySummary):
    description: str = ""
    status: str = "Đang cập nhật"
    genres: list[str] = []
    total_chapters: int = 0
    updated_at: datetime = datetime.now()

class ChapterSummary(BaseModel):
    order: int
    title: str
    slug: str
    url: str
    is_vip: bool = False

class ChapterContent(BaseModel):
    source_id: str
    story_slug: str
    chap_slug: str
    title: str
    order: int
    content_html: str
    original_url: str

class GenreItem(BaseModel):
    id: str
    name: str
    slug: str
    url: str

@runtime_checkable
class SourceAdapter(Protocol):
    id: str
    name: str
    base_url: str
    supports_login: bool

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        """Tìm kiếm truyện theo từ khóa."""
        ...

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        """Lấy danh sách truyện Hot."""
        ...

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        """Lấy danh sách truyện mới nhất."""
        ...

    async def get_genres(self) -> list[GenreItem]:
        """Lấy danh sách thể loại truyện của nguồn."""
        ...

    async def get_story_detail(self, story_slug: str) -> StoryDetail:
        """Lấy thông tin chi tiết bộ truyện."""
        ...

    async def list_chapters(self, story_slug: str, page: int = 1, page_size: int = 100) -> tuple[list[ChapterSummary], int]:
        """Lấy danh sách chương phân trang (trả về danh sách và tổng số trang)."""
        ...

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        """Lấy toàn bộ danh sách chương của bộ truyện (hỗ trợ gom quyển)."""
        ...

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        """Cào và bóc tách nội dung văn bản sạch của 1 chương."""
        ...

    async def login(self, username: str, password: str) -> bool:
        """Đăng nhập tài khoản VIP (nếu nguồn hỗ trợ)."""
        ...
```

---

## 2. Quy Tắc Chuẩn Hóa Nội Dung (Content Sanitization Rules)

1. **XHTML Well-formedness**: Mọi đoạn văn trong `content_html` phải được bao bởi thẻ `<p id="p-{index}">` hợp lệ.
2. **Loại bỏ quảng cáo & text rác**: Loại bỏ các thẻ quảng cáo, link chèn ngoài, text xin donate/tts gây rối mắt trên E-ink.
3. **Mã hóa UTF-8 tiếng Việt**: Giữ nguyên vẹn dấu thanh tiếng Việt (NFC normalized), không bị lỗi ký tự `?` hay Unicode surrogate.
