"""Root OPDS 1.2 catalog navigation, category feeds, source feeds, and cover proxy."""

import asyncio
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import FileResponse
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.domain.models import StorySummary
from app.cache.metadata_repo import repo
from app.cache.cover_service import cover_service
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Catalog"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


@router.get("", response_class=Response)
@router.get("/", response_class=Response)
async def get_opds_root(request: Request, source: str | None = None) -> Response:
    """Return the root OPDS 1.2 navigation feed for Xteink X3 and KOReader."""
    base_url = str(request.base_url).rstrip("/")
    last_read = repo.get_last_read()
    xml = OpdsBuilder.build_root_feed(
        last_read=last_read,
        current_source_id=source,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/sources", response_class=Response)
async def get_opds_sources(request: Request) -> Response:
    """Return list of supported story sources (clean non-technical presentation)."""
    base_url = str(request.base_url).rstrip("/")
    sources = registry.list_adapters()
    xml_entries: list[str] = []

    for src in sources:
        entry_xml = f"""    <entry>
        <title>📚 Kho Truyện: {src.name} ({src.base_url.replace('https://', '')})</title>
        <id>urn:ztruyen:source:{src.id}</id>
        <content type="text">Khám phá tác phẩm từ kho truyện {src.name}</content>
        <link rel="subsection" href="{base_url}/opds/source/{src.id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>"""
        xml_entries.append(entry_xml)

    entries_str = "\n".join(xml_entries)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:sources</id>
    <title>🌐 Chọn Nguồn Truyện Tiếng Việt</title>
    <link rel="self" href="{base_url}/opds/sources" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    <link rel="start" href="{base_url}/opds" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>

{entries_str}
</feed>
"""
    return Response(content=xml.strip(), media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/source/{source_id}", response_class=Response)
@router.get("/sources/{source_id}", response_class=Response)
async def get_opds_source_detail(request: Request, source_id: str) -> Response:
    """Return dedicated navigation feed for a single story source."""
    adapter = registry.get(source_id)
    if not adapter:
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")

    base_url = str(request.base_url).rstrip("/")
    xml = OpdsBuilder.build_source_root_feed(
        source_id=source_id,
        source_name=adapter.name,
        base_url=base_url,
    )
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
        title = f"🔥 Truyện Hot — {adapter.name if adapter else source}"
    else:
        adapters = registry.list_adapters()
        title = "🔥 Truyện Hot & Đọc Nhiều (Tất Cả Nguồn)"

    tasks = [a.get_hot(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch hot stories from a source: {res}")

    prev_url = f"{base_url}/opds/hot?page={page - 1}" + (f"&source={source}" if source else "") if page > 1 else None
    next_url = f"{base_url}/opds/hot?page={page + 1}" + (f"&source={source}" if source else "") if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:hot:{source or 'all'}:{page}",
        title=title,
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
        prev_url=prev_url,
        next_url=next_url,
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
        title = f"⚡ Mới Cập Nhật — {adapter.name if adapter else source}"
    else:
        adapters = registry.list_adapters()
        title = "⚡ Truyện Mới Cập Nhật (Tất Cả Nguồn)"

    tasks = [a.get_latest(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch latest stories: {res}")

    prev_url = f"{base_url}/opds/latest?page={page - 1}" + (f"&source={source}" if source else "") if page > 1 else None
    next_url = f"{base_url}/opds/latest?page={page + 1}" + (f"&source={source}" if source else "") if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:latest:{source or 'all'}:{page}",
        title=title,
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
        prev_url=prev_url,
        next_url=next_url,
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
        title = f"✅ Hoàn Thành — {adapter.name if adapter else source}"
    else:
        adapters = registry.list_adapters()
        title = "✅ Truyện Hoàn Thành (Full Trọn Bộ)"

    tasks = [a.get_completed(page) for a in adapters]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    combined_stories: list[StorySummary] = []
    for res in results:
        if isinstance(res, list):
            combined_stories.extend(res)
        elif isinstance(res, Exception):
            logger.warning(f"Failed to fetch completed stories: {res}")

    prev_url = f"{base_url}/opds/completed?page={page - 1}" + (f"&source={source}" if source else "") if page > 1 else None
    next_url = f"{base_url}/opds/completed?page={page + 1}" + (f"&source={source}" if source else "") if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:completed:{source or 'all'}:{page}",
        title=title,
        stories=combined_stories,
        self_url=self_url,
        base_url=base_url,
        prev_url=prev_url,
        next_url=next_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


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


@router.get("/cover/{source_id}/{book_slug}")
@router.get("/cover")
async def get_story_cover(
    source_id: str | None = None,
    book_slug: str | None = None,
    url: str | None = None,
) -> FileResponse:
    """
    Return high-performance, contrast-enhanced JPEG cover for E-ink screen display.
    Converts WebP/PNG to 100% JPEGDEC-compatible format for Xteink X3.
    """
    cover_path = None
    title = ""
    target_source = source_id or "general"
    target_slug = book_slug or "cover"

    if source_id and book_slug:
        cached_story = repo.get_story(source_id, book_slug)
        cover_remote_url = url or (cached_story.cover_url if cached_story else None)
        title = cached_story.title if cached_story else book_slug

        if not cover_remote_url:
            adapter = registry.get(source_id)
            if adapter:
                try:
                    s_detail = await adapter.get_story_detail(book_slug)
                    cover_remote_url = s_detail.cover_url
                    title = s_detail.title
                    repo.upsert_story(s_detail)
                except Exception:
                    pass

        cover_path = await cover_service.get_or_create_cover(
            source_id=source_id,
            slug=book_slug,
            cover_url=cover_remote_url,
            title=title,
        )
    elif url:
        cover_path = await cover_service.get_or_create_cover(
            source_id="remote",
            slug=cover_service.storage.calculate_sha1(url.encode())[:12],
            cover_url=url,
            title=title,
        )

    if cover_path and cover_path.is_file():
        return FileResponse(
            path=cover_path,
            media_type="image/jpeg",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    raise HTTPException(status_code=404, detail="Cover not found")
