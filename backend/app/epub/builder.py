"""Deterministic EPUB package builder generating valid, lightweight EPUB files with SHA-1 hashing."""

import io
import html
from typing import Any, Sequence
import ebooklib
from ebooklib import epub
from app.epub.template import EPUB_CSS, XHTML_CHAPTER_TEMPLATE, XHTML_TITLE_PAGE_TEMPLATE
from app.cache.object_storage import storage
from app.domain.models import Chapter


class EpubBuilder:
    """Constructs deterministic EPUB 2/3 books optimized for E-ink devices and KOSync."""

    @staticmethod
    def build(
        identifier: str,
        title: str,
        author: str,
        source_name: str,
        volume_title: str,
        chapters: Sequence[Chapter],
        cover_image_bytes: bytes | None = None,
    ) -> tuple[bytes, str]:
        """
        Build EPUB binary in memory and return (epub_bytes, sha1_hex_hash).
        """
        book = epub.EpubBook()
        book.set_identifier(identifier)
        book.set_title(f"{title} - {volume_title}")
        book.set_language("vi")
        book.add_author(author or "Đang cập nhật")

        # 1. Add CSS Stylesheet
        style_item = epub.EpubItem(
            uid="style_css",
            file_name="style.css",
            media_type="text/css",
            content=EPUB_CSS.encode("utf-8"),
        )
        book.add_item(style_item)

        # 2. Add Cover Image if provided
        if cover_image_bytes:
            book.set_cover("cover.jpg", cover_image_bytes)

        # 3. Add Title Page
        title_page_html = XHTML_TITLE_PAGE_TEMPLATE.format(
            title=html.escape(title),
            author=html.escape(author or "Đang cập nhật"),
            volume_title=html.escape(volume_title),
            source_name=html.escape(source_name),
        )
        title_page = epub.EpubHtml(
            title="Trang bìa",
            file_name="title_page.xhtml",
            lang="vi",
            content=title_page_html.encode("utf-8"),
        )
        title_page.add_item(style_item)
        book.add_item(title_page)

        # 4. Add Chapters
        spine_items: list[Any] = ["nav", title_page]
        toc_items: list[Any] = [epub.Link("title_page.xhtml", "Trang bìa", "title_page")]

        for idx, chap in enumerate(chapters, start=1):
            chap_filename = f"chapter_{chap.order_num:04d}.xhtml"
            chap_html = XHTML_CHAPTER_TEMPLATE.format(
                title=html.escape(chap.title),
                content=chap.content_clean,
            )
            epub_chap = epub.EpubHtml(
                title=chap.title,
                file_name=chap_filename,
                lang="vi",
                content=chap_html.encode("utf-8"),
            )
            epub_chap.add_item(style_item)
            book.add_item(epub_chap)
            spine_items.append(epub_chap)
            toc_items.append(epub.Link(chap_filename, chap.title, f"chap_{idx}"))

        # 5. Define Table of Contents & Navigation
        book.toc = tuple(toc_items)
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        book.spine = spine_items

        # 6. Write to in-memory byte buffer
        buffer = io.BytesIO()
        epub.write_epub(buffer, book, {})
        epub_data = buffer.getvalue()

        # 7. Calculate SHA-1 checksum
        sha1_hash = storage.calculate_sha1(epub_data)

        return epub_data, sha1_hash


epub_builder = EpubBuilder()
