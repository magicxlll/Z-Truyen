"""Metadata repository for SQLite operations on stories, chapters, volumes and credentials."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from app.cache.database import get_connection
from app.domain.models import Source, Story, Chapter, VolumeBundle, SourceCredential
from app.domain.ids import build_story_id, build_chapter_id, build_volume_id


class MetadataRepository:
    """Repository handling CRUD operations against SQLite metadata storage."""

    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path

    # --- Source Operations ---
    def upsert_source(self, source: Source) -> None:
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO sources (id, name, base_url, adapter_type, supports_login, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    base_url=excluded.base_url,
                    adapter_type=excluded.adapter_type,
                    supports_login=excluded.supports_login,
                    enabled=excluded.enabled
                """,
                (
                    source.id,
                    source.name,
                    source.base_url,
                    source.adapter_type,
                    1 if source.supports_login else 0,
                    1 if source.enabled else 0,
                ),
            )

    def get_source(self, source_id: str) -> Source | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM sources WHERE id = ?", (source_id,)).fetchone()
            if not row:
                return None
            return Source(
                id=row["id"],
                name=row["name"],
                base_url=row["base_url"],
                adapter_type=row["adapter_type"],
                supports_login=bool(row["supports_login"]),
                enabled=bool(row["enabled"]),
            )

    def list_sources(self) -> list[Source]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute("SELECT * FROM sources WHERE enabled = 1").fetchall()
            return [
                Source(
                    id=row["id"],
                    name=row["name"],
                    base_url=row["base_url"],
                    adapter_type=row["adapter_type"],
                    supports_login=bool(row["supports_login"]),
                    enabled=bool(row["enabled"]),
                )
                for row in rows
            ]

    # --- Story Operations ---
    def upsert_story(self, story: Story) -> None:
        genres_json = json.dumps(story.genres, ensure_ascii=False)
        updated_at_str = story.updated_at.isoformat()
        with get_connection(self.db_path) as conn:
            # Ensure parent source row exists to satisfy foreign key constraint
            conn.execute(
                """
                INSERT OR IGNORE INTO sources (id, name, base_url, adapter_type, supports_login, enabled)
                VALUES (?, ?, ?, 'custom', 0, 1)
                """,
                (story.source_id, story.source_id, ""),
            )
            conn.execute(
                """
                INSERT INTO stories (
                    id, source_id, slug, title, author, description,
                    cover_url, status, genres_json, total_chapters, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    author=excluded.author,
                    description=excluded.description,
                    cover_url=excluded.cover_url,
                    status=excluded.status,
                    genres_json=excluded.genres_json,
                    total_chapters=excluded.total_chapters,
                    updated_at=excluded.updated_at
                """,
                (
                    story.id,
                    story.source_id,
                    story.slug,
                    story.title,
                    story.author,
                    story.description,
                    story.cover_url,
                    story.status,
                    genres_json,
                    story.total_chapters,
                    updated_at_str,
                ),
            )

    def get_story(self, source_id: str, slug: str) -> Story | None:
        story_id = build_story_id(source_id, slug)
        with get_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,)).fetchone()
            if not row:
                return None
            genres = json.loads(row["genres_json"]) if row["genres_json"] else []
            updated_at = datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
            return Story(
                id=row["id"],
                source_id=row["source_id"],
                slug=row["slug"],
                title=row["title"],
                author=row["author"] or "Đang cập nhật",
                description=row["description"] or "",
                cover_url=row["cover_url"],
                status=row["status"] or "Đang cập nhật",
                genres=genres,
                total_chapters=row["total_chapters"],
                updated_at=updated_at,
            )

    def search_stories(self, query: str, source_id: str | None = None, limit: int = 30) -> list[Story]:
        like_query = f"%{query}%"
        with get_connection(self.db_path) as conn:
            if source_id:
                sql = """
                SELECT * FROM stories
                WHERE source_id = ? AND (title LIKE ? OR author LIKE ? OR description LIKE ?)
                ORDER BY updated_at DESC LIMIT ?
                """
                rows = conn.execute(sql, (source_id, like_query, like_query, like_query, limit)).fetchall()
            else:
                sql = """
                SELECT * FROM stories
                WHERE title LIKE ? OR author LIKE ? OR description LIKE ?
                ORDER BY updated_at DESC LIMIT ?
                """
                rows = conn.execute(sql, (like_query, like_query, like_query, limit)).fetchall()

            results: list[Story] = []
            for row in rows:
                genres = json.loads(row["genres_json"]) if row["genres_json"] else []
                updated_at = datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now()
                results.append(
                    Story(
                        id=row["id"],
                        source_id=row["source_id"],
                        slug=row["slug"],
                        title=row["title"],
                        author=row["author"] or "Đang cập nhật",
                        description=row["description"] or "",
                        cover_url=row["cover_url"],
                        status=row["status"] or "Đang cập nhật",
                        genres=genres,
                        total_chapters=row["total_chapters"],
                        updated_at=updated_at,
                    )
                )
            return results

    # --- Chapter Operations ---
    def upsert_chapter(self, chapter: Chapter) -> None:
        scraped_at_str = chapter.scraped_at.isoformat()
        with get_connection(self.db_path) as conn:
            # Ensure parent story row exists
            source_id = chapter.id.split(":")[0] if ":" in chapter.id else "default"
            conn.execute(
                """
                INSERT OR IGNORE INTO stories (id, source_id, slug, title, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (chapter.story_id, source_id, chapter.story_id, chapter.story_id, scraped_at_str),
            )
            conn.execute(
                """
                INSERT INTO chapters (
                    id, story_id, order_num, title, original_url, content_clean, is_vip, scraped_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    order_num=excluded.order_num,
                    title=excluded.title,
                    original_url=excluded.original_url,
                    content_clean=excluded.content_clean,
                    is_vip=excluded.is_vip,
                    scraped_at=excluded.scraped_at
                """,
                (
                    chapter.id,
                    chapter.story_id,
                    chapter.order_num,
                    chapter.title,
                    chapter.original_url,
                    chapter.content_clean,
                    1 if chapter.is_vip else 0,
                    scraped_at_str,
                ),
            )

    def get_chapter(self, source_id: str, story_slug: str, chap_slug: str) -> Chapter | None:
        chap_id = build_chapter_id(source_id, story_slug, chap_slug)
        with get_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM chapters WHERE id = ?", (chap_id,)).fetchone()
            if not row:
                return None
            scraped_at = datetime.fromisoformat(row["scraped_at"]) if row["scraped_at"] else datetime.now()
            return Chapter(
                id=row["id"],
                story_id=row["story_id"],
                order_num=row["order_num"],
                title=row["title"],
                original_url=row["original_url"],
                content_clean=row["content_clean"],
                is_vip=bool(row["is_vip"]),
                scraped_at=scraped_at,
            )

    def get_chapters_by_range(self, story_id: str, start_order: int, end_order: int) -> list[Chapter]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                """
                SELECT * FROM chapters
                WHERE story_id = ? AND order_num >= ? AND order_num <= ?
                ORDER BY order_num ASC
                """,
                (story_id, start_order, end_order),
            ).fetchall()
            return [
                Chapter(
                    id=row["id"],
                    story_id=row["story_id"],
                    order_num=row["order_num"],
                    title=row["title"],
                    original_url=row["original_url"],
                    content_clean=row["content_clean"],
                    is_vip=bool(row["is_vip"]),
                    scraped_at=datetime.fromisoformat(row["scraped_at"]) if row["scraped_at"] else datetime.now(),
                )
                for row in rows
            ]

    # --- Volume Bundle Operations ---
    def upsert_volume_bundle(self, bundle: VolumeBundle) -> None:
        built_at_str = bundle.built_at.isoformat()
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO volume_bundles (
                    id, story_id, vol_index, start_order, end_order,
                    chapter_count, filename, sha1_hash, file_size_bytes, built_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    start_order=excluded.start_order,
                    end_order=excluded.end_order,
                    chapter_count=excluded.chapter_count,
                    filename=excluded.filename,
                    sha1_hash=excluded.sha1_hash,
                    file_size_bytes=excluded.file_size_bytes,
                    built_at=excluded.built_at
                """,
                (
                    bundle.id,
                    bundle.story_id,
                    bundle.vol_index,
                    bundle.start_order,
                    bundle.end_order,
                    bundle.chapter_count,
                    bundle.filename,
                    bundle.sha1_hash,
                    bundle.file_size_bytes,
                    built_at_str,
                ),
            )

    def get_volume_bundle(self, source_id: str, story_slug: str, vol_index: int) -> VolumeBundle | None:
        bundle_id = build_volume_id(source_id, story_slug, vol_index)
        with get_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM volume_bundles WHERE id = ?", (bundle_id,)).fetchone()
            if not row:
                return None
            built_at = datetime.fromisoformat(row["built_at"]) if row["built_at"] else datetime.now()
            return VolumeBundle(
                id=row["id"],
                story_id=row["story_id"],
                vol_index=row["vol_index"],
                start_order=row["start_order"],
                end_order=row["end_order"],
                chapter_count=row["chapter_count"],
                filename=row["filename"],
                sha1_hash=row["sha1_hash"],
                file_size_bytes=row["file_size_bytes"],
                built_at=built_at,
            )

    def list_volume_bundles(self, story_id: str) -> list[VolumeBundle]:
        with get_connection(self.db_path) as conn:
            rows = conn.execute(
                "SELECT * FROM volume_bundles WHERE story_id = ? ORDER BY vol_index ASC",
                (story_id,),
            ).fetchall()
            return [
                VolumeBundle(
                    id=row["id"],
                    story_id=row["story_id"],
                    vol_index=row["vol_index"],
                    start_order=row["start_order"],
                    end_order=row["end_order"],
                    chapter_count=row["chapter_count"],
                    filename=row["filename"],
                    sha1_hash=row["sha1_hash"],
                    file_size_bytes=row["file_size_bytes"],
                    built_at=datetime.fromisoformat(row["built_at"]) if row["built_at"] else datetime.now(),
                )
                for row in rows
            ]

    # --- Credential Operations ---
    def save_credential(self, cred: SourceCredential) -> None:
        last_login_str = cred.last_login_at.isoformat() if cred.last_login_at else None
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO source_credentials (
                    source_id, username, password_encrypted, session_cookies_json, last_login_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    username=excluded.username,
                    password_encrypted=excluded.password_encrypted,
                    session_cookies_json=excluded.session_cookies_json,
                    last_login_at=excluded.last_login_at
                """,
                (
                    cred.source_id,
                    cred.username,
                    cred.password_encrypted,
                    cred.session_cookies_json,
                    last_login_str,
                ),
            )

    def get_credential(self, source_id: str) -> SourceCredential | None:
        with get_connection(self.db_path) as conn:
            row = conn.execute("SELECT * FROM source_credentials WHERE source_id = ?", (source_id,)).fetchone()
            if not row:
                return None
            last_login = datetime.fromisoformat(row["last_login_at"]) if row["last_login_at"] else None
            return SourceCredential(
                source_id=row["source_id"],
                username=row["username"],
                password_encrypted=row["password_encrypted"],
                session_cookies_json=row["session_cookies_json"],
                last_login_at=last_login,
            )

    # --- Last Read / Continue Reading ---
    def set_last_read(
        self, source_id: str, story_slug: str, story_title: str, chap_order: int = 1
    ) -> None:
        now_str = datetime.now().isoformat()
        with get_connection(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS last_read (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    source_id TEXT NOT NULL,
                    story_slug TEXT NOT NULL,
                    story_title TEXT NOT NULL,
                    chap_order INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                INSERT INTO last_read (id, source_id, story_slug, story_title, chap_order, updated_at)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    source_id=excluded.source_id,
                    story_slug=excluded.story_slug,
                    story_title=excluded.story_title,
                    chap_order=excluded.chap_order,
                    updated_at=excluded.updated_at
                """,
                (source_id, story_slug, story_title, chap_order, now_str),
            )

    def get_last_read(self) -> dict[str, Any] | None:
        with get_connection(self.db_path) as conn:
            try:
                row = conn.execute("SELECT * FROM last_read WHERE id = 1").fetchone()
                if not row:
                    return None
                return {
                    "source_id": row["source_id"],
                    "story_slug": row["story_slug"],
                    "story_title": row["story_title"],
                    "chap_order": row["chap_order"],
                    "updated_at": row["updated_at"],
                }
            except Exception:
                return None


repo = MetadataRepository()
