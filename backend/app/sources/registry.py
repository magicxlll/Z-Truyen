"""Source adapter registry and aggregator."""

import asyncio
from app.sources.base import SourceAdapter
from app.sources.storyaclick import StoryaClickAdapter
from app.sources.akaytruyen import AkayTruyenAdapter
from app.sources.conduongbachu import ConDuongBaChuAdapter
from app.domain.models import StorySummary, Source
from app.logging import logger


class SourceRegistry:
    """Registry coordinating multiple story source adapters."""

    def __init__(self) -> None:
        self._adapters: dict[str, SourceAdapter] = {}

    def register(self, adapter: SourceAdapter) -> None:
        """Register a new source adapter."""
        self._adapters[adapter.id] = adapter
        logger.info(f"Registered source adapter: {adapter.name} ({adapter.id})")

    def get(self, source_id: str) -> SourceAdapter | None:
        """Get source adapter by ID."""
        return self._adapters.get(source_id)

    def list_adapters(self) -> list[SourceAdapter]:
        """Return all registered source adapters."""
        return list(self._adapters.values())

    def list_sources_metadata(self) -> list[Source]:
        """Convert registered adapters to domain Source models."""
        return [
            Source(
                id=a.id,
                name=a.name,
                base_url=a.base_url,
                supports_login=a.supports_login,
                enabled=True,
            )
            for a in self._adapters.values()
        ]

    async def search_all(self, query: str, limit_per_source: int = 15) -> list[StorySummary]:
        """Search concurrently across all registered source adapters."""
        tasks = [adapter.search(query) for adapter in self._adapters.values()]
        results_by_source = await asyncio.gather(*tasks, return_exceptions=True)

        combined: list[StorySummary] = []
        for res in results_by_source:
            if isinstance(res, list):
                combined.extend(res[:limit_per_source])
            elif isinstance(res, Exception):
                logger.error(f"Search failed on one of the sources: {res}")

        return combined


def create_default_registry() -> SourceRegistry:
    """Create and initialize registry with default 3 sources."""
    registry = SourceRegistry()
    registry.register(StoryaClickAdapter())
    registry.register(AkayTruyenAdapter())
    registry.register(ConDuongBaChuAdapter())
    return registry


registry = create_default_registry()
