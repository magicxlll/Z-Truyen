"""OPDS endpoint tests for Z-Truyen backend."""

import pytest
from fastapi.testclient import TestClient

from main import app
from opds_renderer import escape_xml, render_root_catalog, render_book_detail
from mock_data import MOCK_BOOKS
from sources import BookSummary, Chapter


class TestHealthEndpoint:
    """Tests for the health check endpoint."""

    def test_healthz_returns_ok(self, client: TestClient) -> None:
        """Verify health endpoint returns status 'ok'."""
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert "version" in data


class TestOPDSRenderer:
    """Tests for the OPDS XML renderer functions."""

    def test_escape_xml_escapes_special_chars(self) -> None:
        """Test XML escaping handles special characters correctly."""
        # Test basic escaping
        assert escape_xml("&") == "&amp;"
        assert escape_xml("<") == "&lt;"
        assert escape_xml(">") == "&gt;"
        assert escape_xml('"') == "&quot;"
        assert escape_xml("'") == "&apos;"

        # Test combined escaping
        assert escape_xml("A & B < C > D \"E\" 'F'") == "A &amp; B &lt; C &gt; D &quot;E&quot; &apos;F&apos;"

        # Test Vietnamese text with special chars
        assert escape_xml("Trẻ < 18 tuổi & già > 65") == "Trẻ &lt; 18 tuổi &amp; già &gt; 65"

    def test_render_root_catalog_produces_valid_xml(self) -> None:
        """Test root catalog XML has valid structure."""
        xml_content = render_root_catalog([], "http://testserver")

        # Check XML declaration
        assert xml_content.startswith('<?xml version="1.0" encoding="UTF-8"?>')

        # Check required Atom elements
        assert "<feed xmlns=" in xml_content
        assert "xmlns:opds=" in xml_content
        assert "xmlns:dc=" in xml_content
        assert "<id>http://testserver/opds/</id>" in xml_content
        assert "<title>Z-Truyen OPDS Catalog</title>" in xml_content
        assert "<updated>" in xml_content
        assert "</feed>" in xml_content

        # Check navigation links
        assert 'rel="search"' in xml_content
        assert 'rel="self"' in xml_content
        assert 'rel="start"' in xml_content

    def test_render_root_catalog_contains_books(self) -> None:
        """Test books are rendered in the root catalog."""
        xml_content = render_root_catalog(MOCK_BOOKS, "http://testserver")

        # Check that all books appear in the catalog
        for book in MOCK_BOOKS:
            assert f"<title>{escape_xml(book.title)}</title>" in xml_content
            assert f"urn:uuid:{book.id}" in xml_content
            assert f"<author>\n    <name>{escape_xml(book.author)}</name>" in xml_content

    def test_render_book_detail_produces_valid_xml(self) -> None:
        """Test book detail XML has valid structure."""
        book = MOCK_BOOKS[0]
        xml_content = render_book_detail(book, "http://testserver")

        # Check book entry elements (entry-level XML, no XML declaration)
        assert f"urn:uuid:{book.id}" in xml_content
        assert f"<title>{escape_xml(book.title)}</title>" in xml_content
        assert f"<author>\n    <name>{escape_xml(book.author)}</name>" in xml_content
        assert f"<summary>{escape_xml(book.summary)}</summary>" in xml_content
        assert "<updated>" in xml_content
        assert "<entry>" in xml_content
        assert "</entry>" in xml_content

    def test_render_book_detail_contains_chapters(self) -> None:
        """Test chapters are rendered in book detail."""
        book = MOCK_BOOKS[0]
        xml_content = render_book_detail(book, "http://testserver")

        # Check chapters are included
        assert "simplified:navigation" in xml_content
        assert "Các Chương" in xml_content

        # Verify each chapter appears
        for chapter in book.chapters:
            assert f"urn:uuid:{chapter.id}" in xml_content
            assert f"<title>{escape_xml(chapter.title)}</title>" in xml_content

    def test_render_root_catalog_with_book_summary(self) -> None:
        """Test BookSummary from storya adapter renders correctly."""
        book = BookSummary(
            id="storya:test-book",
            title="Test Story",
            author="Test Author",
            summary="A test story summary",
            cover_url="https://example.com/cover.jpg",
            source_id="storya",
            url="https://storya.click/truyen/test-book"
        )
        xml_content = render_root_catalog([book], "http://testserver")

        # Check book entry
        assert f"urn:uuid:storya:test-book" in xml_content
        assert "<title>Test Story</title>" in xml_content
        assert "<author>\n    <name>Test Author</name>" in xml_content
        assert "<summary>A test story summary</summary>" in xml_content
        # Check that the href contains the book URL (without double-escaping)
        assert 'href="http://testserver/opds/book/storya:test-book"' in xml_content

    def test_render_book_detail_with_chapters_list(self) -> None:
        """Test book detail with chapters from API."""
        book = BookSummary(
            id="storya:test-book",
            title="Test Story",
            author="Test Author",
            summary="A test story",
            source_id="storya",
            url="https://storya.click/truyen/test-book"
        )
        chapters = [
            Chapter(
                id="storya:test-book:chapter-1",
                title="Chapter 1: Introduction",
                order=1,
                book_id="storya:test-book",
                url="https://storya.click/truyen/test-book/chapter-1"
            ),
            Chapter(
                id="storya:test-book:chapter-2",
                title="Chapter 2: The Beginning",
                order=2,
                book_id="storya:test-book",
                url="https://storya.click/truyen/test-book/chapter-2"
            )
        ]
        xml_content = render_book_detail(book, "http://testserver", chapters)

        # Check chapters are included
        assert "simplified:navigation" in xml_content
        assert "Các Chương" in xml_content
        assert "urn:uuid:storya:test-book:chapter-1" in xml_content
        assert "<title>Chapter 1: Introduction</title>" in xml_content
        assert "urn:uuid:storya:test-book:chapter-2" in xml_content
        assert "<title>Chapter 2: The Beginning</title>" in xml_content


class TestOPDSEndpoints:
    """Tests for OPDS API endpoints."""

    def test_opds_catalog_returns_xml(self, client: TestClient) -> None:
        """Test GET /opds returns XML catalog."""
        response = client.get("/opds")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/atom+xml;profile=opds-catalog;kind=navigation"
        assert '<?xml version="1.0" encoding="UTF-8"?>' in response.text
        assert "<feed" in response.text
        assert "</feed>" in response.text

    def test_opds_search_returns_xml(self, client: TestClient) -> None:
        """Test GET /opds/search returns XML catalog."""
        response = client.get("/opds/search", params={"q": "test query"})

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/atom+xml;profile=opds-catalog;kind=navigation"
        assert '<?xml version="1.0" encoding="UTF-8"?>' in response.text

    def test_opds_book_returns_400_for_unsupported_source(self, client: TestClient) -> None:
        """Test GET /opds/book/{id} returns 400 for unsupported source."""
        response = client.get("/opds/book/unsupported-source:book-id")

        assert response.status_code == 400
        assert "Unsupported book source" in response.text

    def test_opds_book_returns_404_for_unknown_book(self, client: TestClient) -> None:
        """Test GET /opds/book/{id} returns 404 for unknown book."""
        response = client.get("/opds/book/storya:nonexistent-book")

        assert response.status_code == 404
        assert "Book not found" in response.text

    def test_opds_book_returns_chapters_from_mock(self, client: TestClient) -> None:
        """Test GET /opds/book/{id} returns chapters for mock book."""
        valid_book_id = "storya:cdb-main-001"
        response = client.get(f"/opds/book/{valid_book_id}")

        assert response.status_code == 200
        assert response.headers["content-type"] == "application/atom+xml;profile=opds-catalog;kind=acquisition"

        # Check book details
        assert f"urn:uuid:{valid_book_id}" in response.text
        assert "<title>Con Đường Bá Chủ (Chính Truyện)</title>" in response.text

        # Check chapters are included
        assert "simplified:navigation" in response.text
        assert "Các Chương" in response.text

    def test_opds_download_returns_400_for_invalid_format(self, client: TestClient) -> None:
        """Test GET /opds/download/{id} returns 400 for invalid format."""
        response = client.get("/opds/download/invalid-chapter-id")

        assert response.status_code == 400
        assert "Invalid chapter ID format" in response.text

    def test_opds_download_returns_400_for_unsupported_source(self, client: TestClient) -> None:
        """Test GET /opds/download/{id} returns 400 for unsupported source."""
        response = client.get("/opds/download/unsupported:book:chapter")

        assert response.status_code == 400
        assert "Unsupported source" in response.text

    def test_opds_download_returns_404_for_missing_chapter(self, client: TestClient) -> None:
        """Test GET /opds/download/{id} returns 404 when chapter not found."""
        response = client.get("/opds/download/storya:book:chapter")

        # The mock adapter raises ValueError, which should return 404
        assert response.status_code == 404
        assert "Chapter not found" in response.text
