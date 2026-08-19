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
    self_url = f"{base_url}/opds/search?q={q}" + (f"&source={source}" if source else "")

    results: list[StorySummary] = []

    if source:
        adapter = registry.get(source)
        if adapter:
            try:
                results = await adapter.search(q, page=page)
            except Exception as e:
                logger.error(f"Search failed for source '{source}': {e}")
    else:
        results = await registry.search_all(q)

    title = f"Kết quả tìm kiếm: '{q}'" if q else "Tìm kiếm truyện"
    from urllib.parse import quote
    safe_q = quote(q.strip()) if q else "all"

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:search:{safe_q}",
        title=title,
        stories=results,
        self_url=self_url,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)
