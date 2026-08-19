"""High-performance in-memory TTL cache for instantaneous OPDS feeds and API responses."""

from __future__ import annotations

import time
import asyncio
from typing import Any, Callable, Coroutine


class CacheEntry:
    __slots__ = ("value", "expires_at")

    def __init__(self, value: Any, expires_at: float) -> None:
        self.value = value
        self.expires_at = expires_at

    @property
    def is_expired(self) -> bool:
        return time.monotonic() > self.expires_at


class FastCache:
    """Async-safe in-memory cache with Time-To-Live (TTL) expiration."""

    def __init__(self, default_ttl: int = 300) -> None:
        self.default_ttl = default_ttl
        self._store: dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    def get(self, key: str) -> Any | None:
        """Get cached value if present and unexpired, else None."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.is_expired:
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Set cached value with TTL in seconds."""
        duration = ttl if ttl is not None else self.default_ttl
        expires_at = time.monotonic() + duration
        self._store[key] = CacheEntry(value, expires_at)

    def delete(self, key: str) -> None:
        """Remove a single key from cache."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()

    async def get_or_set(
        self,
        key: str,
        coro_func: Callable[[], Coroutine[Any, Any, Any]],
        ttl: int | None = None,
    ) -> Any:
        """Get cached value, or execute async coroutine, cache and return result."""
        cached = self.get(key)
        if cached is not None:
            return cached

        async with self._lock:
            # Double-check after acquiring lock
            cached = self.get(key)
            if cached is not None:
                return cached

            val = await coro_func()
            self.set(key, val, ttl)
            return val


# Global FastCache instance
fast_cache = FastCache(default_ttl=300)  # 5 minutes default
