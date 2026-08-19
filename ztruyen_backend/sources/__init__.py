"""Z-Truyen X3 Source Adapters.

This module provides the base classes and protocols for implementing
story source adapters. Each adapter fetches content from a specific
source website and returns normalized data structures.
"""

from sources.base import (
    # Data Classes
    BookSummary,
    Chapter,
    ChapterContent,
    # Protocol
    SourceAdapter,
    # Base Class
    BaseSource,
    # Utility Functions
    build_book_id,
    build_chapter_id,
    build_chapter_id_from_order,
    normalize_url,
    extract_id_from_url,
    generate_stable_hash,
    parse_page_param,
)
from sources.storya import StoryaAdapter, create_storya_adapter
from sources.conduongbachu import (
    ConDuongBaChuAdapter,
    create_conduongbachu_adapter,
    STORIES,
)

__all__ = [
    # Data Classes
    "BookSummary",
    "Chapter",
    "ChapterContent",
    # Protocol
    "SourceAdapter",
    # Base Class
    "BaseSource",
    # Utility Functions
    "build_book_id",
    "build_chapter_id",
    "build_chapter_id_from_order",
    "normalize_url",
    "extract_id_from_url",
    "generate_stable_hash",
    "parse_page_param",
    # Storya Adapter
    "StoryaAdapter",
    "create_storya_adapter",
    # ConDuongBaChu Adapter
    "ConDuongBaChuAdapter",
    "create_conduongbachu_adapter",
    "STORIES",
]
