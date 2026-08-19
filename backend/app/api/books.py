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

