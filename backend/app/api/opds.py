"""Root OPDS 1.2 catalog navigation, category feeds, source feeds, and cover proxy."""

import asyncio
from fastapi import APIRouter, Request, Response, HTTPException
from fastapi.responses import FileResponse
from app.api.opds_builder import OpdsBuilder
from app.sources.registry import registry
from app.domain.models import StorySummary
from app.cache.metadata_repo import repo
from app.cache.fast_cache import fast_cache
from app.cache.cover_service import cover_service
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Catalog"])

ATOM_XML_MEDIA_TYPE = "application/atom+xml;profile=opds-catalog"


@router.get("", response_class=Response)
@router.get("/", response_class=Response)
async def get_opds_root(request: Request, source: str | None = None) -> Response:
    """Return the root OPDS 1.2 navigation feed for Xteink X3 and KOReader."""
    base_url = str(request.base_url).rstrip("/")
    if source:
        repo.set_active_source(source)
    active_source = source or repo.get_active_source()
    last_read = repo.get_last_read()
    xml = OpdsBuilder.build_root_feed(
        last_read=last_read,
        current_source_id=active_source,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/sources", response_class=Response)
async def get_opds_sources(request: Request) -> Response:
    """Return list of supported story sources for easy source switching."""
    base_url = str(request.base_url).rstrip("/")
    sources = registry.list_adapters()
    active_source = repo.get_active_source()
    xml_entries: list[str] = []

    for src in sources:
        is_active = (src.id == active_source)
        active_mark = " (Đang chọn)" if is_active else ""
        entry_xml = f"""    <entry>
        <title>📚 {src.name}{active_mark}</title>
        <id>urn:ztruyen:source:{src.id}</id>
        <content type="text">Chọn kho truyện {src.name} làm nguồn hoạt động chính.</content>
        <link rel="subsection" href="{base_url}/opds?source={src.id}" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>"""
        xml_entries.append(entry_xml)

    # Option for all sources
    all_active = " (Đang chọn)" if active_source == "all" else ""
    xml_entries.append(f"""    <entry>
        <title>🌐 Tất Cả Nguồn (Tổng Hợp){all_active}</title>
        <id>urn:ztruyen:source:all</id>
        <content type="text">Khám phá tổng hợp tác phẩm từ tất cả nguồn truyện.</content>
        <link rel="subsection" href="{base_url}/opds?source=all" type="application/atom+xml;profile=opds-catalog;kind=navigation"/>
    </entry>""")

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
    """Select source and return dedicated navigation feed for a single story source."""
    adapter = registry.get(source_id)
    if not adapter and source_id != "all":
        raise HTTPException(status_code=404, detail=f"Source '{source_id}' not found")

    repo.set_active_source(source_id)
    base_url = str(request.base_url).rstrip("/")
    last_read = repo.get_last_read()
    xml = OpdsBuilder.build_root_feed(
        last_read=last_read,
        current_source_id=source_id,
        base_url=base_url,
    )
    return Response(content=xml, media_type=ATOM_XML_MEDIA_TYPE)


@router.get("/hot", response_class=Response)
@router.get("/catalog/hot", response_class=Response)
async def get_opds_hot(request: Request, page: int = 1, source: str | None = None) -> Response:
    """Return trending and popular stories across active sources (or single source)."""
    base_url = str(request.base_url).rstrip("/")
    active_source = source if source is not None else repo.get_active_source()
    cache_key = f"feed:hot:{active_source or 'all'}:{page}"

    async def _fetch():
        if active_source and active_source != "all":
            adapter = registry.get(active_source)
            adapters = [adapter] if adapter else []
            title = f"🔥 Truyện Hot — {adapter.name if adapter else active_source}"
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
        return title, combined_stories

    title, combined_stories = await fast_cache.get_or_set(cache_key, _fetch, ttl=300)

    source_param = f"&source={active_source}" if active_source and active_source != "all" else ""
    self_url = f"{base_url}/opds/hot?page={page}{source_param}"
    prev_url = f"{base_url}/opds/hot?page={page - 1}{source_param}" if page > 1 else None
    next_url = f"{base_url}/opds/hot?page={page + 1}{source_param}" if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:hot:{active_source or 'all'}:{page}",
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
    active_source = source if source is not None else repo.get_active_source()
    cache_key = f"feed:latest:{active_source or 'all'}:{page}"

    async def _fetch():
        if active_source and active_source != "all":
            adapter = registry.get(active_source)
            adapters = [adapter] if adapter else []
            title = f"⚡ Truyện Mới Cập Nhật — {adapter.name if adapter else active_source}"
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
        return title, combined_stories

    title, combined_stories = await fast_cache.get_or_set(cache_key, _fetch, ttl=300)

    source_param = f"&source={active_source}" if active_source and active_source != "all" else ""
    self_url = f"{base_url}/opds/latest?page={page}{source_param}"
    prev_url = f"{base_url}/opds/latest?page={page - 1}{source_param}" if page > 1 else None
    next_url = f"{base_url}/opds/latest?page={page + 1}{source_param}" if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:latest:{active_source or 'all'}:{page}",
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
    active_source = source if source is not None else repo.get_active_source()
    cache_key = f"feed:completed:{active_source or 'all'}:{page}"

    async def _fetch():
        if active_source and active_source != "all":
            adapter = registry.get(active_source)
            adapters = [adapter] if adapter else []
            title = f"✅ Truyện Hoàn Thành — {adapter.name if adapter else active_source}"
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
        return title, combined_stories

    title, combined_stories = await fast_cache.get_or_set(cache_key, _fetch, ttl=600)

    source_param = f"&source={active_source}" if active_source and active_source != "all" else ""
    self_url = f"{base_url}/opds/completed?page={page}{source_param}"
    prev_url = f"{base_url}/opds/completed?page={page - 1}{source_param}" if page > 1 else None
    next_url = f"{base_url}/opds/completed?page={page + 1}{source_param}" if len(combined_stories) >= 10 else None

    xml = OpdsBuilder.build_story_list_feed(
        feed_id=f"urn:ztruyen:category:completed:{active_source or 'all'}:{page}",
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
async def get_opds_genres(request: Request, source: str | None = None) -> Response:
    """Return list of supported story genres for active source (or all sources)."""
    base_url = str(request.base_url).rstrip("/")
    active_source = source if source is not None else repo.get_active_source()
    cache_key = f"feed:genres:{active_source or 'all'}"

    async def _fetch():
        if active_source and active_source != "all":
            adapter = registry.get(active_source)
            adapters = [adapter] if adapter else []
            source_name = adapter.name if adapter else active_source
        else:
            adapters = registry.list_adapters()
            source_name = "Tất Cả Nguồn"

        tasks = [a.get_genres() for a in adapters]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_genres = []
        seen_slugs = set()
        for res in results:
            if isinstance(res, list):
                for g in res:
                    if g.slug not in seen_slugs:
                        seen_slugs.add(g.slug)
                        all_genres.append(g)
        return source_name, all_genres

    source_name, all_genres = await fast_cache.get_or_set(cache_key, _fetch, ttl=1800)

    xml_entries: list[str] = []
    source_query = f"&source={active_source}" if active_source and active_source != "all" else ""
    for g in all_genres:
        search_url = f"{base_url}/opds/search?q={g.name}{source_query}"
        entry_xml = f"""    <entry>
        <title>{g.name}</title>
        <id>urn:ztruyen:genre:{g.slug}</id>
        <content type="text">Khám phá thể loại {g.name} từ {source_name}</content>
        <link rel="subsection" href="{search_url}" type="application/atom+xml;profile=opds-catalog;kind=acquisition"/>
    </entry>"""
        xml_entries.append(entry_xml)

    entries_str = "\n".join(xml_entries)
    xml = f"""<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:dc="http://purl.org/dc/terms/"
      xmlns:opds="http://opds-spec.org/2010/catalog">
    <id>urn:ztruyen:genres:{active_source or 'all'}</id>
    <title>📂 Thể Loại Truyện ({source_name})</title>
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
    """Proxy and optimize original book cover image to X3 BMP/JPEG dimensions."""
    target_url = url
    if not target_url and source_id and book_slug:
        cached_story = repo.get_story(source_id, book_slug)
        if cached_story and cached_story.cover_url:
            target_url = cached_story.cover_url
        else:
            adapter = registry.get(source_id)
            if adapter:
                try:
                    story = await adapter.get_story_detail(book_slug)
                    target_url = story.cover_url
                except Exception as e:
                    logger.warning(f"Could not resolve cover URL for {source_id}:{book_slug}: {e}")

    if not target_url:
        raise HTTPException(status_code=404, detail="Cover image URL not found")

    try:
        cover_path = await cover_service.get_or_create_cover(
            source_id=source_id or "generic",
            slug=book_slug or "cover",
            cover_url=target_url,
        )
        return FileResponse(path=cover_path, media_type="image/jpeg")
    except Exception as e:
        logger.error(f"Failed to serve cover image ({target_url}): {e}")
        raise HTTPException(status_code=502, detail=f"Failed to retrieve cover image: {e}")
