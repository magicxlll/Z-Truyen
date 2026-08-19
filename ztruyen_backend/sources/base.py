"""Source Adapter Base Class for Z-Truyen X3.

This module defines the common interface and utility functions for all story source adapters.
Each adapter implements the SourceAdapter protocol to fetch content from a specific source.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Protocol, Optional, Any
from urllib.parse import urljoin, urlparse, parse_qs


# =============================================================================
# Data Classes
# =============================================================================


@dataclass
class BookSummary:
    """Minimal book/story summary for catalog and search listings."""

    id: str
    title: str
    author: str
    summary: str = ""
    cover_url: Optional[str] = None
    source_id: str = ""
    url: str = ""


@dataclass
class Chapter:
    """Chapter metadata for table of contents."""

    id: str
    title: str
    order: int
    book_id: str
    url: str


@dataclass
class ChapterContent:
    """Full chapter content with HTML for reading and EPUB compilation."""

    id: str
    title: str
    content: str  # HTML content
    book_id: str
    chapter_order: int


# =============================================================================
# Source Adapter Protocol
# =============================================================================


class SourceAdapter(Protocol):
    """Protocol that all story source adapters must conform to.

    Each adapter is responsible for fetching content from a specific source website.
    The adapter handles the source-specific URL construction, API calls, and
    response parsing.

    Implementations should inherit from BaseSource or define these attributes:
        - id: str - Unique identifier (e.g., 'storyaclick')
        - name: str - Human-readable name (e.g., 'Storya.click')
    """

    async def search(self, query: str, page: int = 1) -> list[BookSummary]:
        """Search books by keyword.

        Args:
            query: Search keyword
            page: Page number (1-indexed)

        Returns:
            List of BookSummary matching the query
        """
        ...

    async def get_book(self, book_id: str) -> BookSummary:
        """Fetch detailed metadata for a single book.

        Args:
            book_id: Source-specific book identifier

        Returns:
            BookSummary with full metadata
        """
        ...

    async def list_chapters(self, book_id: str, page: int = 1) -> list[Chapter]:
        """Fetch paginated chapter list for a book.

        Args:
            book_id: Source-specific book identifier
            page: Page number (1-indexed)

        Returns:
            List of Chapter metadata
        """
        ...

    async def get_chapter_content(self, chapter: Chapter) -> ChapterContent:
        """Fetch raw HTML content of a single chapter.

        Args:
            chapter: Chapter object with id and url

        Returns:
            ChapterContent with HTML content
        """
        ...


# =============================================================================
# Base Source Class (Optional Helper)
# =============================================================================


class BaseSource:
    """Base class providing common functionality for source adapters.

    Subclasses should override class attributes and implement the abstract methods.
    This class is optional - adapters can implement SourceAdapter directly.
    """

    id: str = "base"
    """Unique identifier of the source"""

    name: str = "Base Source"
    """Human-readable source name"""

    base_url: str = ""
    """Base URL of the source website"""

    def __init__(self) -> None:
        """Initialize the source adapter."""
        self._client: Optional[Any] = None

    def _fix_cover_url(self, cover: Optional[str]) -> Optional[str]:
        """Fix cover URL by handling relative paths.

        Args:
            cover: Cover URL which may be absolute or relative

        Returns:
            Absolute URL or None if cover is empty
        """
        if not cover:
            return None
        if cover.startswith("//"):
            return f"https:{cover}"
        if cover.startswith("/"):
            return urljoin(self.base_url, cover)
        if not urlparse(cover).netloc:
            return urljoin(self.base_url, cover)
        return cover

    def _build_book_id(self, source_book_id: str) -> str:
        """Build composite book ID from source ID and source-specific ID.

        Args:
            source_book_id: Source-specific book identifier (slug, URL segment, etc.)

        Returns:
            Composite ID: {source_id}:{source_book_id}
        """
        return build_book_id(self.id, source_book_id)

    def _build_chapter_id(self, source_book_id: str, source_chapter_id: str) -> str:
        """Build composite chapter ID.

        Args:
            source_book_id: Source-specific book identifier
            source_chapter_id: Source-specific chapter identifier

        Returns:
            Composite ID: {source_id}:{source_book_id}:{source_chapter_id}
        """
        return build_chapter_id(self.id, source_book_id, source_chapter_id)


# =============================================================================
# Utility Functions
# =============================================================================


def build_book_id(source_id: str, source_book_id: str) -> str:
    """Build composite book ID from source and book identifiers.

    Creates a stable, unique identifier for a book across all sources.

    Args:
        source_id: Source adapter identifier (e.g., 'storyaclick')
        source_book_id: Source-specific book identifier (slug, ID, URL segment)

    Returns:
        Composite ID in format: {source_id}:{source_book_id}

    Example:
        >>> build_book_id("storyaclick", "dao-hai-tac")
        'storyaclick:dao-hai-tac'
    """
    return f"{source_id}:{source_book_id}"


def build_chapter_id(source_id: str, source_book_id: str, source_chapter_id: str) -> str:
    """Build composite chapter ID from source, book, and chapter identifiers.

    Creates a stable, unique identifier for a chapter across all sources.

    Args:
        source_id: Source adapter identifier
        source_book_id: Source-specific book identifier
        source_chapter_id: Source-specific chapter identifier

    Returns:
        Composite ID in format: {source_id}:{source_book_id}:{source_chapter_id}

    Example:
        >>> build_chapter_id("storyaclick", "dao-hai-tac", "chapter-1")
        'storyaclick:dao-hai-tac:chapter-1'
    """
    return f"{source_id}:{source_book_id}:{source_chapter_id}"


def build_chapter_id_from_order(source_id: str, source_book_id: str, order: int) -> str:
    """Build composite chapter ID using chapter order number.

    Useful when source doesn't provide a slug/ID for chapters.

    Args:
        source_id: Source adapter identifier
        source_book_id: Source-specific book identifier
        order: Chapter order number (1-indexed)

    Returns:
        Composite ID in format: {source_id}:{source_book_id}:c{order:04d}

    Example:
        >>> build_chapter_id_from_order("storyaclick", "dao-hai-tac", 5)
        'storyaclick:dao-hai-tac:c0005'
    """
    return f"{source_id}:{source_book_id}:c{order:04d}"


def normalize_url(url: str, base_url: str = "") -> str:
    """Normalize URL by handling relative paths and common variations.

    Args:
        url: URL to normalize (may be absolute or relative)
        base_url: Base URL for resolving relative URLs

    Returns:
        Normalized absolute URL

    Example:
        >>> normalize_url("/truyen/dao-hai-tac", "https://storya.click")
        'https://storya.click/truyen/dao-hai-tac'
    """
    if not url:
        return ""

    # Handle protocol-relative URLs
    if url.startswith("//"):
        return f"https:{url}"

    # Handle absolute URLs
    parsed = urlparse(url)
    if parsed.netloc:
        return url

    # Handle relative URLs with base
    if base_url:
        return urljoin(base_url, url)

    # Handle root-relative URLs
    if url.startswith("/"):
        if base_url:
            return urljoin(base_url, url)
        return url

    return url


def extract_id_from_url(url: str, pattern: str) -> Optional[str]:
    """Extract identifier from URL using regex pattern.

    Useful for extracting slugs or IDs from source URLs.

    Args:
        url: URL to extract from
        pattern: Regex pattern with one capture group for the ID

    Returns:
        Extracted identifier or None if no match

    Example:
        >>> extract_id_from_url(
        ...     "https://example.com/truyen/dao-hai-tac/chapter-1",
        ...     r"/truyen/([^/]+)"
        ... )
        'dao-hai-tac'
    """
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None


def generate_stable_hash(*parts: str) -> str:
    """Generate a stable hash from multiple string parts.

    Useful for creating deterministic identifiers.

    Args:
        *parts: String parts to hash

    Returns:
        MD5 hash of the concatenated parts (first 12 characters)

    Example:
        >>> generate_stable_hash("storyaclick", "dao-hai-tac", "1")
        'a1b2c3d4e5f6'
    """
    combined = ":".join(str(p) for p in parts)
    return hashlib.md5(combined.encode("utf-8")).hexdigest()[:12]


def parse_page_param(url: str) -> int:
    """Extract page number from URL query parameters.

    Args:
        url: URL potentially containing a 'page' parameter

    Returns:
        Page number (1 if not specified or invalid)

    Example:
        >>> parse_page_param("https://example.com/page?page=3")
        3
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    page_values = params.get("page", ["1"])
    try:
        return max(1, int(page_values[0]))
    except (ValueError, IndexError):
        return 1
