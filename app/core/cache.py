import time
from typing import Any

from app.config import settings


class TTLCache:
    """Cache en memoria por proceso. El TTL garantiza convergencia
    si se escala a varios workers."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        item = self._data.get(key)
        if item is None:
            return None
        expires, value = item
        if time.monotonic() > expires:
            self._data.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any) -> None:
        self._data[key] = (time.monotonic() + self._ttl, value)

    def invalidate(self, key: str) -> None:
        self._data.pop(key, None)

    def clear(self) -> None:
        self._data.clear()


tenant_cache = TTLCache(settings.tenant_cache_ttl)
