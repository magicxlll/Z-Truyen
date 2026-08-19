"""Pytest global configuration and fixtures."""

import pytest
from app.cache.fast_cache import fast_cache
from app.sources.registry import registry, create_default_registry


@pytest.fixture(autouse=True)
def reset_cache_and_registry():
    """Ensure every test has a clean in-memory cache and fresh default source registry."""
    fast_cache.clear()
    default_reg = create_default_registry()
    registry._adapters = default_reg._adapters
    yield
    fast_cache.clear()
