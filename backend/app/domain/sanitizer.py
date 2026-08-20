"""Vietnamese text and HTML normalizer and sanitizer for XHTML EPUB compatibility."""

import html
import re
import unicodedata
from selectolax.parser import HTMLParser


# Common noise phrases in scraped Vietnamese web chapters
JUNK_PATTERNS = [
    re.compile(r"nguồn\s*:\s*[^\n<]+", re.IGNORECASE),
    re.compile(r"đăng\s*bởi\s*:\s*[^\n<]+", re.IGNORECASE),
    re.compile(r"chúc\s*bạn\s*đọc\s*truyện\s*vui\s*vẻ", re.IGNORECASE),
    re.compile(r"đọc\s*truyện\s*tại\s*[^\n<]+", re.IGNORECASE),
    re.compile(r"ủng\s*hộ\s*dịch\s*giả[^\n<]*", re.IGNORECASE),
    re.compile(r"mọi\s*người\s*nhớ\s*like\s*và\s*share[^\n<]*", re.IGNORECASE),
    re.compile(r"theo\s*dõi\s*fanpage[^\n<]*", re.IGNORECASE),
    re.compile(r"^[-=*_~]{3,}$"),  # Divider lines
]


def clean_vietnamese_text(text: str) -> str:
    """Normalize Unicode to NFC form and strip excess whitespaces."""
    if not text:
        return ""
    # NFC is the standard normalized form for Vietnamese
    text = unicodedata.normalize("NFC", text)
    # Replace non-breaking spaces and irregular whitespace
    text = text.replace("\xa0", " ").replace("\u200b", "").replace("\ufeff", "")
    return text.strip()


def remove_accents(input_str: str) -> str:
    """Remove Vietnamese tone marks and accents, converting to lowercase unaccented text."""
    if not input_str:
        return ""
    # Replace special Vietnamese chars like đ, Đ
    s = input_str.replace("đ", "d").replace("Đ", "D")
    nfkd_form = unicodedata.normalize("NFKD", s)
    return "".join(c for c in nfkd_form if not unicodedata.combining(c)).lower().strip()


def is_junk_paragraph(text: str) -> bool:
    """Check if a paragraph is unwanted noise or advertisement."""
    cleaned = text.strip()
    if not cleaned or len(cleaned) < 2:
        return True
    for pattern in JUNK_PATTERNS:
        if pattern.search(cleaned):
            # If the paragraph is very short and matches noise pattern, discard
            if len(cleaned) < 120:
                return True
    return False


def sanitize_chapter_html(raw_html: str) -> str:
    """
    Parse raw HTML from scrapers, remove unwanted elements,
    extract textual paragraphs, clean Vietnamese characters,
    and output deterministic well-formed XHTML with `<p id="p-N">` tags.
    """
    if not raw_html or not raw_html.strip():
        return "<p id=\"p-1\">[Không có nội dung]</p>"

    # Pre-clean known line-break markers before parsing
    prepped_html = re.sub(r"(?i)<br\s*/?>", "\n", raw_html)
    prepped_html = re.sub(r"(?i)</p>", "\n</p>", prepped_html)

    tree = HTMLParser(prepped_html)

    # Remove script, style, iframe, audio, video, img, select, options, navigation tags
    for tag in tree.css("script, style, iframe, audio, video, img, noscript, svg, button, form, select, option, nav, aside, .chapter-filter-container, .post-tts-player-wrap, .searchform-wrapper, .chapter-nav, .nav-previous, .nav-next"):
        tag.decompose()

    # Extract text content while preserving newlines
    raw_text = tree.text(separator="\n")
    lines = raw_text.splitlines()

    clean_paragraphs: list[str] = []
    for line in lines:
        cleaned_line = clean_vietnamese_text(line)
        if cleaned_line and not is_junk_paragraph(cleaned_line):
            clean_paragraphs.append(cleaned_line)

    if not clean_paragraphs:
        return "<p id=\"p-1\">[Nội dung đang được cập nhật]</p>"

    # Build deterministic XHTML paragraphs
    xhtml_parts: list[str] = []
    for idx, para in enumerate(clean_paragraphs, start=1):
        escaped_para = html.escape(para, quote=True)
        xhtml_parts.append(f'<p id="p-{idx}">{escaped_para}</p>')

    return "\n".join(xhtml_parts)
