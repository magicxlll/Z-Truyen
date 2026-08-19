"""Z-Truyen OPDS Backend - FastAPI application."""

import logging
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import Response

from mock_data import MOCK_BOOKS
from opds_renderer import render_root_catalog, render_book_detail
from sources import create_storya_adapter, create_conduongbachu_adapter, BookSummary, Chapter, ChapterContent
from epub_builder import build_epub

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class XMLResponse(Response):
    """Custom XML Response class for OPDS feeds."""

    media_type = "application/xml"

    def __init__(self, content: str, status_code: int = 200, media_type: str = None, **kwargs):
        super().__init__(content=content, status_code=status_code, media_type=media_type, **kwargs)


app = FastAPI(
    title="Z-Truyen OPDS Backend",
    version="0.1.0",
    description="Vietnamese story discovery and download for Xteink X3",
)

# Configure CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for EPUB downloads
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.on_event("startup")
async def startup_event():
    """Initialize resources on startup."""
    app.state.storya_adapter = create_storya_adapter()
    app.state.conduongbachu_adapter = create_conduongbachu_adapter()
    logger.info("Storya adapter initialized")
    logger.info("ConDuongBaChu adapter initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    if hasattr(app.state, "storya_adapter"):
        await app.state.storya_adapter.close()
        logger.info("Storya adapter closed")
    if hasattr(app.state, "conduongbachu_adapter"):
        await app.state.conduongbachu_adapter.close()
        logger.info("ConDuongBaChu adapter closed")


@app.get("/healthz", response_model_exclude_none=True)
async def healthz() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "ok", "version": "0.1.0"})


@app.get("/opds", response_class=XMLResponse)
async def opds_root(request: Request) -> XMLResponse:
    """Root OPDS catalog endpoint.

    Returns an XML catalog containing all available books from all sources.
    Combines books from storya.click and ConDuongBaChu.com.
    Falls back to mock data if all APIs are unavailable.
    """
    base_url = str(request.base_url).rstrip("/")
    storya_adapter = getattr(request.app.state, "storya_adapter", None)
    conduongbachu_adapter = getattr(request.app.state, "conduongbachu_adapter", None)

    all_books: list[BookSummary] = []

    # Fetch from storya
    try:
        if storya_adapter:
            storya_books = await storya_adapter.list_books()
            all_books.extend(storya_books)
            logger.info(f"Fetched {len(storya_books)} books from storya")
    except httpx.HTTPStatusError as e:
        logger.warning(f"storya.click API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching from storya.click: {e}")

    # Fetch from ConDuongBaChu
    try:
        if conduongbachu_adapter:
            conduongbachu_books = await conduongbachu_adapter.list_books()
            all_books.extend(conduongbachu_books)
            logger.info(f"Fetched {len(conduongbachu_books)} books from ConDuongBaChu")
    except httpx.HTTPStatusError as e:
        logger.warning(f"ConDuongBaChu API error: {e}")
    except Exception as e:
        logger.error(f"Error fetching from ConDuongBaChu: {e}")

    # Return combined catalog
    if all_books:
        xml_content = render_root_catalog(all_books, base_url)
        return XMLResponse(
            content=xml_content,
            media_type="application/atom+xml;profile=opds-catalog;kind=navigation"
        )

    # Fallback to mock data if all sources fail
    xml_content = render_root_catalog(MOCK_BOOKS, base_url)
    return XMLResponse(
        content=xml_content,
        media_type="application/atom+xml;profile=opds-catalog;kind=navigation"
    )


@app.get("/opds/search", response_class=XMLResponse)
async def opds_search(request: Request, q: str = "") -> XMLResponse:
    """Search endpoint for OPDS catalog.

    Returns search results from all sources (storya.click, ConDuongBaChu.com).

    Args:
        request: The incoming request.
        q: Search query string.
    """
    base_url = str(request.base_url).rstrip("/")
    storya_adapter = getattr(request.app.state, "storya_adapter", None)
    conduongbachu_adapter = getattr(request.app.state, "conduongbachu_adapter", None)

    if not q.strip():
        # Return empty catalog if query is empty
        xml_content = render_root_catalog([], base_url)
        return XMLResponse(
            content=xml_content,
            media_type="application/atom+xml;profile=opds-catalog;kind=navigation"
        )

    all_results: list[BookSummary] = []

    # Search storya
    try:
        if storya_adapter:
            results = await storya_adapter.search(q.strip())
            all_results.extend(results)
    except httpx.HTTPStatusError as e:
        logger.warning(f"storya.click search API error: {e}")
    except Exception as e:
        logger.error(f"Error searching storya.click: {e}")

    # Note: ConDuongBaChu does not support search, skip it

    xml_content = render_root_catalog(all_results, base_url)
    return XMLResponse(
        content=xml_content,
        media_type="application/atom+xml;profile=opds-catalog;kind=navigation"
    )


@app.get("/opds/book/{book_id}", response_class=XMLResponse)
async def opds_book_detail(request: Request, book_id: str) -> XMLResponse:
    """Book detail endpoint with chapter list.

    Routes to the appropriate adapter based on book_id source prefix.

    Args:
        request: The incoming request.
        book_id: The unique identifier of the book (format: source:book_id).
                 Supported formats:
                 - storya:<book_slug>
                 - conduongbachu:<story_id>
    """
    base_url = str(request.base_url).rstrip("/")
    storya_adapter = getattr(request.app.state, "storya_adapter", None)
    conduongbachu_adapter = getattr(request.app.state, "conduongbachu_adapter", None)

    # Route to appropriate adapter based on source prefix
    if book_id.startswith("storya:"):
        adapter = storya_adapter
        source_name = "storya.click"
    elif book_id.startswith("conduongbachu:"):
        adapter = conduongbachu_adapter
        source_name = "ConDuongBaChu"
    else:
        return XMLResponse(
            content=f"""<?xml version="1.0" encoding="UTF-8"?>
<error>
  <message>Unsupported book source: {book_id}</message>
</error>""",
            status_code=400,
            media_type="application/xml",
        )

    if not adapter:
        return XMLResponse(
            content=f"""<?xml version="1.0" encoding="UTF-8"?>
<error>
  <message>{source_name} adapter not available</message>
</error>""",
            status_code=503,
            media_type="application/xml",
        )

    try:
        # Fetch book details
        book = await adapter.get_book(book_id)
        # Fetch chapters
        chapters = await adapter.list_chapters(book_id)

        xml_content = render_book_detail(book, base_url, chapters)
        return XMLResponse(
            content=xml_content,
            media_type="application/atom+xml;profile=opds-catalog;kind=acquisition"
        )
    except httpx.HTTPStatusError as e:
        logger.warning(f"{source_name} book API error: {e}")
    except ValueError as e:
        logger.warning(f"Invalid book ID format: {e}")
    except Exception as e:
        logger.error(f"Error fetching book from {source_name}: {e}")

    return XMLResponse(
        content=f"""<?xml version="1.0" encoding="UTF-8"?>
<error>
  <message>Book not found: {book_id}</message>
</error>""",
        status_code=404,
        media_type="application/xml",
    )


@app.get("/opds/download/{chapter_id}")
async def opds_download(request: Request, chapter_id: str) -> StreamingResponse:
    """Download endpoint for chapter EPUB.

    Parses chapter_id to extract source and route to the appropriate adapter,
    then fetches content and generates an EPUB file.

    Args:
        request: The incoming request.
        chapter_id: The unique identifier of the chapter.
                    Supported formats:
                    - storya:<book_slug>:<chapter_slug>
                    - conduongbachu:<story_id>:<chapter_num>

    Returns:
        EPUB file as streaming response.
    """
    storya_adapter = getattr(request.app.state, "storya_adapter", None)
    conduongbachu_adapter = getattr(request.app.state, "conduongbachu_adapter", None)

    # Parse chapter_id based on source
    parts = chapter_id.split(":")
    if len(parts) < 2:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid chapter ID format: {chapter_id}. "
                   f"Expected format: source:book_id:chapter_id"
        )

    source_id = parts[0]
    adapter = None
    source_name = ""

    if source_id == "storya":
        if len(parts) != 3:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid storya chapter ID format: {chapter_id}. "
                       f"Expected: storya:<book_slug>:<chapter_slug>"
            )
        adapter = storya_adapter
        source_name = "storya.click"
        book_slug = parts[1]
        book_id = f"storya:{book_slug}"
    elif source_id == "conduongbachu":
        if len(parts) != 3:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid conduongbachu chapter ID format: {chapter_id}. "
                       f"Expected: conduongbachu:<story_id>:<chapter_num>"
            )
        adapter = conduongbachu_adapter
        source_name = "ConDuongBaChu"
        story_id = parts[1]
        book_id = f"conduongbachu:{story_id}"
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported source: {source_id}"
        )

    if not adapter:
        raise HTTPException(
            status_code=503,
            detail=f"{source_name} adapter not available"
        )

    # Create chapter object for API call
    chapter = Chapter(
        id=chapter_id,
        title="",  # Will be filled by API
        order=0,
        book_id=book_id,
        url=""
    )

    try:
        # Fetch chapter content
        chapter_content = await adapter.get_chapter_content(chapter)
    except httpx.HTTPStatusError as e:
        logger.warning(f"{source_name} chapter API error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch chapter from {source_name}"
        )
    except ValueError as e:
        logger.warning(f"Chapter not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Chapter not found: {chapter_id}"
        )

    try:
        # Fetch book details for metadata
        book = await adapter.get_book(book_id)
    except httpx.HTTPStatusError as e:
        logger.warning(f"{source_name} book API error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch book metadata from {source_name}"
        )
    except ValueError as e:
        logger.warning(f"Book not found: {e}")
        raise HTTPException(
            status_code=404,
            detail=f"Book not found: {book_id}"
        )

    try:
        # Build EPUB
        epub_bytes = build_epub(
            chapter=chapter_content,
            book_title=book.title,
            author=book.author,
            cover_url=book.cover_url
        )

        # Generate filename (ASCII-only for HTTP header compatibility with latin-1 encoding)
        # Remove all non-ASCII characters and replace spaces with underscores
        safe_title = "".join(c if (ord(c) < 128 and c.isalnum()) else "_" for c in book.title).strip()[:50]
        # Collapse multiple underscores
        while "__" in safe_title:
            safe_title = safe_title.replace("__", "_")
        safe_title = safe_title.strip("_")
        filename = f"ztruyen__{safe_title}__chuong_{chapter_content.chapter_order:04d}.epub"

        return StreamingResponse(
            iter([epub_bytes]),
            media_type="application/epub+zip",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(epub_bytes)),
            }
        )
    except Exception as e:
        import traceback
        logger.error(f"Error building EPUB: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal error generating EPUB: {e}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
