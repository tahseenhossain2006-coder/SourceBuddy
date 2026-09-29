"""YaCy search engine (self-hosted, default http://localhost:8090)."""
import logging
from typing import List
from urllib.parse import urlencode

import aiohttp

from .base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class YaCyEngine(SearchEngine):
    name = "yacy"

    def __init__(self, base_url: str = "http://localhost:8090", timeout: float = 10.0):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _search(self, query: str, limit: int) -> List[SearchResult]:
        params = {
            "query": query,
            "maximumRecords": limit,
            "contentDom": "text",
            "resource": "global",
            "nav": "json",
        }
        url = f"{self.base_url}/yacysearch.json?{urlencode(params)}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.info("YaCy returned %s", resp.status)
                    return []
                data = await resp.json(content_type=None)

        channels = data.get("channels") or []
        if not channels:
            return []
        items = channels[0].get("items") or []

        results: List[SearchResult] = []
        for item in items[:limit]:
            title = (item.get("title") or "").strip()
            link = (item.get("link") or "").strip()
            snippet = (item.get("description") or "").strip()
            if title and link:
                results.append(SearchResult(
                    title=title, url=link, snippet=snippet,
                    source_engine=self.name, query=query,
                ))
        return results

    async def _health_check(self) -> bool:
        url = f"{self.base_url}/Status.html"
        timeout = aiohttp.ClientTimeout(total=3.0)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:
            return False