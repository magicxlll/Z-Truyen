"""Structured logging configuration for Z-Truyen Backend."""

import logging
import sys
from typing import Any


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure structured console logging for the application."""
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger("ztruyen")
    root_logger.setLevel(level)

    # Avoid duplicate handlers if setup is called multiple times
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    return root_logger


logger = setup_logging()


def log_scraper_event(source: str, action: str, details: dict[str, Any] | None = None) -> None:
    """Log scraper lifecycle events with contextual details."""
    detail_str = f" | {details}" if details else ""
    logger.info(f"[Scraper:{source}] {action}{detail_str}")


def log_epub_event(artifact_name: str, action: str, duration_sec: float | None = None) -> None:
    """Log EPUB generation and caching events."""
    dur_str = f" (took {duration_sec:.2f}s)" if duration_sec is not None else ""
    logger.info(f"[EPUB:{artifact_name}] {action}{dur_str}")
