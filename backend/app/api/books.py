"""Story detail and Volume catalog OPDS endpoints."""

from fastapi import APIRouter, Request, Response, HTTPException
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.cache.metadata_repo import repo
from app.epub.bundler import volume_bundler
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Book Details"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


@router.get("/book/{source_id}/{book_slug}", response_class=Response)
async def get_opds_book(
    request: Request,
    source_id: str,
    book_slug: str,
) -> Response:
    """Return story detail feed with list of downloadable EPUB volumes."""
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    try:
        story = await adapter.get_story_detail(book_slug)
        repo.upsert_story(story)
    except Exception as e:
        logger.error(f"Failed to fetch story details ({source_id}:{book_slug}): {e}")
        # Try local cache
        cached_story = repo.get_story(source_id, book_slug)
        if cached_story:
            story = cached_story
        else:
            raise HTTPException(status_code=502, detail=f"Could not load story from source: {e}")

    total_chapters = story.total_chapters
    if total_chapters <= 0:
        try:
            all_chapters = await adapter.get_all_chapters(book_slug)
            total_chapters = len(all_chapters)
            story.total_chapters = total_chapters
            repo.upsert_story(story)
        except Exception as e:
            logger.warning(f"Could not load chapter count: {e}")
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
    sort: str = "asc",
) -> Response:
    """Return story detail feed with individual chapters (supports ?sort=asc|desc)."""
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    try:
        story = await adapter.get_story_detail(book_slug)
        all_chapters = await adapter.get_all_chapters(book_slug)
    except Exception as e:
        logger.error(f"Failed to fetch chapters for ({source_id}:{book_slug}): {e}")
        raise HTTPException(status_code=502, detail=f"Could not load chapters: {e}")

    if sort.lower() == "desc":
        all_chapters = sorted(all_chapters, key=lambda c: c.order, reverse=True)
    else:
        all_chapters = sorted(all_chapters, key=lambda c: c.order)

    base_url = str(request.base_url).rstrip("/")
    xml = OpdsBuilder.build_book_chapters_feed(
        story=story,
        chapters=all_chapters,
        base_url=base_url,
        sort_order=sort.lower(),
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
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source adapter '{source_id}' not found")

    try:
        story = await adapter.get_story_detail(book_slug)
        all_chapters = await adapter.get_all_chapters(book_slug)
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

