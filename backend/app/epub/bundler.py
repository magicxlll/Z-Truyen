"""Dynamic Volume Bundling engine for segmenting stories into 50-chapter EPUBs."""

import asyncio
from pathlib import Path
from typing import Sequence
from app.config import settings
from app.domain.models import Story, Chapter, VolumeBundle
from app.domain.ids import (
    build_story_id,
    build_chapter_id,
    build_volume_id,
    build_volume_filename,
    build_chapter_filename,
)
from app.cache.metadata_repo import repo, MetadataRepository
from app.cache.object_storage import storage, ObjectStorage
from app.sources.registry import registry, SourceRegistry
from app.epub.builder import epub_builder, EpubBuilder
from app.logging import logger, log_epub_event


class VolumeBundler:
    """Orchestrates chapter scraping, volume segmentation, and EPUB caching."""

    def __init__(
        self,
        metadata_repo: MetadataRepository | None = None,
        object_storage: ObjectStorage | None = None,
        source_registry: SourceRegistry | None = None,
        builder: EpubBuilder | None = None,
        chapters_per_volume: int = settings.CHAPTERS_PER_VOLUME,
    ) -> None:
        self.repo = metadata_repo or repo
        self.storage = object_storage or storage
        self.registry = source_registry or registry
        self.builder = builder or epub_builder
        self.chapters_per_volume = chapters_per_volume

        self._build_locks: dict[str, asyncio.Lock] = {}

    def _get_lock(self, key: str) -> asyncio.Lock:
        """Get or create concurrency lock for a specific volume compilation."""
        if key not in self._build_locks:
            self._build_locks[key] = asyncio.Lock()
        return self._build_locks[key]

    def calculate_volume_slices(self, total_chapters: int) -> list[dict[str, int]]:
        """Calculate start and end chapter orders for all volumes of a story."""
        if total_chapters <= 0:
            return [{"vol_index": 1, "start_order": 1, "end_order": 1, "count": 1}]

        slices: list[dict[str, int]] = []
        vol_index = 1
        start = 1
        while start <= total_chapters:
            end = min(start + self.chapters_per_volume - 1, total_chapters)
            slices.append(
                {
                    "vol_index": vol_index,
                    "start_order": start,
                    "end_order": end,
                    "count": end - start + 1,
                }
            )
            start = end + 1
            vol_index += 1
        return slices

    async def get_or_build_volume(
        self, source_id: str, story_slug: str, vol_index: int
    ) -> tuple[Path, str]:
        """
        Retrieve cached Volume EPUB or scrape necessary chapters and build it.
        Returns (file_path, sha1_hash).
        """
        lock_key = f"{source_id}:{story_slug}:{vol_index}"
        async with self._get_lock(lock_key):
            filename = build_volume_filename(source_id, story_slug, vol_index)
            cached_path = self.storage.get_epub_path(filename)
            cached_bundle = self.repo.get_volume_bundle(source_id, story_slug, vol_index)

            if cached_path and cached_bundle:
                logger.info(f"Serving cached volume EPUB: {filename}")
                return cached_path, cached_bundle.sha1_hash

            logger.info(f"Building volume EPUB {filename} (source={source_id}, slug={story_slug}, vol={vol_index})")
            adapter = self.registry.get(source_id)
            if not adapter:
                raise ValueError(f"Unknown source adapter '{source_id}'")

            # 1. Fetch Story Metadata
            story = await adapter.get_story_detail(story_slug)
            self.repo.upsert_story(story)

            # 2. Fetch All Chapters
            all_chapters_summary = await adapter.get_all_chapters(story_slug)
            total_chapters = len(all_chapters_summary)
            if story.total_chapters != total_chapters:
                story.total_chapters = total_chapters
                self.repo.upsert_story(story)

            start_order = (vol_index - 1) * self.chapters_per_volume + 1
            end_order = min(vol_index * self.chapters_per_volume, total_chapters)

            if start_order > total_chapters:
                raise ValueError(
                    f"Volume {vol_index} is out of range for story with {total_chapters} chapters"
                )

            # Target chapter summaries in slice
            target_summaries = [
                c for c in all_chapters_summary if start_order <= c.order <= end_order
            ]
            if not target_summaries:
                target_summaries = all_chapters_summary[start_order - 1 : end_order]

            # 3. Concurrently fetch/scrape missing chapters in volume
            sem = asyncio.Semaphore(settings.FAST_SCRAPE_CONCURRENCY)

            async def fetch_single_chap(chap_summary) -> Chapter:
                cached_chap = self.repo.get_chapter(source_id, story_slug, chap_summary.slug)
                if cached_chap and cached_chap.content_clean:
                    return cached_chap

                async with sem:
                    logger.info(f"Scraping chapter: {chap_summary.title} ({chap_summary.slug})")
                    chap_content = await adapter.get_chapter_content(story_slug, chap_summary.slug)
                    domain_chap = Chapter(
                        id=build_chapter_id(source_id, story_slug, chap_summary.slug),
                        story_id=build_story_id(source_id, story_slug),
                        order_num=chap_summary.order,
                        title=chap_summary.title,
                        original_url=chap_content.original_url,
                        content_clean=chap_content.content_html,
                        is_vip=chap_summary.is_vip,
                    )
                    self.repo.upsert_chapter(domain_chap)
                    return domain_chap

            chapters_to_compile = await asyncio.gather(
                *(fetch_single_chap(c) for c in target_summaries)
            )
            chapters_to_compile = sorted(chapters_to_compile, key=lambda c: c.order_num)

        # 4. Fetch cover bytes if available
        cover_bytes: bytes | None = None
        if story.cover_url:
            try:
                cover_resp = await adapter.client.get(story.cover_url)
                if cover_resp.status_code == 200:
                    cover_bytes = cover_resp.content
            except Exception as e:
                logger.warning(f"Could not download cover image from {story.cover_url}: {e}")

        # 5. Build EPUB
        volume_title = f"Tập {vol_index:02d} (Chương {start_order}-{end_order})"
        identifier = f"urn:ztruyen:{source_id}:{story_slug}:v{vol_index:02d}"

        epub_bytes, sha1_hash = self.builder.build(
            identifier=identifier,
            title=story.title,
            author=story.author,
            source_name=adapter.name,
            volume_title=volume_title,
            chapters=chapters_to_compile,
            cover_image_bytes=cover_bytes,
        )

        # 6. Save to disk cache and database
        saved_file_path = self.storage.save_epub(filename, epub_bytes)
        bundle = VolumeBundle(
            id=build_volume_id(source_id, story_slug, vol_index),
            story_id=build_story_id(source_id, story_slug),
            vol_index=vol_index,
            start_order=start_order,
            end_order=end_order,
            chapter_count=len(chapters_to_compile),
            filename=filename,
            sha1_hash=sha1_hash,
            file_size_bytes=len(epub_bytes),
        )
        self.repo.upsert_volume_bundle(bundle)

        return saved_file_path, sha1_hash

    async def get_or_build_single_chapter(
        self, source_id: str, story_slug: str, chap_order: int
    ) -> tuple[Path, str]:
        """Build and cache a single-chapter EPUB for immediate reading."""
        filename = build_chapter_filename(source_id, story_slug, chap_order)
        cached_path = self.storage.get_epub_path(filename)
        if cached_path:
            sha1 = self.storage.calculate_file_sha1(cached_path)
            return cached_path, sha1

        adapter = self.registry.get(source_id)
        if not adapter:
            raise ValueError(f"Unknown source adapter '{source_id}'")

        story = await adapter.get_story_detail(story_slug)
        all_chapters = await adapter.get_all_chapters(story_slug)
        target_chap_summary = next(
            (c for c in all_chapters if c.order == chap_order),
            all_chapters[chap_order - 1] if 0 < chap_order <= len(all_chapters) else None,
        )
        if not target_chap_summary:
            raise ValueError(f"Chapter {chap_order} not found in story '{story_slug}'")

        chap_content = await adapter.get_chapter_content(story_slug, target_chap_summary.slug)
        domain_chap = Chapter(
            id=build_chapter_id(source_id, story_slug, target_chap_summary.slug),
            story_id=build_story_id(source_id, story_slug),
            order_num=target_chap_summary.order,
            title=target_chap_summary.title,
            original_url=chap_content.original_url,
            content_clean=chap_content.content_html,
            is_vip=target_chap_summary.is_vip,
        )
        self.repo.upsert_chapter(domain_chap)

        identifier = f"urn:ztruyen:{source_id}:{story_slug}:c{chap_order:04d}"
        epub_bytes, sha1_hash = self.builder.build(
            identifier=identifier,
            title=story.title,
            author=story.author,
            source_name=adapter.name,
            volume_title=f"Chương {chap_order}",
            chapters=[domain_chap],
        )

        saved_path = self.storage.save_epub(filename, epub_bytes)
        return saved_path, sha1_hash

    async def prefetch_and_cleanup(
        self,
        source_id: str,
        story_slug: str,
        current_chap_order: int,
        prefetch_count: int = 3,
        cleanup_behind: int = 5,
    ) -> None:
        """
        Background worker:
        1. Prefetch next N chapters (build EPUBs in background for near-online instant reading).
        2. Clean up single-chapter EPUBs older than 5 chapters behind to save disk space.
        """
        logger.info(
            f"[PrefetchEngine] Starting background prefetch for {source_id}:{story_slug} from chapter {current_chap_order}"
        )
        # 1. Prefetch next chapters
        for next_order in range(current_chap_order + 1, current_chap_order + 1 + prefetch_count):
            try:
                next_filename = build_chapter_filename(source_id, story_slug, next_order)
                if not self.storage.has_epub(next_filename):
                    logger.info(f"[PrefetchEngine] Background caching next chapter {next_order}...")
                    await self.get_or_build_single_chapter(source_id, story_slug, next_order)
            except Exception as e:
                logger.debug(f"[PrefetchEngine] Reached end of chapters or prefetch stopped at {next_order}: {e}")
                break

        # 2. Smart auto-cleanup for chapters older than cleanup_behind
        if current_chap_order > cleanup_behind:
            clean_until = current_chap_order - cleanup_behind
            for old_order in range(1, clean_until + 1):
                old_filename = build_chapter_filename(source_id, story_slug, old_order)
                old_path = self.storage.epub_dir / old_filename
                if old_path.is_file():
                    try:
                        old_path.unlink()
                        logger.info(f"[SmartCache] Auto-cleaned old cached chapter: {old_filename}")
                    except Exception as e:
                        logger.debug(f"[SmartCache] Failed to delete {old_filename}: {e}")

    async def get_or_build_custom_range(
        self,
        source_id: str,
        story_slug: str,
        start_order: int,
        end_order: int,
    ) -> tuple[Path, str]:
        """Build and cache a custom range of chapters (e.g., 1-32 or all) into a single EPUB file."""
        if start_order < 1:
            start_order = 1
        if end_order < start_order:
            end_order = start_order

        is_all = (start_order == 1 and end_order >= 99999)
        if is_all:
            filename = f"ztruyen_{source_id}_{story_slug}_all.epub"
        else:
            filename = f"ztruyen_{source_id}_{story_slug}_c{start_order:04d}-{end_order:04d}.epub"

        cached_path = self.storage.get_epub_path(filename)
        if cached_path:
            sha1 = self.storage.calculate_file_sha1(cached_path)
            return cached_path, sha1

        lock_key = f"{source_id}:{story_slug}:{filename}"
        async with self._get_lock(lock_key):
            cached_path = self.storage.get_epub_path(filename)
            if cached_path:
                sha1 = self.storage.calculate_file_sha1(cached_path)
                return cached_path, sha1

            adapter = self.registry.get(source_id)
            if not adapter:
                raise ValueError(f"Unknown source adapter '{source_id}'")

            story = await adapter.get_story_detail(story_slug)
            all_chapters_summary = await adapter.get_all_chapters(story_slug)
            total_chapters = len(all_chapters_summary)
            if total_chapters == 0:
                raise ValueError(f"No chapters found for story '{story_slug}'")

            actual_end_order = min(end_order, total_chapters)
            actual_start_order = min(start_order, actual_end_order)

            target_summaries = [
                c for c in all_chapters_summary if actual_start_order <= c.order <= actual_end_order
            ]
            if not target_summaries:
                target_summaries = all_chapters_summary[actual_start_order - 1 : actual_end_order]

            sem = asyncio.Semaphore(settings.FAST_SCRAPE_CONCURRENCY)

            async def fetch_single_chap(chap_summary) -> Chapter:
                cached_chap = self.repo.get_chapter(source_id, story_slug, chap_summary.slug)
                if cached_chap and cached_chap.content_clean:
                    return cached_chap

                async with sem:
                    chap_content = await adapter.get_chapter_content(story_slug, chap_summary.slug)
                    domain_chap = Chapter(
                        id=build_chapter_id(source_id, story_slug, chap_summary.slug),
                        story_id=build_story_id(source_id, story_slug),
                        order_num=chap_summary.order,
                        title=chap_summary.title,
                        original_url=chap_content.original_url,
                        content_clean=chap_content.content_html,
                        is_vip=chap_summary.is_vip,
                    )
                    self.repo.upsert_chapter(domain_chap)
                    return domain_chap

            chapters_to_compile = await asyncio.gather(
                *(fetch_single_chap(c) for c in target_summaries)
            )
            chapters_to_compile = sorted(chapters_to_compile, key=lambda c: c.order_num)

            cover_bytes: bytes | None = None
            if story.cover_url:
                try:
                    cover_resp = await adapter.client.get(story.cover_url)
                    if cover_resp.status_code == 200:
                        cover_bytes = cover_resp.content
                except Exception as e:
                    logger.warning(f"Could not download cover: {e}")

            if is_all or (actual_start_order == 1 and actual_end_order == total_chapters):
                volume_title = f"Trọn Bộ ({total_chapters} Chương)"
                identifier = f"urn:ztruyen:{source_id}:{story_slug}:all"
            else:
                volume_title = f"Chương {actual_start_order}-{actual_end_order}"
                identifier = f"urn:ztruyen:{source_id}:{story_slug}:c{actual_start_order:04d}-{actual_end_order:04d}"

            epub_bytes, sha1_hash = self.builder.build(
                identifier=identifier,
                title=story.title,
                author=story.author,
                source_name=adapter.name,
                volume_title=volume_title,
                chapters=chapters_to_compile,
                cover_image_bytes=cover_bytes,
            )

            saved_file_path = self.storage.save_epub(filename, epub_bytes)
            return saved_file_path, sha1_hash


volume_bundler = VolumeBundler()
