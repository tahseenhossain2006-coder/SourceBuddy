"""Whoogle search engine (self-hosted Google proxy).

Whoogle is marked EOL/unreliable. We treat it as optional — if the
configured base URL is not reachable, we return an empty result set
and mark the engine unhealthy. It never blocks the router.
"""
import logging
from typing import List
from urllib.parse import urlencode

import aiohttp
from bs4 import BeautifulSoup

from .base import SearchEngine, SearchResult

logger = logging.getLogger(__name__)


class WhoogleEngine(SearchEngine):
    name = "whoogle"

    def __init__(self, base_url: str = "http://localhost:5000", timeout: float = 10.0):
        super().__init__()
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def _search(self, query: str, limit: int) -> List[SearchResult]:
        url = f"{self.base_url}/search?{urlencode({'q': query})}"
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.info("Whoogle returned %s (likely offline)", resp.status)
                    return []
                html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        results: List[SearchResult] = []
        for node in soup.select("div.g, div.result"):
            a = node.select_one("a[href^='http']")
            if not a:
                continue
            title_el = node.select_one("h3") or a
            title = title_el.get_text(" ", strip=True)
            href = a.get("href")
            snippet_el = node.select_one(".IsZvec, .VwiC3b, .st")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            if title and href:
                results.append(SearchResult(
                    title=title, url=href, snippet=snippet,
                    source_engine=self.name, query=query,
                ))
            if len(results) >= limit:
                break
        return results

    async def _health_check(self) -> bool:
        timeout = aiohttp.ClientTimeout(total=3.0)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.base_url + "/") as resp:
                    return resp.status == 200
        except Exception:
            return False