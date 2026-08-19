"""Object storage management for local disk caching of EPUB files and story covers."""

import hashlib
from pathlib import Path
from app.config import settings
from app.logging import log_epub_event


class ObjectStorage:
    """Manages file storage and lookup for generated EPUB packages and images."""

    def __init__(self, epub_dir: Path | None = None, cover_dir: Path | None = None) -> None:
        self.epub_dir = epub_dir or settings.epub_cache_dir
        self.cover_dir = cover_dir or settings.cover_cache_dir
        self.ensure_directories()

    def ensure_directories(self) -> None:
        """Ensure storage directories exist."""
        self.epub_dir.mkdir(parents=True, exist_ok=True)
        self.cover_dir.mkdir(parents=True, exist_ok=True)

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

    def _safe_epub_path(self, filename: str) -> Path:
        """Resolve and validate that the target EPUB file path remains inside epub_dir."""
        clean_name = Path(filename).name
        target = (self.epub_dir / clean_name).resolve()
        if not target.is_relative_to(self.epub_dir.resolve()):
            raise ValueError(f"Path traversal detected in filename: {filename}")
        return target

    def save_epub(self, filename: str, data: bytes) -> Path:
        """Persist EPUB byte content to disk cache."""
        self.ensure_directories()
        target_path = self._safe_epub_path(filename)
        target_path.write_bytes(data)
        log_epub_event(filename, f"Saved EPUB to cache ({len(data)} bytes)")
        return target_path

    def get_epub_path(self, filename: str) -> Path | None:
        """Get file path of cached EPUB if it exists."""
        target_path = self._safe_epub_path(filename)
        if target_path.is_file() and target_path.stat().st_size > 0:
            return target_path
        return None

    def get_epub(self, filename: str) -> bytes | None:
        """Retrieve EPUB content from disk cache."""
        path = self.get_epub_path(filename)
        if path:
            return path.read_bytes()
        return None

    def has_epub(self, filename: str) -> bool:
        """Check if an EPUB is present in disk cache."""
        path = self.epub_dir / filename
        return path.is_file() and path.stat().st_size > 0

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
