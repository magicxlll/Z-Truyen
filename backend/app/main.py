"""Main entry point for Z-Truyen FastAPI backend."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.logging import logger
from app.cache.database import init_db
from app.api.health import router as health_router
from app.api.opds import router as opds_router
from app.api.search import router as search_router
from app.api.books import router as books_router
from app.api.chapters import router as chapters_router
from app.api.web import router as web_router


from app.fetcher.client import http_client
from app.network import mdns_service


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for startup and shutdown routines."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    settings.ensure_directories()
    init_db()
    logger.info("Database and storage initialized successfully.")
    mdns_service.start()
    yield
    logger.info(f"Stopping {settings.APP_NAME}...")
    mdns_service.stop()
    await http_client.close()


def create_app() -> FastAPI:
    """Factory function for FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="Vietnamese Story Scraper & OPDS 1.2 Feed Provider for Xteink X3 and KOReader",
        lifespan=lifespan,
    )

    # Allow Cross-Origin requests for OPDS readers and web UIs
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Web Testing UI
    app.include_router(web_router)

    # Core healthcheck endpoints
    app.include_router(health_router)

    # OPDS 1.2 catalog and acquisition endpoints
    app.include_router(opds_router)
    app.include_router(search_router)
    app.include_router(books_router)
    app.include_router(chapters_router)

    return app


app = create_app()
