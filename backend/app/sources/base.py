"""Source Adapter Protocol specification for story scrapers."""

from typing import Protocol, runtime_checkable
from app.domain.models import StorySummary, Story, ChapterSummary, ChapterContent, GenreItem


@runtime_checkable
class SourceAdapter(Protocol):
    """Protocol that all story source adapters must conform to."""

    id: str
    name: str
    base_url: str
    supports_login: bool

    async def search(self, query: str, page: int = 1) -> list[StorySummary]:
        """Search stories by keyword."""
        ...

    async def get_hot(self, page: int = 1) -> list[StorySummary]:
        """Retrieve popular / trending stories."""
        ...

    async def get_latest(self, page: int = 1) -> list[StorySummary]:
        """Retrieve newest / updated stories."""
        ...

    async def get_genres(self) -> list[GenreItem]:
        """Retrieve list of genre categories."""
        ...

    async def get_story_detail(self, story_slug: str) -> Story:
        """Fetch detailed metadata for a single story."""
        ...

    async def list_chapters(
        self, story_slug: str, page: int = 1, page_size: int = 100
    ) -> tuple[list[ChapterSummary], int]:
        """Fetch paginated chapters (returns chapter list and total pages)."""
        ...

    async def get_all_chapters(self, story_slug: str) -> list[ChapterSummary]:
        """Retrieve all chapters for volume bundling."""
        ...

    async def get_chapter_content(self, story_slug: str, chap_slug: str) -> ChapterContent:
        """Fetch raw HTML content of a single chapter."""
        ...

    async def login(self, username: str, password: str) -> bool:
        """Authenticate user session if source supports VIP access."""
        ...
