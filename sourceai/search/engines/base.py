"""Base classes for search engines."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urlparse


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source_engine: str
    query: str
    rank: int = 0
    domain: Optional[str] = None
    discovered_at: datetime = field(default_factory=utc_now)

    def __post_init__(self):
        if self.domain is None and self.url:
            try:
                self.domain = urlparse(self.url).netloc.lower() or None
            except Exception:
                self.domain = None


class SearchEngine(ABC):
    """Abstract base class for all search engines.

    Subclasses must define `name` and implement `_search()` and `_health_check()`.
    Public methods `search()` and `health_check()` add caching and error handling.
    """

    name: str = "base"
    health_cache_ttl: float = 60.0  # seconds

    def __init__(self):
        self._last_health_ok: Optional[bool] = None
        self._last_health_time: Optional[datetime] = None

    # -------- public --------

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        if not query or not query.strip():
            return []
        try:
            results = await self._search(query.strip(), limit)
        except Exception:
            return []
        for i, r in enumerate(results, start=1):
            r.source_engine = self.name
            r.rank = i
        return results[:limit]

    async def health_check(self, force: bool = False) -> bool:
        now = utc_now()
        if not force and self._last_health_time is not None:
            age = (now - self._last_health_time).total_seconds()
            if age < self.health_cache_ttl:
                return bool(self._last_health_ok)
        try:
            ok = await self._health_check()
        except Exception:
            ok = False
        self._last_health_ok = ok
        self._last_health_time = now
        return ok

    # -------- must override --------

    @abstractmethod
    async def _search(self, query: str, limit: int) -> List[SearchResult]:
        ...

    @abstractmethod
    async def _health_check(self) -> bool:
        ...