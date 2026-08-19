"""Story detail, Volume catalog, and Paginated Chapter OPDS endpoints."""

from fastapi import APIRouter, Request, Response, HTTPException
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.cache.metadata_repo import repo
from app.cache.fast_cache import fast_cache
from app.epub.bundler import volume_bundler
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Book Details"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


async def _get_cached_story(source_id: str, book_slug: str):
    """Retrieve story metadata with fast in-memory caching."""
    cache_key_story = f"story:{source_id}:{book_slug}"
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    async def _fetch_story():
        try:
            s = await adapter.get_story_detail(book_slug)
            repo.upsert_story(s)
            return s
        except Exception as e:
            cached_s = repo.get_story(source_id, book_slug)
            if cached_s:
                return cached_s
            raise e

    return await fast_cache.get_or_set(cache_key_story, _fetch_story, ttl=1800)


async def _get_cached_chapters(source_id: str, book_slug: str):
    """Retrieve story all chapters with fast in-memory caching."""
    cache_key_chaps = f"chapters:{source_id}:{book_slug}"
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    async def _fetch_chapters():
        return await adapter.get_all_chapters(book_slug)

    return await fast_cache.get_or_set(cache_key_chaps, _fetch_chapters, ttl=1800)


@router.get("/book/{source_id}/{book_slug}", response_class=Response)
async def get_opds_book(
    request: Request,
    source_id: str,
    book_slug: str,
) -> Response:
    """Return story detail feed with list of downloadable EPUB volumes."""
    try:
        story = await _get_cached_story(source_id, book_slug)
        repo.set_last_read(source_id, book_slug, story.title, 1)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch story details ({source_id}:{book_slug}): {e}")
        raise HTTPException(status_code=502, detail=f"Could not load story from source: {e}")

    total_chapters = story.total_chapters
    if total_chapters <= 0:
        try:
            chaps = await _get_cached_chapters(source_id, book_slug)
            total_chapters = len(chaps)
            story.total_chapters = total_chapters
            repo.upsert_story(story)
        except Exception:
            total_chapters = 1

    volume_slices = volume_bundler.calculate_volume_slices(total_chapters)
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
    try:
        story = await _get_cached_story(source_id, book_slug)
        all_chapters = await _get_cached_chapters(source_id, book_slug)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch chapters for ({source_id}:{book_slug}): {e}")
        raise HTTPException(status_code=502, detail=f"Could not load chapters: {e}")

    is_desc = sort.lower() == "desc"
    sorted_chapters = sorted(all_chapters, key=lambda c: c.order, reverse=is_desc)
    total_chapters = len(sorted_chapters)

    last_read = repo.get_last_read()
    last_read_order = None
    if last_read and last_read.get("story_slug") == book_slug:
        last_read_order = last_read.get("chap_order", 1)

    base_url = str(request.base_url).rstrip("/")

    # If no specific range requested and total chapters > 50, display Range Selection Feed (50 chapters/block)
    if start is None and total_chapters > 50:
        xml = OpdsBuilder.build_chapter_ranges_feed(
            story=story,
            total_chapters=total_chapters,
            chapters_per_range=50,
            last_read_order=last_read_order,
            base_url=base_url,
            sort_order=sort.lower(),
        )
        return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)

    # Specific range requested, or total_chapters <= 50
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


@router.get("/api/book/{source_id}/{book_slug}")
@router.get("/api/book/{source_id}/{book_slug}/chapters")
async def get_json_book_chapters(
    source_id: str,
    book_slug: str,
    sort: str = "asc",
):
    """Return JSON chapter list for high-speed interactive Web UI."""
    try:
        story = await _get_cached_story(source_id, book_slug)
        all_chapters = await _get_cached_chapters(source_id, book_slug)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch story chapters: {e}")
        raise HTTPException(status_code=502, detail=f"Could not load chapters: {e}")

    if sort.lower() == "desc":
        all_chapters = sorted(all_chapters, key=lambda c: c.order, reverse=True)
    else:
        all_chapters = sorted(all_chapters, key=lambda c: c.order)

    return {
        "story": {
            "title": story.title,
            "author": story.author,
            "cover_url": story.cover_url,
            "total_chapters": len(all_chapters),
            "description": story.description,
        },
        "chapters": [
            {
                "order": c.order,
                "title": c.title,
                "slug": c.slug,
                "is_vip": c.is_vip,
                "download_url": f"/opds/download/{source_id}/{book_slug}/ztruyen_{source_id}_{book_slug}_c{c.order:04d}.epub",
                "filename": f"ztruyen_{source_id}_{book_slug}_c{c.order:04d}.epub",
            }
            for c in all_chapters
        ],
    }


@router.get("/book/{combined_slug}", response_class=Response)
async def get_opds_book_combined(
    request: Request,
    combined_slug: str,
) -> Response:
    """Handle combined source:slug format (e.g., /opds/book/conduongbachu:main)."""
    if ":" in combined_slug:
        source_id, book_slug = combined_slug.split(":", 1)
        return await get_opds_book(request, source_id, book_slug)
    raise HTTPException(status_code=404, detail=f"Invalid story identifier format: {combined_slug}")
