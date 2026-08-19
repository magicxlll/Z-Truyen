"""EPUB builder for Z-Truyen X3 - generates EPUB files from chapter content."""

from __future__ import annotations

import io
import re
import unicodedata
from typing import Optional

import httpx
from ebooklib import epub
from PIL import Image

from sources.base import ChapterContent


# Maximum cover image dimensions for E-ink devices
MAX_COVER_WIDTH = 800
MAX_COVER_HEIGHT = 1200

# EPUB CSS styles for Vietnamese content
EPUB_CSS = """
@charset "utf-8";

body {
    margin: 5% 4%;
    padding: 0;
    font-family: serif;
    font-size: 1.05em;
    line-height: 1.6;
    text-align: justify;
    text-justify: inter-word;
    color: #000000;
    background-color: #ffffff;
}

h1, h2, h3 {
    text-align: center;
    font-weight: bold;
    margin-top: 1.5em;
    margin-bottom: 1em;
    page-break-before: always;
    page-break-after: avoid;
    line-height: 1.3;
}

p {
    margin: 0.4em 0;
    text-indent: 1.5em;
    orphans: 2;
    widows: 2;
}

p.no-indent {
    text-indent: 0;
}

.center {
    text-align: center;
    text-indent: 0;
}

hr {
    border: none;
    border-top: 1px solid #666666;
    margin: 2em auto;
    width: 60%;
}
""".strip()


def sanitize_filename(text: str) -> str:
    """Sanitize text for use in filenames.

    Args:
        text: Input text to sanitize.

    Returns:
        Sanitized text safe for filenames.
    """
    if not text:
        return "untitled"

    # Normalize unicode to NFC form
    text = unicodedata.normalize("NFC", text)

    # Replace invalid filename characters
    invalid_chars = r'[<>:"/\\|?*\x00-\x1f]'
    text = re.sub(invalid_chars, "_", text)

    # Replace spaces and multiple underscores with single underscore
    text = re.sub(r'[\s]+', "_", text)
    text = re.sub(r'_+', "_", text)

    # Truncate if too long
    if len(text) > 100:
        text = text[:100].rstrip("_")

    return text.strip("_") or "untitled"


def generate_epub_filename(source_id: str, book_id: str, chapter_order: int) -> str:
    """Generate EPUB filename in the specified format.

    Args:
        source_id: Source identifier.
        book_id: Book identifier.
        chapter_order: Chapter order number.

    Returns:
        Sanitized EPUB filename.
    """
    safe_source = sanitize_filename(source_id)
    safe_book = sanitize_filename(book_id)
    return f"ztruyen__{safe_source}__{safe_book}__{chapter_order:04d}.epub"


def clean_html_content(html_content: str) -> str:
    """Clean and sanitize HTML content for EPUB.

    Args:
        html_content: Raw HTML content from scraper.

    Returns:
        Cleaned XHTML-compatible content.
    """
    if not html_content or not html_content.strip():
        return "<p>[Không có nội dung]</p>"

    # Convert <br> tags to newlines
    cleaned = re.sub(r"(?i)<br\s*/?>", "\n", html_content)

    # Remove unwanted elements
    unwanted_tags = [
        "script", "style", "iframe", "audio", "video", "img", "noscript",
        "svg", "button", "form", "select", "option", "nav", "aside",
        "a", "input", "textarea"
    ]
    for tag in unwanted_tags:
        # Remove complete tags with content
        cleaned = re.sub(rf"<{tag}[^>]*>.*?</{tag}>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
        # Remove self-closing tags
        cleaned = re.sub(rf"<{tag}[^>]*/?>", "", cleaned, flags=re.IGNORECASE)

    # Normalize whitespace
    cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
    cleaned = cleaned.strip()

    if not cleaned:
        return "<p>[Nội dung đang được cập nhật]</p>"

    return cleaned


def convert_to_xhtml(html_content: str, title: str) -> str:
    """Convert HTML content to XHTML format for EPUB.

    Args:
        html_content: HTML content to convert.
        title: Chapter title for the XHTML document.

    Returns:
        XHTML-formatted content as string.
    """
    cleaned = clean_html_content(html_content)

    # Wrap in XHTML structure if not already wrapped
    if not cleaned.startswith("<?xml") and not cleaned.startswith("<html"):
        xhtml = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="vi" lang="vi">
<head>
    <meta charset="utf-8" />
    <title>{_escape_xml(title)}</title>
    <link rel="stylesheet" type="text/css" href="style.css" />
</head>
<body>
    <h2>{_escape_xml(title)}</h2>
    <div class="chapter-content">
{cleaned}
    </div>
</body>
</html>'''
        return xhtml

    return cleaned


def _escape_xml(text: str) -> str:
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


def resize_image(image_bytes: bytes, max_width: int, max_height: int) -> bytes:
    """Resize image if it exceeds maximum dimensions.

    Args:
        image_bytes: Raw image bytes.
        max_width: Maximum width in pixels.
        max_height: Maximum height in pixels.

    Returns:
        Resized image bytes, or original if resizing not needed.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if img.mode in ("RGBA", "P", "LA"):
            rgb_img = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            rgb_img.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = rgb_img

        # Check if resize is needed
        if img.width <= max_width and img.height <= max_height:
            return image_bytes

        # Calculate new dimensions maintaining aspect ratio
        ratio = min(max_width / img.width, max_height / img.height)
        new_width = int(img.width * ratio)
        new_height = int(img.height * ratio)

        # Resize with high-quality resampling
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Save to bytes
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85, optimize=True)
        return output.getvalue()

    except Exception:
        # Return original bytes if resize fails
        return image_bytes


async def fetch_cover_image(cover_url: str) -> Optional[bytes]:
    """Download cover image from URL.

    Args:
        cover_url: URL of the cover image.

    Returns:
        Image bytes or None if download fails.
    """
    if not cover_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(cover_url)
            response.raise_for_status()

            content_type = response.headers.get("content-type", "").lower()
            if "image" not in content_type and not any(
                cover_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]
            ):
                return None

            return response.content

    except Exception:
        return None


def add_cover_image(book: epub.EpubBook, cover_url: str) -> None:
    """Download and add cover image to EPUB book.

    Args:
        book: EpubBook instance to add cover to.
        cover_url: URL of the cover image.
    """
    import asyncio

    try:
        # Run async fetch in sync context
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    image_bytes = loop.run_until_complete(fetch_cover_image(cover_url))

    if image_bytes:
        try:
            # Resize if needed
            resized = resize_image(image_bytes, MAX_COVER_WIDTH, MAX_COVER_HEIGHT)
            book.set_cover("cover.jpg", resized)
        except Exception:
            # Try with original if resize fails
            try:
                book.set_cover("cover.jpg", image_bytes)
            except Exception:
                pass  # Silently fail - cover is optional


def create_epub_metadata(
    book_title: str,
    author: str,
    chapter_title: str
) -> tuple[epub.EpubItem, epub.EpubItem, epub.EpubNcx]:
    """Create metadata items for EPUB book.

    Args:
        book_title: Title of the book.
        author: Author name.
        chapter_title: Title of the chapter.

    Returns:
        Tuple of (metadata item, guide item, NCX item).
    """
    # Create metadata as Dublin Core items
    metadata_item = epub.EpubItem(
        uid="metadata",
        file_name="metadata.xml",
        media_type="application/xml",
        content=f'''<?xml version="1.0" encoding="utf-8"?>
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>{_escape_xml(book_title)}</dc:title>
    <dc:creator>{_escape_xml(author)}</dc:creator>
    <dc:language>vi</dc:language>
    <dc:rights>Z-Truyen X3</dc:rights>
</metadata>'''.encode("utf-8")
    )

    # Create guide item for navigation
    guide_item = epub.EpubItem(
        uid="guide",
        file_name="guide.xml",
        media_type="application/xml",
        content=f'''<?xml version="1.0" encoding="utf-8"?>
<guide>
    <reference type="toc" title="{_escape_xml(chapter_title)}" href="chapter.xhtml"/>
</guide>'''.encode("utf-8")
    )

    # Create NCX navigation control file
    ncx_item = epub.EpubNcx()

    return metadata_item, guide_item, ncx_item


def build_epub(
    chapter: ChapterContent,
    book_title: str,
    author: str,
    cover_url: Optional[str] = None
) -> bytes:
    """Build EPUB bytes from chapter content.

    Args:
        chapter: ChapterContent with the chapter data.
        book_title: Title of the book.
        author: Author name.
        cover_url: Optional URL for cover image.

    Returns:
        EPUB file as bytes for direct serving.
    """
    # Create EPUB book
    book = epub.EpubBook()

    # Set unique identifier based on chapter ID
    # Parse chapter.id: format is "{source_id}:{book_id}:{chapter_slug}"
    chapter_id_parts = chapter.id.split(":")
    source_id = chapter_id_parts[0] if len(chapter_id_parts) >= 1 else "unknown"
    story_slug = chapter_id_parts[1] if len(chapter_id_parts) >= 2 else "unknown"
    chap_slug = chapter_id_parts[2] if len(chapter_id_parts) >= 3 else "unknown"

    identifier = f"ztruyen-{source_id}-{story_slug}-{chap_slug}"
    book.set_identifier(identifier)
    book.set_title(f"{book_title} - {chapter.title}")
    book.set_language("vi")
    book.add_author(author or "Đang cập nhật")

    # Add CSS stylesheet
    style_item = epub.EpubItem(
        uid="style_css",
        file_name="style.css",
        media_type="text/css",
        content=EPUB_CSS.encode("utf-8")
    )
    book.add_item(style_item)

    # Add cover image if provided
    if cover_url:
        add_cover_image(book, cover_url)

    # Convert chapter content to XHTML (use 'content' field from sources.base.ChapterContent)
    xhtml_content = convert_to_xhtml(chapter.content, chapter.title)

    # Create chapter HTML
    chapter_html = epub.EpubHtml(
        title=chapter.title,
        file_name="text/chapter.xhtml",
        lang="vi",
        content=xhtml_content.encode("utf-8")
    )
    chapter_html.add_item(style_item)
    book.add_item(chapter_html)

    # Create navigation document (EPUB 3 nav)
    nav_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="vi" lang="vi">
<head>
    <meta charset="utf-8" />
    <title>Navigation</title>
</head>
<body>
    <nav epub:type="toc">
        <h1>Mục lục</h1>
        <ol>
            <li><a href="text/chapter.xhtml">{_escape_xml(chapter.title)}</a></li>
        </ol>
    </nav>
</body>
</html>'''

    nav_item = epub.EpubNav(
        uid="nav",
        file_name="nav.xhtml",
    )
    nav_item.content = nav_html
    nav_item.add_item(style_item)
    book.add_item(nav_item)

    # Set table of contents
    book.toc = (
        epub.Link("text/chapter.xhtml", chapter.title, "chapter"),
    )

    # Add NCX for EPUB 2 compatibility
    book.add_item(epub.EpubNcx())

    # Define spine (reading order)
    book.spine = ["nav", chapter_html]

    # Write EPUB to in-memory buffer
    buffer = io.BytesIO()
    epub.write_epub(buffer, book, {})

    return buffer.getvalue()


# Synchronous version for when async is not needed
def build_epub_sync(
    chapter: ChapterContent,
    book_title: str,
    author: str,
    cover_url: Optional[str] = None
) -> bytes:
    """Synchronous version of build_epub for use in non-async contexts.

    Args:
        chapter: ChapterContent with the chapter data.
        book_title: Title of the book.
        author: Author name.
        cover_url: Optional URL for cover image.

    Returns:
        EPUB file as bytes for direct serving.
    """
    # Create EPUB book
    book = epub.EpubBook()

    # Set unique identifier based on chapter ID
    # Parse chapter.id: format is "{source_id}:{book_id}:{chapter_slug}"
    chapter_id_parts = chapter.id.split(":")
    source_id = chapter_id_parts[0] if len(chapter_id_parts) >= 1 else "unknown"
    story_slug = chapter_id_parts[1] if len(chapter_id_parts) >= 2 else "unknown"
    chap_slug = chapter_id_parts[2] if len(chapter_id_parts) >= 3 else "unknown"

    identifier = f"ztruyen-{source_id}-{story_slug}-{chap_slug}"
    book.set_identifier(identifier)
    book.set_title(f"{book_title} - {chapter.title}")
    book.set_language("vi")
    book.add_author(author or "Đang cập nhật")

    # Add CSS stylesheet
    style_item = epub.EpubItem(
        uid="style_css",
        file_name="style.css",
        media_type="text/css",
        content=EPUB_CSS.encode("utf-8")
    )
    book.add_item(style_item)

    # Add cover image synchronously if provided
    if cover_url:
        try:
            import httpx
            response = httpx.get(cover_url, timeout=15.0)
            response.raise_for_status()
            image_bytes = response.content

            # Resize if needed
            from PIL import Image
            img = Image.open(io.BytesIO(image_bytes))

            if img.width > MAX_COVER_WIDTH or img.height > MAX_COVER_HEIGHT:
                ratio = min(MAX_COVER_WIDTH / img.width, MAX_COVER_HEIGHT / img.height)
                new_width = int(img.width * ratio)
                new_height = int(img.height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            book.set_cover("cover.jpg", output.getvalue())
        except Exception:
            pass  # Silently fail - cover is optional

    # Convert chapter content to XHTML (use 'content' field from sources.base.ChapterContent)
    xhtml_content = convert_to_xhtml(chapter.content, chapter.title)

    # Create chapter HTML
    chapter_html = epub.EpubHtml(
        title=chapter.title,
        file_name="text/chapter.xhtml",
        lang="vi",
        content=xhtml_content.encode("utf-8")
    )
    chapter_html.add_item(style_item)
    book.add_item(chapter_html)

    # Create navigation document (EPUB 3 nav)
    nav_html = f'''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="vi" lang="vi">
<head>
    <meta charset="utf-8" />
    <title>Navigation</title>
</head>
<body>
    <nav epub:type="toc">
        <h1>Mục lục</h1>
        <ol>
            <li><a href="text/chapter.xhtml">{_escape_xml(chapter.title)}</a></li>
        </ol>
    </nav>
</body>
</html>'''

    nav_item = epub.EpubNav(
        uid="nav",
        file_name="nav.xhtml",
    )
    nav_item.content = nav_html
    nav_item.add_item(style_item)
    book.add_item(nav_item)

    # Set table of contents
    book.toc = (
        epub.Link("text/chapter.xhtml", chapter.title, "chapter"),
    )

    # Add NCX for EPUB 2 compatibility
    book.add_item(epub.EpubNcx())

    # Define spine (reading order)
    book.spine = ["nav", chapter_html]

    # Write EPUB to in-memory buffer
    buffer = io.BytesIO()
    epub.write_epub(buffer, book, {})

    return buffer.getvalue()
