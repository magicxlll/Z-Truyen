"""EPUB file download gateway endpoint for Xteink X3 and KOReader."""

import re
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from app.epub.bundler import volume_bundler
from app.logging import logger

router = APIRouter(prefix="/opds", tags=["OPDS Download Gateway"])


@router.get("/download/{source_id}/{book_slug}/{artifact_name}")
async def download_epub(
    source_id: str,
    book_slug: str,
    artifact_name: str,
    background_tasks: BackgroundTasks,
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
            # Kích hoạt tải ngầm 3 chương tiếp theo & dọn dẹp 5 chương cũ
            background_tasks.add_task(
                volume_bundler.prefetch_and_cleanup,
                source_id,
                book_slug,
                chap_order,
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

    # 3. Check if Custom Range pattern: _range_{start}_{end}.epub or _c{start}-{end}.epub
    range_match = re.search(r"_(?:range_(\d+)_(\d+)|c(\d+)-(\d+))\.epub$", artifact_name, re.IGNORECASE)
    if range_match:
        s_str = range_match.group(1) or range_match.group(3)
        e_str = range_match.group(2) or range_match.group(4)
        start_order = int(s_str)
        end_order = int(e_str)
        try:
            file_path, sha1_hash = await volume_bundler.get_or_build_custom_range(
                source_id=source_id,
                story_slug=book_slug,
                start_order=start_order,
                end_order=end_order,
            )
            return FileResponse(
                path=file_path,
                media_type="application/epub+zip",
                filename=artifact_name,
                headers={"X-KOSync-SHA1": sha1_hash},
            )
        except Exception as e:
            logger.error(f"Failed to build custom range {start_order}-{end_order} for {source_id}:{book_slug}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build range EPUB: {e}")

    # 4. Check if Full Story / All Chapters pattern: _all.epub
    if re.search(r"_all\.epub$", artifact_name, re.IGNORECASE):
        try:
            file_path, sha1_hash = await volume_bundler.get_or_build_custom_range(
                source_id=source_id,
                story_slug=book_slug,
                start_order=1,
                end_order=999999,
            )
            return FileResponse(
                path=file_path,
                media_type="application/epub+zip",
                filename=artifact_name,
                headers={"X-KOSync-SHA1": sha1_hash},
            )
        except Exception as e:
            logger.error(f"Failed to build full story for {source_id}:{book_slug}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to build all chapters EPUB: {e}")

    raise HTTPException(
        status_code=400,
        detail=f"Invalid artifact filename '{artifact_name}'. Expected format: ztruyen_source_slug_v01.epub or _c0001.epub or _c0001-0032.epub",
    )
