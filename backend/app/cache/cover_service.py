"""Cover optimization and caching service for E-ink displays (JPEG 16-level grayscale compatible)."""

import io
from pathlib import Path
from PIL import Image, ImageEnhance, ImageDraw, ImageFont
from app.fetcher.client import http_client, HttpClient
from app.cache.object_storage import storage, ObjectStorage
from app.logging import logger


class CoverService:
    """Fetches, converts (WebP -> JPEG), resizes and enhances covers for Xteink X3 E-ink."""

    TARGET_SIZE = (240, 360)

    def __init__(self, obj_storage: ObjectStorage | None = None, client: HttpClient | None = None) -> None:
        self.storage = obj_storage or storage
        self.client = client or http_client

    def _get_cover_path(self, source_id: str, slug: str) -> Path:
        self.storage.cover_dir.mkdir(parents=True, exist_ok=True)
        return self.storage.cover_dir / f"{source_id}_{slug}.jpg"

    def get_cached_cover_path(self, source_id: str, slug: str) -> Path | None:
        p = self._get_cover_path(source_id, slug)
        if p.is_file() and p.stat().st_size > 0:
            return p
        return None

    def _process_image_bytes(self, raw_bytes: bytes) -> bytes:
        """Convert any image (WebP, PNG, GIF) to E-ink optimized JPEG."""
        with Image.open(io.BytesIO(raw_bytes)) as img:
            # Convert to RGB (handling transparency)
            if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
                bg = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                bg.paste(img, mask=img.split()[-1])
                img = bg
            elif img.mode != "RGB":
                img = img.convert("RGB")

            # Resize maintaining aspect ratio
            img.thumbnail(self.TARGET_SIZE, Image.Resampling.LANCZOS)

            # Slight contrast enhancement for crisp E-ink reading
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.15)

            out_buf = io.BytesIO()
            img.save(out_buf, format="JPEG", quality=85, optimize=True)
            return out_buf.getvalue()

    def generate_placeholder_cover(self, title: str, source_name: str) -> bytes:
        """Generate a clean procedural placeholder cover for stories without covers."""
        width, height = self.TARGET_SIZE
        img = Image.new("RGB", (width, height), (240, 240, 240))
        draw = ImageDraw.Draw(img)

        # Border
        draw.rectangle([(4, 4), (width - 5, height - 5)], outline=(80, 80, 80), width=2)
        draw.rectangle([(8, 8), (width - 9, height - 9)], outline=(180, 180, 180), width=1)

        # Title text
        words = title.split()
        lines = []
        cur_line = []
        for w in words:
            cur_line.append(w)
            if len(" ".join(cur_line)) > 14:
                lines.append(" ".join(cur_line))
                cur_line = []
        if cur_line:
            lines.append(" ".join(cur_line))

        y = 50
        for line in lines[:5]:
            draw.text((20, y), line, fill=(20, 20, 20))
            y += 24

        # Source badge at bottom
        draw.rectangle([(16, height - 48), (width - 16, height - 20)], fill=(50, 50, 50))
        draw.text((26, height - 40), f"Z-Truyen • {source_name}", fill=(255, 255, 255))

        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=80)
        return out_buf.getvalue()

    async def get_or_create_cover(
        self,
        source_id: str,
        slug: str,
        cover_url: str | None = None,
        title: str = "",
    ) -> Path:
        """Retrieve cached cover or fetch, convert, and cache it."""
        cached = self.get_cached_cover_path(source_id, slug)
        if cached:
            return cached

        target_path = self._get_cover_path(source_id, slug)

        if cover_url:
            try:
                resp = await self.client.get(cover_url, timeout=5.0)
                if resp.status_code == 200 and len(resp.content) > 100:
                    jpeg_bytes = self._process_image_bytes(resp.content)
                    target_path.write_bytes(jpeg_bytes)
                    logger.info(f"[CoverService] Converted and cached cover for {source_id}:{slug}")
                    return target_path
            except Exception as e:
                logger.warning(f"[CoverService] Failed to fetch remote cover ({cover_url}): {e}")

        # Fallback to generated placeholder
        placeholder_bytes = self.generate_placeholder_cover(title or slug, source_id.upper())
        target_path.write_bytes(placeholder_bytes)
        return target_path


cover_service = CoverService()
