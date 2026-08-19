"""Root OPDS 1.2 catalog navigation and category feeds."""

import asyncio
from fastapi import APIRouter, Request, Response
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.domain.models import StorySummary
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Catalog"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


@router.get("", response_class=Response)
@router.get("/", response_class=Response)
async def get_opds_root(request: Request) -> Response:
    """Return the root OPDS 1.2 navigation feed for Xteink X3 and KOReader."""
    base_url = str(request.base_url).rstrip("/")
    xml = OpdsBuilder.build_root_feed(base_url=base_url)
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/hot", response_class=Response)
@router.get("/catalog/hot", response_class=Response)
async def get_opds_hot(request: Request, page: int = 1, source: str | None = None) -> Response:
    """Return trending and popular stories across active sources (or single source)."""
    base_url = str(request.base_url).rstrip("/")
    self_url = f"{base_url}/opds/hot?page={page}" + (f"&source={source}" if source else "")

    if source:
        adapter = registry.get(source)
        adapters = [adapter] if adapter else []
    else:
        adapters = registry.list_adapters()

    tasks = [a.get_hot(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch hot stories from a source: {res}")

    xml = OpdsBuilder.build_story_list_feed(
        feed_id="urn:ztruyen:category:hot",
        title="🔥 Truyện Hot & Đọc Nhiều",
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/latest", response_class=Response)
@router.get("/catalog/new", response_class=Response)
@router.get("/catalog/latest", response_class=Response)
async def get_opds_latest(request: Request, page: int = 1, source: str | None = None) -> Response:
    """Return newest updated stories."""
    base_url = str(request.base_url).rstrip("/")
    self_url = f"{base_url}/opds/latest?page={page}" + (f"&source={source}" if source else "")

    if source:
        adapter = registry.get(source)
        adapters = [adapter] if adapter else []
    else:
        adapters = registry.list_adapters()

    tasks = [a.get_latest(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch latest stories: {res}")

    xml = OpdsBuilder.build_story_list_feed(
        feed_id="urn:ztruyen:category:latest",
        title="⚡ Truyện Mới Cập Nhật",
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/completed", response_class=Response)
@router.get("/catalog/completed", response_class=Response)
async def get_opds_completed(request: Request, page: int = 1, source: str | None = None) -> Response:
    """Return completed / full stories."""
    base_url = str(request.base_url).rstrip("/")
    self_url = f"{base_url}/opds/completed?page={page}" + (f"&source={source}" if source else "")

    if source:
        adapter = registry.get(source)
        adapters = [adapter] if adapter else []
    else:
        adapters = registry.list_adapters()

    tasks = [a.get_completed(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch completed stories: {res}")

    xml = OpdsBuilder.build_story_list_feed(
        feed_id="urn:ztruyen:category:completed",
        title="✅ Truyện Hoàn Thành (Full)",
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/sources", response_class=Response)
async def get_opds_sources(request: Request) -> Response:
    """Return list of supported story source adapters."""
    base_url = str(request.base_url).rstrip("/")
    sources = registry.list_adapters()
    xml_entries: list[str] = []

    for src in sources:
        entry_xml = f"""    <entry>
        <title>{src.name}</title>
        <id>urn:ztruyen:source:{src.id}</id>
        <content type="text">Khám phá truyện từ {src.name} ({src.base_url})</content>
        <link rel="subsection" href="{base_url}/opds/search?source={src.id}&amp;q=" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>"""
        xml_entries.append(entry_xml)

    entries_str = "\n".join(xml_entries)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:sources</id>
    <title>🌐 Nguồn Cào Truyện</title>
    <link rel="self" href="{base_url}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>

{entries_str}
</feed>
"""
    return Response(content=xml.strip(), media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/genres", response_class=Response)
@router.get("/the-loai", response_class=Response)
async def get_opds_genres(request: Request) -> Response:
    """Return list of supported story genres across sources."""
    base_url = str(request.base_url).rstrip("/")
    tasks = [a.get_genres() for a in registry.list_adapters()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_genres = []
    seen_slugs = set()
    for res in results:
        if isinstance(res, list):
            for g in res:
                if g.slug not in seen_slugs:
                    seen_slugs.add(g.slug)
                    all_genres.append(g)

    xml_entries: list[str] = []
    for g in all_genres:
        entry_xml = f"""    <entry>
        <title>{g.name}</title>
        <id>urn:ztruyen:genre:{g.slug}</id>
        <content type="text">Khám phá thể loại {g.name}</content>
        <link rel="subsection" href="{base_url}/opds/search?q={g.name}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>"""
        xml_entries.append(entry_xml)

    entries_str = "\n".join(xml_entries)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:genres</id>
    <title>📂 Thể Loại Truyện</title>
    <link rel="self" href="{base_url}/opds/genres" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>

{entries_str}
</feed>
"""
    return Response(content=xml.strip(), media_type=ATOM_XML_MEDIA_TYPE)
