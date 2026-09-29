"""SearXNG search engine (self-hosted meta-search).

SearXNG aggregates results from many upstream search engines (Google,
Bing, DuckDuckGo, Brave, Mojeek, ...) behind a single HTTP JSON API.
It is self-hosted, requires no API key, and returns results in a
consistent schema regardless of which upstream engine produced them.

Endpoint used:
    GET {base_url}/search?q=<query>&format=json

Configuration (sourceai/config/settings.py):
    SEARXNG_ENABLED     bool, default false
    SEARXNG_BASE_URL    str,  default http://localhost:8080
    SEARXNG_TIMEOUT     int,  default 15
"""
import logging
from typing import List
from urllib.parse import urlencode

import aiohttp

from .base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class SearXNGEngine(SearchEngine):
    name = "searxng"

    def __init__(
        self,
        base_url: str = "http://localhost:8080",
        timeout: float = 15.0,
    ):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _search(self, query: str, limit: int) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        params = {
            "q": query,
            "format": "json",
            "language": "en",
            "safesearch": "1",
        }
        url = f"{self.base_url}/search?{urlencode(params)}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.info(
                            "SearXNG returned HTTP %s for query %r",
                            resp.status, query[:80],
                        )
                        return []
                    try:
                        data = await resp.json(content_type=None)
                    except Exception as exc:
                        logger.warning(
                            "SearXNG returned non-JSON response: %s", exc
                        )
                        return []
        except aiohttp.ClientError as exc:
            logger.info("SearXNG connection error: %s", exc)
            return []
        except Exception as exc:
            logger.warning("SearXNG unexpected error: %s", exc)
            return []

        if not isinstance(data, dict):
            logger.warning("SearXNG JSON is not an object")
            return []

        raw_results = data.get("results")
        if not isinstance(raw_results, list):
            return []

        out: List[SearchResult] = []
        for i, r in enumerate(raw_results, start=1):
            if not isinstance(r, dict):
                continue
            url_val = (r.get("url") or "").strip()
            if not url_val:
                continue
            title = (r.get("title") or "").strip()
            snippet = (
                r.get("content")
                or r.get("snippet")
                or ""
            ).strip()
            out.append(SearchResult(
                title=title,
                url=url_val,
                snippet=snippet,
                source_engine=self.name,
                query=query,
                rank=i,
            ))
            if len(out) >= limit:
                break

        logger.info(
            "SearXNG returned %d results for %r",
            len(out), query[:80],
        )
        return out

    async def _health_check(self) -> bool:
        url = f"{self.base_url}/"
        timeout = aiohttp.ClientTimeout(total=3.0)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:
            return False