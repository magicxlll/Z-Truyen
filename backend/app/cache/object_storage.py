"""Object storage management for local disk caching of EPUB files and story covers organized by story."""

import hashlib
import re
from pathlib import Path
from app.config import settings
from app.logging import log_epub_event


class ObjectStorage:
    """Manages file storage and lookup for generated EPUB packages and images."""

    def __init__(
        self,
        epub_dir: Path | None = None,
        cover_dir: Path | None = None,
        downloads_dir: Path | None = None,
    ) -> None:
        self.epub_dir = epub_dir or settings.epub_cache_dir
        self.cover_dir = cover_dir or settings.cover_cache_dir
        self.downloads_dir = downloads_dir or (Path.cwd() / "downloads")
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure storage directories exist."""
        self.epub_dir.mkdir(parents=True, exist_ok=True)
        self.cover_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def calculate_sha1(data: bytes) -> str:
        """Calculate hexadecimal SHA-1 checksum of byte content."""
        hasher = hashlib.sha1()
        hasher.update(data)
        return hasher.hexdigest()

    @staticmethod
    def calculate_file_sha1(file_path: Path) -> str:
        """Calculate hexadecimal SHA-1 checksum of a file on disk."""
        hasher = hashlib.sha1()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _extract_slug_from_filename(self, filename: str) -> str | None:
        """Extract story slug from artifact name pattern like ztruyen_source_slug_v01.epub."""
        m = re.match(r"^ztruyen_[^_]+_([^_]+(?:_[^_]+)*?)_(?:v\d+|c\d+|range_\d+_\d+|all)\.epub$", filename, re.IGNORECASE)
        if m:
            return m.group(1)
        return None

    def _safe_epub_path(self, filename: str, story_slug: str | None = None) -> Path:
        """Resolve and validate target EPUB file path inside story subfolder or epub_dir."""
        clean_name = Path(filename).name
        slug = story_slug or self._extract_slug_from_filename(clean_name)
        if slug:
            folder = (self.epub_dir / slug).resolve()
            folder.mkdir(parents=True, exist_ok=True)
            target = (folder / clean_name).resolve()
        else:
            target = (self.epub_dir / clean_name).resolve()

        if not target.is_relative_to(self.epub_dir.resolve()):
            raise ValueError(f"Path traversal detected in filename: {filename}")
        return target

    def save_epub(self, filename: str, data: bytes, story_slug: str | None = None) -> Path:
        """Persist EPUB byte content to disk cache and organized downloads folder."""
        self.ensure_directories()
        target_path = self._safe_epub_path(filename, story_slug=story_slug)
        target_path.write_bytes(data)

        # Also copy to downloads/{slug}/ for convenient user access
        slug = story_slug or self._extract_slug_from_filename(filename) or "general"
        try:
            dl_folder = self.downloads_dir / slug
            dl_folder.mkdir(parents=True, exist_ok=True)
            (dl_folder / Path(filename).name).write_bytes(data)
        except Exception:
            pass

        log_epub_event(filename, f"Saved EPUB to cache ({len(data)} bytes in {slug}/)")
        return target_path

    def get_epub_path(self, filename: str, story_slug: str | None = None) -> Path | None:
        """Get file path of cached EPUB if it exists (checks story subfolder then root)."""
        clean_name = Path(filename).name
        slug = story_slug or self._extract_slug_from_filename(clean_name)

        if slug:
            sub_path = self.epub_dir / slug / clean_name
            if sub_path.is_file() and sub_path.stat().st_size > 0:
                return sub_path

        root_path = self.epub_dir / clean_name
        if root_path.is_file() and root_path.stat().st_size > 0:
            return root_path

        return None

    def get_epub(self, filename: str, story_slug: str | None = None) -> bytes | None:
        """Retrieve EPUB content from disk cache."""
        path = self.get_epub_path(filename, story_slug=story_slug)
        if path:
            return path.read_bytes()
        return None

    def has_epub(self, filename: str, story_slug: str | None = None) -> bool:
        """Check if an EPUB is present in disk cache."""
        return self.get_epub_path(filename, story_slug=story_slug) is not None

    def save_cover(self, source_id: str, slug: str, image_bytes: bytes, ext: str = "jpg") -> Path:
        """Save story cover image to disk cache."""
        self.ensure_directories()
        filename = f"{source_id}_{slug}.{ext}"
        target_path = self.cover_dir / filename
        target_path.write_bytes(image_bytes)
        return target_path

    def get_cover_path(self, source_id: str, slug: str) -> Path | None:
        """Find cached cover for a story with common image extensions."""
        for ext in ("jpg", "jpeg", "png", "webp"):
            filename = f"{source_id}_{slug}.{ext}"
            path = self.cover_dir / filename
            if path.is_file() and path.stat().st_size > 0:
                return path
        return None


storage = ObjectStorage()
