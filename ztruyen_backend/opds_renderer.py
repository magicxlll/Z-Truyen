"""OPDS XML renderer for Z-Truyen catalog generation."""

from datetime import datetime, timezone
from typing import Optional, Union

from mock_data import MockBook, MockChapter
from sources.base import BookSummary, Chapter


def escape_xml(text: str) -> str:
    """Escape special XML characters.

    Args:
        text: Input text to escape.

    Returns:
        Text with XML special characters escaped.
    """
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """Format datetime as RFC 3339 for Atom/OPDS.

    Args:
        dt: Datetime to format. If None, uses current UTC time.

    Returns:
        RFC 3339 formatted timestamp string.
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def render_book_entry(book: Union[MockBook, BookSummary], base_url: str) -> str:
    """Render single book as OPDS entry.

    Args:
        book: Book to render (MockBook or BookSummary).
        base_url: Base URL for the application.

    Returns:
        OPDS entry XML string.
    """
    # Build cover link if available
    cover_url = getattr(book, 'cover_url', None)
    cover_link = ""
    if cover_url:
        cover_link = f"""<link rel="http://opds-spec.org/cover"
      type="image/jpeg"
      href="{escape_xml(cover_url)}"/>"""

    # Build author element
    author_xml = f"""<author>
    <name>{escape_xml(book.author)}</name>
  </author>"""

    # Build summary element (MockBook has 'summary', BookSummary has empty default)
    summary = getattr(book, 'summary', '') or ''
    summary_xml = f"""<summary>{escape_xml(summary)}</summary>""" if summary else ""

    entry = f"""<entry>
  <id>urn:uuid:{book.id}</id>
  <title>{escape_xml(book.title)}</title>
  {author_xml}
  {summary_xml}
  <updated>{format_timestamp()}</updated>
  {cover_link}
  <link rel="alternate"
      type="application/atom+xml;profile=opds-catalog;kind=acquisition"
      href="{base_url}/opds/book/{book.id}"/>
  <link rel="http://opds-spec.org/acquisition/open-access"
      type="application/atom+xml;profile=opds-catalog;kind=acquisition"
      href="{base_url}/opds/book/{book.id}"/>
  <dc:identifier>{escape_xml(book.id)}</dc:identifier>
  <dc:publisher>Z-Truyen</dc:publisher>
</entry>"""

    return entry


def render_book_detail(book: Union[MockBook, BookSummary], base_url: str, chapters: list[Chapter] = None) -> str:
    """Render book detail with chapter list.

    Args:
        book: Book to render (MockBook or BookSummary).
        base_url: Base URL for the application.
        chapters: List of chapters (for BookSummary). If None, uses MockBook.chapters.

    Returns:
        OPDS entry XML string with navigation links for chapters.
    """
    # Get chapters from parameter or MockBook.chapters
    book_chapters: list = []
    if chapters is not None:
        book_chapters = chapters
    elif hasattr(book, 'chapters'):
        book_chapters = getattr(book, 'chapters', [])

    # Build chapter navigation links
    chapters_nav = ""
    if book_chapters:
        chapters_list = ""
        for chapter in sorted(book_chapters, key=lambda c: c.order):
            chapters_list += f"""<entry>
      <id>urn:uuid:{chapter.id}</id>
      <title>{escape_xml(chapter.title)}</title>
      <updated>{format_timestamp()}</updated>
      <link rel="alternate"
          type="text/html"
          href="{base_url}/opds/read/{chapter.id}"/>
      <link rel="http://opds-spec.org/acquisition/open-access"
          type="application/epub+zip"
          href="{base_url}/opds/download/{chapter.id}"/>
      <dc:identifier>{escape_xml(chapter.id)}</dc:identifier>
      <dc:relation>Chapter {chapter.order}</dc:relation>
    </entry>"""

        chapters_nav = f"""<simplified:navigation xmlns:simplified="http://librarysimplified.org/terms/">
    <id>urn:uuid:{book.id}-chapters</id>
    <title>Các Chương</title>
    {chapters_list}
  </simplified:navigation>"""

    # Build author element
    author_xml = f"""<author>
    <name>{escape_xml(book.author)}</name>
  </author>"""

    # Build summary element
    summary = getattr(book, 'summary', '') or ''
    summary_xml = f"""<summary>{escape_xml(summary)}</summary>""" if summary else ""

    entry = f"""<entry>
  <id>urn:uuid:{book.id}</id>
  <title>{escape_xml(book.title)}</title>
  {author_xml}
  {summary_xml}
  <updated>{format_timestamp()}</updated>
  <link rel="self"
      type="application/atom+xml;profile=opds-catalog;kind=acquisition"
      href="{base_url}/opds/book/{book.id}"/>
  <dc:identifier>{escape_xml(book.id)}</dc:identifier>
  <dc:publisher>Z-Truyen</dc:publisher>
</entry>
{chapters_nav}"""

    return entry


def render_root_catalog(books: list[Union[MockBook, BookSummary]], base_url: str) -> str:
    """Render OPDS root catalog as Atom XML.

    Args:
        books: List of books to include in the catalog (MockBook or BookSummary).
        base_url: Base URL for the application.

    Returns:
        OPDS root catalog XML string.
    """
    # Render all book entries
    entries_xml = "\n".join(render_book_entry(book, base_url) for book in books)

    # Build navigation link
    nav_link = f"""<link rel="search"
      type="application/atom+xml;profile=opds-catalog;kind=search"
      href="{base_url}/opds/search"/>
  <link rel="self"
      type="application/atom+xml;profile=opds-catalog;kind=navigation"
      href="{base_url}/opds/"/>
  <link rel="start"
      type="application/atom+xml;profile=opds-catalog;kind=navigation"
      href="{base_url}/opds/"/>"""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog"
      xmlns:dc="http://purl.org/dc/elements/1.1/"
      xml:lang="vi">
  <id>{base_url}/opds/</id>
  <title>Z-Truyen OPDS Catalog</title>
  <updated>{format_timestamp()}</updated>
  <icon>{base_url}/static/favicon.ico</icon>
  {nav_link}
  {entries_xml}
</feed>"""

    return xml
