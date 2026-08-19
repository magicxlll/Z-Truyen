"""Pytest configuration and fixtures for Z-Truyen OPDS tests."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from fastapi.testclient import TestClient

from main import app
from mock_data import MOCK_BOOKS
from sources.base import BookSummary, Chapter


def _find_mock_book(book_id: str) -> BookSummary | None:
    """Find a mock book by ID."""
    for book in MOCK_BOOKS:
        if book.id == book_id:
            return BookSummary(
                id=book.id,
                title=book.title,
                author=book.author,
                summary=book.summary,
                cover_url=book.cover_url,
                source_id=book.source_id,
                url=f"https://storya.click/truyen/{book_id.split(':')[1]}" if ":" in book_id else "",
            )
    return None


def _find_mock_chapters(book_id: str) -> list[Chapter]:
    """Find mock chapters for a book."""
    for book in MOCK_BOOKS:
        if book.id == book_id:
            return [
                Chapter(
                    id=ch.id,
                    title=ch.title,
                    order=ch.order,
                    book_id=ch.book_id,
                    url=f"https://storya.click/{ch.id}",
                )
                for ch in book.chapters
            ]
    return []


@pytest.fixture
def mock_storya_adapter():
    """Create a mock storya adapter for testing."""
    mock_adapter = MagicMock()
    mock_adapter.list_books = AsyncMock(return_value=[])
    mock_adapter.search = AsyncMock(return_value=[])
    mock_adapter.get_book = AsyncMock(side_effect=ValueError("Book not found"))
    mock_adapter.list_chapters = AsyncMock(return_value=[])
    mock_adapter.get_chapter_content = AsyncMock(side_effect=ValueError("Chapter not found"))
    mock_adapter.close = AsyncMock()

    # Override get_book to return mock data for known IDs
    async def mock_get_book(book_id: str) -> BookSummary:
        book = _find_mock_book(book_id)
        if book:
            return book
        raise ValueError(f"Book not found: {book_id}")

    async def mock_list_chapters(book_id: str, page: int = 1) -> list[Chapter]:
        return _find_mock_chapters(book_id)

    mock_adapter.get_book = AsyncMock(side_effect=mock_get_book)
    mock_adapter.list_chapters = AsyncMock(side_effect=mock_list_chapters)

    return mock_adapter


@pytest.fixture
def client(mock_storya_adapter) -> TestClient:
    """Return a FastAPI test client with mock adapter."""
    # Set up the adapter in app state
    app.state.storya_adapter = mock_storya_adapter
    yield TestClient(app)
    # Clean up
    if hasattr(app.state, "storya_adapter"):
        delattr(app.state, "storya_adapter")


@pytest.fixture
def mock_books() -> list:
    """Return the mock books data."""
    return MOCK_BOOKS
