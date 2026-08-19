"""Document ID generation, slug sanitization, and KOSync deterministic filename helpers."""

import re
import unicodedata


def slugify(text: str) -> str:
    """Normalize text into an ASCII alphanumeric slug with hyphens."""
    if not text:
        return ""
    # Explicitly map Vietnamese Đ/đ
    text = text.replace("Đ", "d").replace("đ", "d")
    # Normalize Vietnamese accented characters
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def build_story_id(source_id: str, story_slug: str) -> str:
    """Construct composite story ID."""
    return f"{source_id}:{story_slug}"


def build_chapter_id(source_id: str, story_slug: str, chap_slug: str) -> str:
    """Construct composite chapter ID."""
    return f"{source_id}:{story_slug}:{chap_slug}"


def build_volume_id(source_id: str, story_slug: str, vol_index: int) -> str:
    """Construct composite volume bundle ID."""
    return f"{source_id}:{story_slug}:v{vol_index:02d}"


def build_volume_filename(source_id: str, story_slug: str, vol_index: int) -> str:
    """Construct deterministic Volume EPUB filename for KOSync."""
    safe_story = slugify(story_slug) or story_slug
    return f"ztruyen_{source_id}_{safe_story}_v{vol_index:02d}.epub"


def build_chapter_filename(source_id: str, story_slug: str, chap_order: int) -> str:
    """Construct deterministic Single Chapter EPUB filename."""
    safe_story = slugify(story_slug) or story_slug
    return f"ztruyen_{source_id}_{safe_story}_c{chap_order:04d}.epub"
