"""Search router: dispatch queries to multiple engines with health-aware fallback."""
import asyncio
import logging
from typing import Dict, List, Optional
from urllib.parse import urlparse

from .engines.base import SearchResult
from .engines.duckduckgo import DuckDuckGoEngine
from .engines.google import GoogleEngine
from .engines.bing import BingEngine
from .engines.yacy import YaCyEngine
from .engines.whoogle import WhoogleEngine
from .engines.searxng import SearXNGEngine

logger = logging.getLogger(__name__)


ENGINE_WEIGHTS = {
    "google": 10.0,
    "bing": 8.0,
    "duckduckgo": 7.0,
    "searxng": 7.5,
    "whoogle": 6.0,
    "yacy": 5.0,
}


class SearchRouter:
    """Dispatch queries to multiple engines in parallel, with fallback."""

    def __init__(self, engines: Optional[List] = None):
        if engines is None:
            engines = [
                DuckDuckGoEngine(),
                GoogleEngine(),
                BingEngine(),
                YaCyEngine(),
                WhoogleEngine(),
            ]

            # Optional: register SearXNG only when explicitly enabled.
            # Import settings lazily so tests that pass an explicit
            # `engines=[...]` list never touch configuration.
            from sourceai.config.settings import settings
            if getattr(settings, "SEARXNG_ENABLED", False):
                engines.append(SearXNGEngine(
                    base_url=settings.SEARXNG_BASE_URL,
                    timeout=float(settings.SEARXNG_TIMEOUT),
                ))

        self.engines = engines

    async def search(
        self,
        query: str,
        limit: int = 10,
        timeout_seconds: float = 20.0,
        only_healthy: bool = False,
    ) -> List[SearchResult]:
        if not query or not query.strip():
            return []

        candidates = list(self.engines)
        if only_healthy:
            healthy = []
            for e in candidates:
                try:
                    if await e.health_check():
                        healthy.append(e)
                except Exception:
                    pass
            if healthy:
                candidates = healthy
            else:
                logger.warning("No healthy engines; falling back to all")

        if not candidates:
            return []

        tasks = [self._one(e, query, limit, timeout_seconds) for e in candidates]
        raw = await asyncio.gather(*tasks, return_exceptions=True)

        flat: List[SearchResult] = []
        for engine, res in zip(candidates, raw):
            if isinstance(res, Exception):
                logger.warning("engine %s failed: %s", engine.name, res)
                continue
            if isinstance(res, list):
                flat.extend(res)

        deduped = self._deduplicate(flat)
        ranked = self._rank(deduped, query)
        return ranked[: max(limit, 10) * 2]

    async def engine_status(self) -> Dict[str, bool]:
        """Return engine name -> healthy bool (cached per engine)."""
        status: Dict[str, bool] = {}
        for e in self.engines:
            try:
                status[e.name] = await e.health_check()
            except Exception:
                status[e.name] = False
        return status

    # -------- internals --------

    async def _one(self, engine, query: str, limit: int, timeout: float) -> List[SearchResult]:
        try:
            return await asyncio.wait_for(engine.search(query, limit), timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("engine %s timed out after %.1fs", engine.name, timeout)
            return []
        except Exception as e:
            logger.warning("engine %s error: %s", engine.name, e)
            return []

    @staticmethod
    def _canonical_url(url: str) -> str:
        if not url:
            return ""
        try:
            p = urlparse(url)
            netloc = p.netloc.lower()
            path = (p.path or "/").rstrip("/") or "/"
            return f"{p.scheme.lower()}://{netloc}{path}"
        except Exception:
            return url

    def _deduplicate(self, results: List[SearchResult]) -> List[SearchResult]:
        seen = set()
        out: List[SearchResult] = []
        for r in results:
            key = self._canonical_url(r.url)
            if key and key not in seen:
                seen.add(key)
                out.append(r)
        return out

    def _rank(self, results: List[SearchResult], query: str) -> List[SearchResult]:
        if not results:
            return results
        terms = set(query.lower().split())
        scored = []
        for r in results:
            score = 0.0
            title_words = set((r.title or "").lower().split())
            snippet_words = set((r.snippet or "").lower().split())
            score += 2.0 * len(terms & title_words)
            score += 1.0 * len(terms & snippet_words)
            score += ENGINE_WEIGHTS.get(r.source_engine, 1.0)
            if r.rank > 0:
                score += max(0.0, 5.0 - r.rank) * 0.5
            if r.domain:
                if r.domain.endswith((".com", ".org", ".net")):
                    score += 1.0
                elif r.domain.endswith((".in", ".co.in")):
                    score += 0.5
            scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [r for _, r in scored]