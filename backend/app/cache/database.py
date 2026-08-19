"""SQLite database connection and schema initialization with WAL mode."""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.config import settings
from app.logging import logger

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sources (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    adapter_type TEXT NOT NULL,
    supports_login INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS stories (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    slug TEXT NOT NULL,
    title TEXT NOT NULL,
    author TEXT DEFAULT 'Đang cập nhật',
    description TEXT DEFAULT '',
    cover_url TEXT,
    status TEXT DEFAULT 'Đang cập nhật',
    genres_json TEXT DEFAULT '[]',
    total_chapters INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_stories_source_slug ON stories (source_id, slug);

CREATE TABLE IF NOT EXISTS chapters (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    order_num INTEGER NOT NULL,
    title TEXT NOT NULL,
    original_url TEXT NOT NULL,
    content_clean TEXT DEFAULT '',
    is_vip INTEGER NOT NULL DEFAULT 0,
    scraped_at TEXT NOT NULL,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_chapters_story_order ON chapters (story_id, order_num);

CREATE TABLE IF NOT EXISTS volume_bundles (
    id TEXT PRIMARY KEY,
    story_id TEXT NOT NULL,
    vol_index INTEGER NOT NULL,
    start_order INTEGER NOT NULL,
    end_order INTEGER NOT NULL,
    chapter_count INTEGER NOT NULL,
    filename TEXT NOT NULL,
    sha1_hash TEXT NOT NULL,
    file_size_bytes INTEGER NOT NULL,
    built_at TEXT NOT NULL,
    FOREIGN KEY (story_id) REFERENCES stories(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_volume_bundles_story ON volume_bundles (story_id, vol_index);

CREATE TABLE IF NOT EXISTS source_credentials (
    source_id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    password_encrypted TEXT NOT NULL,
    session_cookies_json TEXT,
    last_login_at TEXT,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS cache_entries (
    key TEXT PRIMARY KEY,
    file_path TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    last_accessed_at TEXT NOT NULL
);
"""


def get_db_path() -> Path:
    """Return resolved SQLite database path."""
    settings.ensure_directories()
    return settings.db_path


def init_db(db_path: Path | None = None) -> None:
    """Initialize database tables and set WAL journal mode."""
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(target_path) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=NORMAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.executescript(SCHEMA_SQL)
        conn.commit()

    logger.info(f"Initialized SQLite database at {target_path} in WAL mode.")


_initialized_db_paths: set[str] = set()


def ensure_db_initialized(target_path: Path) -> None:
    """Ensure database tables exist at target path."""
    path_key = str(target_path.resolve())
    if path_key not in _initialized_db_paths:
        init_db(target_path)
        _initialized_db_paths.add(path_key)


@contextmanager
def get_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Provide a contextual transactional SQLite connection."""
    target_path = db_path or get_db_path()
    ensure_db_initialized(target_path)
    conn = sqlite3.connect(target_path, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
