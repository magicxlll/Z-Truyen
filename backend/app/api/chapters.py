"""EPUB file download gateway endpoint for Xteink X3 and KOReader."""

import re
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.epub.bundler import volume_bundler
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Download Gateway"])


@router.get("/download/{source_id}/{book_slug}/{artifact_name}")
async def download_epub(
    source_id: str,
    book_slug: str,
    artifact_name: str,
) -> FileResponse:
    """
    Download compiled EPUB volume or single chapter directly to X3 SD card.
    """
    # 1. Check if Volume Bundle pattern: _v{index}.epub
    vol_match = re.search(r"_v(\d+)\.epub$", artifact_name, re.IGNORECASE)
    if vol_match:
        vol_index = int(vol_match.group(1))
        try:
            file_path, sha1_hash = await volume_bundler.get_or_build_volume(
                source_id=source_id,
                story_slug=book_slug,
                vol_index=vol_index,
            )
            return FileResponse(
                path=file_path,
                media_type="application/epub+zip",
                filename=artifact_name,
                headers={"X-KOSync-SHA1": sha1_hash},
            )
        except Exception as e:
            logger.error(f"Failed to build volume {vol_index} for {source_id}:{book_slug}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build volume EPUB: {e}")

    # 2. Check if Single Chapter pattern: _c{order}.epub
    chap_match = re.search(r"_c(\d+)\.epub$", artifact_name, re.IGNORECASE)
    if chap_match:
        chap_order = int(chap_match.group(1))
        try:
            file_path, sha1_hash = await volume_bundler.get_or_build_single_chapter(
                source_id=source_id,
                story_slug=book_slug,
                chap_order=chap_order,
            )
            return FileResponse(
                path=file_path,
                media_type="application/epub+zip",
                filename=artifact_name,
                headers={"X-KOSync-SHA1": sha1_hash},
            )
        except Exception as e:
            logger.error(f"Failed to build chapter {chap_order} for {source_id}:{book_slug}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build chapter EPUB: {e}")

    raise HTTPException(
        status_code=400,
        detail=f"Invalid artifact filename '{artifact_name}'. Expected format: ztruyen_source_slug_v01.epub",
    )
