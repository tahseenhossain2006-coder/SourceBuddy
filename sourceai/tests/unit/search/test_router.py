"""Unit tests for SearchRouter."""
import asyncio
import pytest

from sourceai.search.engines.base import SearchEngine, SearchResult
from sourceai.search.router import SearchRouter


class StubEngine(SearchEngine):
    def __init__(self, name, results=None, healthy=True, delay=0.0):
        super().__init__()
        self.name = name
        self._results = results or []
        self._healthy = healthy
        self._delay = delay
        self.calls = 0

    async def _search(self, query, limit):
        self.calls += 1
        if self._delay:
            await asyncio.sleep(self._delay)
        return [SearchResult(
            title=r["title"], url=r["url"], snippet=r.get("snippet", ""),
            source_engine=self.name, query=query,
        ) for r in self._results]

    async def _health_check(self):
        return self._healthy


@pytest.mark.asyncio
async def test_router_aggregates_multiple_engines():
    e1 = StubEngine("duckduckgo", [{"title": "A", "url": "https://a.com"}])
    e2 = StubEngine("bing", [{"title": "B", "url": "https://b.com"}])
    router = SearchRouter(engines=[e1, e2])
    results = await router.search("x", limit=5)
    urls = {r.url for r in results}
    assert "https://a.com" in urls
    assert "https://b.com" in urls


@pytest.mark.asyncio
async def test_router_deduplicates_canonical_urls():
    e1 = StubEngine("duckduckgo", [{"title": "A", "url": "https://a.com/x"}])
    e2 = StubEngine("bing", [{"title": "A2", "url": "https://A.com/x/#frag"}])
    router = SearchRouter(engines=[e1, e2])
    results = await router.search("x", limit=5)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_router_timeout_does_not_crash():
    slow = StubEngine("google", [{"title": "slow", "url": "https://slow.com"}], delay=2.0)
    fast = StubEngine("bing", [{"title": "fast", "url": "https://fast.com"}])
    router = SearchRouter(engines=[slow, fast])
    results = await router.search("x", limit=5, timeout_seconds=0.2)
    urls = {r.url for r in results}
    assert "https://fast.com" in urls
    assert "https://slow.com" not in urls


@pytest.mark.asyncio
async def test_router_only_healthy_skips_unhealthy():
    bad = StubEngine("google", [{"title": "bad", "url": "https://bad.com"}], healthy=False)
    good = StubEngine("bing", [{"title": "good", "url": "https://good.com"}], healthy=True)
    router = SearchRouter(engines=[bad, good])
    results = await router.search("x", limit=5, only_healthy=True)
    urls = {r.url for r in results}
    assert "https://good.com" in urls
    assert "https://bad.com" not in urls
    assert bad.calls == 0


@pytest.mark.asyncio
async def test_router_engine_status():
    e1 = StubEngine("duckduckgo", healthy=True)
    e2 = StubEngine("bing", healthy=False)
    router = SearchRouter(engines=[e1, e2])
    status = await router.engine_status()
    assert status == {"duckduckgo": True, "bing": False}


@pytest.mark.asyncio
async def test_router_ranking_prefers_google_when_ties():
    e_ddg = StubEngine("duckduckgo", [{"title": "cotton shirt", "url": "https://ddg.com"}])
    e_goog = StubEngine("google", [{"title": "cotton shirt", "url": "https://google.com"}])
    router = SearchRouter(engines=[e_ddg, e_goog])
    results = await router.search("cotton shirt", limit=5)
    assert results[0].url == "https://google.com"


@pytest.mark.asyncio
async def test_router_empty_query_returns_empty():
    e = StubEngine("bing", [{"title": "A", "url": "https://a.com"}])
    router = SearchRouter(engines=[e])
    assert await router.search("", limit=5) == []
    assert await router.search("   ", limit=5) == []
    assert e.calls == 0
@pytest.mark.asyncio
async def test_router_includes_searxng_when_enabled(monkeypatch):
    """SearXNGEngine should be registered when SEARXNG_ENABLED=true."""
    from sourceai.config import settings as settings_module
    from sourceai.search import router as router_module

    monkeypatch.setattr(settings_module.settings, "SEARXNG_ENABLED", True)
    monkeypatch.setattr(settings_module.settings, "SEARXNG_BASE_URL", "http://localhost:8080")
    monkeypatch.setattr(settings_module.settings, "SEARXNG_TIMEOUT", 15)

    r = router_module.SearchRouter()
    names = [e.name for e in r.engines]
    assert "searxng" in names


@pytest.mark.asyncio
async def test_router_excludes_searxng_when_disabled(monkeypatch):
    """SearXNGEngine must NOT be registered when SEARXNG_ENABLED=false."""
    from sourceai.config import settings as settings_module
    from sourceai.search import router as router_module

    monkeypatch.setattr(settings_module.settings, "SEARXNG_ENABLED", False)

    r = router_module.SearchRouter()
    names = [e.name for e in r.engines]
    assert "searxng" not in names


@pytest.mark.asyncio
async def test_router_failover_when_searxng_returns_nothing(monkeypatch):
    """SearXNG returns [] when it fails; other engines must still contribute."""
    class _EmptySearxng(SearchEngine):
        name = "searxng"
        async def _search(self, query, limit):
            return []
        async def _health_check(self):
            return False

    searx = _EmptySearxng()
    ddg = StubEngine("duckduckgo", [{"title": "A", "url": "https://a.com"}])
    router = SearchRouter(engines=[searx, ddg])
    results = await router.search("x", limit=5)
    assert any(r.url == "https://a.com" for r in results)    