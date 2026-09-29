# sourceai/search/engines/duckduckgo.py
import asyncio
import logging
from typing import List
from .base import SearchEngine, SearchResult

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

logger = logging.getLogger(__name__)


class DuckDuckGoEngine(SearchEngine):
    async def _search(self, query: str, limit: int = 10) -> List[SearchResult]:
        if not DDGS_AVAILABLE:
            logger.warning("ddgs not installed; returning empty")
            return []

        def _sync():
            with DDGS() as ddgs:
                return list(ddgs.text(query, max_results=limit))

        try:
            raw = await asyncio.to_thread(_sync)
        except Exception as e:
            logger.warning(f"DDG search failed: {e}")
            return []

        out: List[SearchResult] = []
        for i, r in enumerate(raw, start=1):
            url = r.get("href") or r.get("url") or r.get("link", "")
            if not url:
                continue
            out.append(SearchResult(
                title=r.get("title", ""),
                url=url,
                snippet=r.get("body") or r.get("snippet", ""),
                source_engine="duckduckgo",
                query=query,
                rank=i,
            ))
        logger.info(f"DDG returned {len(out)} results for '{query}'")
        return out

    async def _health_check(self) -> bool:
        try:
            results = await self._search("test", limit=1)
            return bool(results)
        except Exception:
            return False

    async def search(self, query: str, limit: int = 10) -> List[SearchResult]:
        return await self._search(query, limit)

    async def health_check(self) -> bool:
        return await self._health_check()