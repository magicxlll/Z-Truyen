"""Configuration settings for Z-Truyen Backend."""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server settings
    APP_NAME: str = "Z-Truyen X3 Backend"
    APP_VERSION: str = "1.0.0"
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = False

    # Base directory and storage paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = Path(os.getenv("ZTRUYEN_DATA_DIR", str(Path(__file__).resolve().parent.parent / "data")))

    # Scraper & Volume bundling parameters
    CHAPTERS_PER_VOLUME: int = 50
    REQUEST_TIMEOUT_SECONDS: float = 15.0
    FAST_SCRAPE_CONCURRENCY: int = 5
    ENABLE_PLAYWRIGHT_FALLBACK: bool = True

    # VIP Source Credentials
    AKAY_USERNAME: str | None = None
    AKAY_PASSWORD: str | None = None

    @property
    def db_path(self) -> Path:
        """Path to SQLite database file."""
        return self.DATA_DIR / "ztruyen.db"

    @property
    def cache_dir(self) -> Path:
        """Path to main cache directory."""
        return self.DATA_DIR / "cache"

    @property
    def epub_cache_dir(self) -> Path:
        """Path to generated EPUB files storage."""
        return self.cache_dir / "epubs"

    @property
    def cover_cache_dir(self) -> Path:
        """Path to cached book covers."""
        return self.cache_dir / "covers"

    def ensure_directories(self) -> None:
        """Create necessary storage directories if they do not exist."""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.epub_cache_dir.mkdir(parents=True, exist_ok=True)
        self.cover_cache_dir.mkdir(parents=True, exist_ok=True)


settings = Settings()
