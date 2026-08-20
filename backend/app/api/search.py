"""OpenSearch OPDS endpoint for searching stories."""

from fastapi import APIRouter, Request, Response, Query
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.domain.models import StorySummary
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Search"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


@router.get("/search", response_class=Response)
async def search_opds(
    request: Request,
    q: str = Query("", description="Search keywords"),
    source: str | None = Query(None, description="Optional source filter (storyaclick, akaytruyen, conduongbachu)"),
    page: int = Query(1, ge=1),
) -> Response:
    """Search stories matching keywords across sources."""
    base_url = str(request.base_url).rstrip("/")
    from app.cache.metadata_repo import repo
    from app.domain.sanitizer import remove_accents

    active_source = source if source is not None else repo.get_active_source()
    self_url = f"{base_url}/opds/search?q={q}" + (f"&source={active_source}" if active_source and active_source != "all" else "")

    results: list[StorySummary] = []

    if active_source and active_source != "all":
        adapter = registry.get(active_source)
        if adapter:
            try:
                results = await adapter.search(q, page=page)
            except Exception as e:
                logger.error(f"Search failed for source '{active_source}': {e}")
    else:
        results = await registry.search_all(q)

    # Rank results matching unaccented query first
    if q and results:
        q_unaccent = remove_accents(q)
        def _score(item: StorySummary) -> int:
            t_unaccent = remove_accents(item.title)
            if t_unaccent == q_unaccent:
                return 0
            if t_unaccent.startswith(q_unaccent):
                return 1
            if q_unaccent in t_unaccent:
                return 2
            return 3
        results = sorted(results, key=_score)

    source_name = ""
    if active_source and active_source != "all":
        adapter = registry.get(active_source)
        if adapter:
            source_name = f" ({adapter.name})"

    title = f"Kết quả tìm kiếm: '{q}'{source_name}" if q else f"Tìm kiếm truyện{source_name}"
    from urllib.parse import quote
    safe_q = quote(q.strip()) if q else "all"

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:search:{safe_q}:{active_source or 'all'}",
        title=title,
        stories=results,
        self_url=self_url,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)
