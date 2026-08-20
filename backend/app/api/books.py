"""OPDS acquisition feeds for book details, volumes, chapters, and EPUB binary downloads."""

import asyncio
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, Request, Response
from app.api.opds_builder import OpdsBuilder
from app.cache.fast_cache import fast_cache
from app.cache.metadata_repo import repo
from app.domain.models import Story
from app.epub.bundler import volume_bundler
from app.logging import logger
from app.sources.registry import registry

router = APIRouter(prefix="/opds", tags=["OPDS Books"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"
EPUB_MEDIA_TYPE = "application/epub+zip"


async def _get_cached_story(source_id: str, book_slug: str) -> Story:
    """Retrieve story metadata with FastCache."""
    cache_key = f"story:{source_id}:{book_slug}"
    cached = fast_cache.get(cache_key)
    if cached is not None:
        return cached

    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    try:
        story = await adapter.get_story_detail(book_slug)
        fast_cache.set(cache_key, story, ttl=600.0)
        return story
    except Exception as e:
        logger.error(f"Failed to fetch story details ({source_id}:{book_slug}): {e}")
        raise HTTPException(status_code=502, detail=f"Could not load story details: {e}")


async def _get_cached_chapters(source_id: str, book_slug: str) -> list:
    """Retrieve all chapter summaries with FastCache."""
    cache_key = f"chapters:{source_id}:{book_slug}"
    cached = fast_cache.get(cache_key)
    if cached is not None:
        return cached

    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    try:
        all_chapters = await adapter.get_all_chapters(book_slug)
        fast_cache.set(cache_key, all_chapters, ttl=600.0)
        return all_chapters
    except Exception as e:
        logger.error(f"Failed to fetch chapter list ({source_id}:{book_slug}): {e}")
        raise HTTPException(status_code=502, detail=f"Could not load chapter list: {e}")


@router.get("/book/{source_id}/{book_slug}", response_class=Response)
async def get_opds_book_detail(
    request: Request,
    source_id: str,
    book_slug: str,
) -> Response:
    """Return story detail feed with multiple acquisition options: Single-chapter, Volumes, Full story."""
    story = await _get_cached_story(source_id, book_slug)

    total_chapters = story.total_chapters or 0
    if total_chapters <= 1:
        all_chaps = await _get_cached_chapters(source_id, book_slug)
        total_chapters = len(all_chaps) if all_chaps else 1

    volume_slices = volume_bundler.calculate_volume_slices(total_chapters=total_chapters)

    base_url = str(request.base_url).rstrip("/")
    xml = OpdsBuilder.build_book_volumes_feed(
        story=story,
        volume_slices=volume_slices,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/book/{source_id}/{book_slug}/chapters", response_class=Response)
async def get_opds_book_chapters(
    request: Request,
    source_id: str,
    book_slug: str,
    start: int | None = None,
    limit: int = 50,
    sort: str = "asc",
) -> Response:
    """Return individual chapters feed with range groups / pagination support for X3."""
    story = await _get_cached_story(source_id, book_slug)
    total_chapters = story.total_chapters or 0
    if total_chapters <= 1 and start is None:
        all_chaps = await _get_cached_chapters(source_id, book_slug)
        total_chapters = len(all_chaps) if all_chaps else 1
    base_url = str(request.base_url).rstrip("/")

    # If no specific range requested and story has > 50 chapters, return Range Selection Screen instantly
    if start is None and total_chapters > 50:
        last_read = repo.get_last_read()
        last_read_order = None
        if last_read and last_read.get("story_slug") == book_slug:
            last_read_order = last_read.get("chap_order", 1)

        xml = OpdsBuilder.build_chapter_ranges_feed(
            story=story,
            total_chapters=total_chapters,
            chapters_per_range=50,
            last_read_order=last_read_order,
            base_url=base_url,
            sort_order=sort.lower(),
        )
        return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)

    # Specific range requested or short story <= 50 chapters -> Load chapter list
    all_chapters = await _get_cached_chapters(source_id, book_slug)
    is_desc = sort.lower() == "desc"
    sorted_chapters = sorted(all_chapters, key=lambda c: c.order, reverse=is_desc)

    start_order = start if start is not None else (sorted_chapters[0].order if sorted_chapters else 1)
    if is_desc:
        filtered = [c for c in sorted_chapters if c.order <= start_order]
        sliced = filtered[:limit]
    else:
        filtered = [c for c in sorted_chapters if c.order >= start_order]
        sliced = filtered[:limit]

    # Build pagination links
    prev_url = None
    next_url = None
    range_label = ""

    if sliced:
        first_ch = sliced[0].order
        last_ch = sliced[-1].order
        range_label = f"Chương {min(first_ch, last_ch)} - {max(first_ch, last_ch)}"

        if is_desc:
            if first_ch < total_chapters:
                prev_start = min(first_ch + limit, total_chapters)
                prev_url = f"{base_url}/opds/book/{source_id}/{book_slug}/chapters?start={prev_start}&limit={limit}&sort=desc"
            if len(filtered) > limit:
                next_start = sliced[-1].order - 1
                if next_start >= 1:
                    next_url = f"{base_url}/opds/book/{source_id}/{book_slug}/chapters?start={next_start}&limit={limit}&sort=desc"
        else:
            if first_ch > 1:
                prev_start = max(1, first_ch - limit)
                prev_url = f"{base_url}/opds/book/{source_id}/{book_slug}/chapters?start={prev_start}&limit={limit}&sort=asc"
            if len(filtered) > limit:
                next_start = sliced[-1].order + 1
                next_url = f"{base_url}/opds/book/{source_id}/{book_slug}/chapters?start={next_start}&limit={limit}&sort=asc"

    self_url = f"{base_url}/opds/book/{source_id}/{book_slug}/chapters?start={start_order}&limit={limit}&sort={sort.lower()}"

    xml = OpdsBuilder.build_book_chapters_feed(
        story=story,
        chapters=sliced,
        base_url=base_url,
        sort_order=sort.lower(),
        range_label=range_label,
        self_url=self_url,
        prev_url=prev_url,
        next_url=next_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/api/book/{source_id}/{book_slug}/chapters")
async def get_book_chapters_json(
    source_id: str,
    book_slug: str,
    sort: str = "asc",
):
    """JSON API endpoint for Web UI to fetch chapter lists."""
    story = await _get_cached_story(source_id, book_slug)
    all_chapters = await _get_cached_chapters(source_id, book_slug)
    is_desc = sort.lower() == "desc"
    sorted_chapters = sorted(all_chapters, key=lambda c: c.order, reverse=is_desc)
    return {
        "story": {
            "id": story.id,
            "title": story.title,
            "author": story.author,
            "total_chapters": len(all_chapters),
        },
        "chapters": [
            {
                "order": c.order,
                "title": c.title,
                "slug": c.slug,
                "is_vip": c.is_vip,
            }
            for c in sorted_chapters
        ],
    }


@router.get("/download/{source_id}/{story_slug}/{filename}")
async def download_epub(
    request: Request,
    source_id: str,
    story_slug: str,
    filename: str,
) -> Response:
    """Stream or generate on-demand EPUB binary (single-chapter, volume, custom range, or all chapters)."""
    clean_filename = Path(filename).name
    if not clean_filename.endswith(".epub"):
        raise HTTPException(status_code=400, detail="Only .epub files are supported")

    try:
        m_range = re.search(r"_c(\d+)-(\d+)\.epub$", clean_filename)
        m_single = re.search(r"_c(\d+)\.epub$", clean_filename)
        m_vol = re.search(r"_v(\d+)\.epub$", clean_filename)
        m_all = re.search(r"_all\.epub$", clean_filename)

        if m_range:
            start_order = int(m_range.group(1))
            end_order = int(m_range.group(2))
            epub_path, sha1_hash = await volume_bundler.get_or_build_custom_range(
                source_id=source_id,
                story_slug=story_slug,
                start_order=start_order,
                end_order=end_order,
            )
        elif m_all:
            epub_path, sha1_hash = await volume_bundler.get_or_build_custom_range(
                source_id=source_id,
                story_slug=story_slug,
                start_order=1,
                end_order=99999,
            )
        elif m_single:
            chap_order = int(m_single.group(1))
            epub_path, sha1_hash = await volume_bundler.get_or_build_single_chapter(
                source_id=source_id,
                story_slug=story_slug,
                chap_order=chap_order,
            )
            # Trigger background prefetch
            asyncio.create_task(
                volume_bundler.prefetch_and_cleanup(
                    source_id=source_id,
                    story_slug=story_slug,
                    current_chap_order=chap_order,
                )
            )
        elif m_vol:
            vol_index = int(m_vol.group(1))
            epub_path, sha1_hash = await volume_bundler.get_or_build_volume(
                source_id=source_id,
                story_slug=story_slug,
                vol_index=vol_index,
            )
        else:
            raise HTTPException(status_code=400, detail="Unrecognized EPUB filename format")

        # Update last read progress with real story title
        try:
            story_obj = repo.get_story(source_id, story_slug)
            real_title = story_obj.title if (story_obj and story_obj.title) else story_slug
            read_order = 1
            if m_single:
                read_order = int(m_single.group(1))
            elif m_vol:
                read_order = (int(m_vol.group(1)) - 1) * 50 + 1
            elif m_range:
                read_order = int(m_range.group(1))
            repo.set_last_read(
                source_id=source_id,
                story_slug=story_slug,
                story_title=real_title,
                chap_order=read_order,
            )
        except Exception as e:
            logger.debug(f"Failed to update last_read on download: {e}")

        if not epub_path.is_file():
            raise HTTPException(status_code=500, detail="EPUB build completed but file not found on disk")

        epub_bytes = epub_path.read_bytes()
        headers = {
            "Content-Disposition": f'attachment; filename="{clean_filename}"',
            "Content-Length": str(len(epub_bytes)),
            "X-KOSync-SHA1": sha1_hash,
        }
        return Response(
            content=epub_bytes,
            media_type=EPUB_MEDIA_TYPE,
            headers=headers,
        )

    except HTTPException:
        raise
    except ValueError as ve:
        logger.error(f"Value error while preparing EPUB download ({filename}): {ve}")
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Unexpected error while preparing EPUB download ({filename}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate EPUB: {e}")
