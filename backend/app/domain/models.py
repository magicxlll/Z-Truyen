"""Domain data models using Pydantic v2."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class Source(BaseModel):
    """Source adapter metadata model."""
    id: str = Field(..., description="Unique identifier of the source (e.g., 'storyaclick')")
    name: str = Field(..., description="Human-readable source name")
    base_url: str = Field(..., description="Base URL of source website")
    adapter_type: Literal["json_api", "laravel_html", "wp_json", "custom"] = "json_api"
    supports_login: bool = False
    enabled: bool = True


class StorySummary(BaseModel):
    """Minimal story summary for catalog and search listing."""
    source_id: str
    slug: str
    title: str
    author: str = "Đang cập nhật"
    cover_url: str | None = None
    kind: str = "text"


class Story(BaseModel):
    """Detailed story entity model."""
    id: str = Field(..., description="Composite ID: {source_id}:{slug}")
    source_id: str
    slug: str
    title: str
    author: str = "Đang cập nhật"
    description: str = ""
    cover_url: str | None = None
    status: str = "Đang cập nhật"
    genres: list[str] = Field(default_factory=list)
    total_chapters: int = 0
    updated_at: datetime = Field(default_factory=datetime.now)


class ChapterSummary(BaseModel):
    """Lightweight chapter metadata for table of contents."""
    order: int
    title: str
    slug: str
    url: str
    is_vip: bool = False


class Chapter(BaseModel):
    """Full chapter content model for reading and EPUB compilation."""
    id: str = Field(..., description="Composite ID: {source_id}:{story_slug}:{chap_slug}")
    story_id: str
    order_num: int
    title: str
    original_url: str
    content_clean: str
    is_vip: bool = False
    scraped_at: datetime = Field(default_factory=datetime.now)


class ChapterContent(BaseModel):
    """DTO returned by source scraper."""
    source_id: str
    story_slug: str
    chap_slug: str
    title: str
    order: int
    content_html: str
    original_url: str


class VolumeBundle(BaseModel):
    """Compiled EPUB volume bundle representation."""
    id: str = Field(..., description="Composite ID: {source_id}:{story_slug}:v{vol_index:02d}")
    story_id: str
    vol_index: int
    start_order: int
    end_order: int
    chapter_count: int
    filename: str
    sha1_hash: str
    file_size_bytes: int
    built_at: datetime = Field(default_factory=datetime.now)


class SourceCredential(BaseModel):
    """Credential data for VIP authenticated sources."""
    source_id: str
    username: str
    password_encrypted: str
    session_cookies_json: str | None = None
    last_login_at: datetime | None = None


class GenreItem(BaseModel):
    """Genre category definition."""
    id: str
    name: str
    slug: str
    url: str = ""


class CacheEntry(BaseModel):
    """Disk cache entry tracking metadata."""
    key: str
    file_path: str
    mime_type: str
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.now)
    last_accessed_at: datetime = Field(default_factory=datetime.now)
