"""Unit tests for search engines (HTTP mocked)."""
import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from sourceai.search.engines.base import SearchResult, SearchEngine
from sourceai.search.engines.duckduckgo import DuckDuckGoEngine
from sourceai.search.engines.yacy import YaCyEngine
from sourceai.search.engines.whoogle import WhoogleEngine


def test_search_result_timestamp_is_tz_aware_utc():
    r = SearchResult(title="a", url="https://a.com", snippet="", source_engine="x", query="q")
    assert r.discovered_at.tzinfo is not None
    assert r.discovered_at.utcoffset() == timedelta(0)
    # Sanity: timestamp is close to now (within 5 seconds)
    delta = abs((datetime.now(timezone.utc) - r.discovered_at).total_seconds())
    assert delta < 5.0


def test_search_result_uses_fresh_default_factory():
    """Proves `discovered_at` uses default_factory, not a shared mutable default."""
    a = SearchResult(title="a", url="https://a.com", snippet="", source_engine="x", query="q")
    # Force a measurable gap
    import time
    time.sleep(0.01)
    b = SearchResult(title="b", url="https://b.com", snippet="", source_engine="x", query="q")
    assert b.discovered_at > a.discovered_at
    assert (b.discovered_at - a.discovered_at).total_seconds() >= 0.005


def test_search_result_domain_extraction():
    a = SearchResult(title="a", url="https://Sub.Example.COM/path", snippet="", source_engine="x", query="q")
    b = SearchResult(title="b", url="https://other.org/", snippet="", source_engine="x", query="q")
    assert a.domain == "sub.example.com"
    assert b.domain == "other.org"


# ---------------------------------------------------------------------------
# DuckDuckGo
#
# The engine uses the `ddgs` library (DDG blocks direct HTML scraping for
# automated clients). Tests mock the DDGS class, not aiohttp, because the
# engine no longer performs its own HTTP.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_duckduckgo_maps_ddgs_results(monkeypatch):
    from sourceai.search.engines import duckduckgo as ddg_mod

    fake_rows = [
        {"title": "Foo Bar", "href": "https://foo.com/bar",
         "body": "A snippet about foo"},
        {"title": "Baz", "href": "https://baz.com/",
         "body": "Another snippet"},
    ]

    class _FakeDDGS:
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False
        def text(self, query, max_results=10):
            return fake_rows[:max_results]

    monkeypatch.setattr(ddg_mod, "DDGS", _FakeDDGS)
    monkeypatch.setattr(ddg_mod, "DDGS_AVAILABLE", True)

    engine = ddg_mod.DuckDuckGoEngine()
    results = await engine.search("foo", limit=5)

    assert len(results) == 2
    assert results[0].title == "Foo Bar"
    assert results[0].url == "https://foo.com/bar"
    assert results[0].source_engine == "duckduckgo"
    assert results[0].rank == 1
    assert results[1].url == "https://baz.com/"
    assert results[1].rank == 2


@pytest.mark.asyncio
async def test_duckduckgo_skips_results_without_url(monkeypatch):
    from sourceai.search.engines import duckduckgo as ddg_mod

    fake_rows = [
        {"title": "No URL", "body": "..."},                    # skipped
        {"title": "OK", "href": "https://ok.example", "body": ""},
    ]

    class _FakeDDGS:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def text(self, query, max_results=10):
            return fake_rows

    monkeypatch.setattr(ddg_mod, "DDGS", _FakeDDGS)
    monkeypatch.setattr(ddg_mod, "DDGS_AVAILABLE", True)

    engine = ddg_mod.DuckDuckGoEngine()
    results = await engine.search("x", limit=5)
    assert len(results) == 1
    assert results[0].url == "https://ok.example"


@pytest.mark.asyncio
async def test_duckduckgo_returns_empty_when_library_missing(monkeypatch):
    from sourceai.search.engines import duckduckgo as ddg_mod

    monkeypatch.setattr(ddg_mod, "DDGS_AVAILABLE", False)
    monkeypatch.setattr(ddg_mod, "DDGS", None)

    engine = ddg_mod.DuckDuckGoEngine()
    results = await engine.search("x", limit=5)
    assert results == []


# ---------------------------------------------------------------------------
# Shared HTTP mocking helpers — used by YaCy and Whoogle tests.
# ---------------------------------------------------------------------------


class _FakeResponse:
    def __init__(self, status=200, text="", json_data=None):
        self.status = status
        self._text = text
        self._json = json_data
    async def text(self):
        return self._text
    async def json(self, content_type=None):
        return self._json
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False


class _FakeSession:
    def __init__(self, response):
        self._response = response
    async def __aenter__(self):
        return self
    async def __aexit__(self, *a):
        return False
    def post(self, *a, **kw):
        return self._response
    def get(self, *a, **kw):
        return self._response


@pytest.mark.asyncio
async def test_yacy_parses_json(monkeypatch):
    payload = {"channels": [{"items": [
        {"title": "ACME", "link": "https://acme.example", "description": "We make things"},
        {"title": "Beta Co", "link": "https://beta.example", "description": "Another"},
    ]}]}
    engine = YaCyEngine()
    resp = _FakeResponse(status=200, json_data=payload)
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **kw: _FakeSession(resp))

    results = await engine.search("widgets", limit=10)
    assert [r.title for r in results] == ["ACME", "Beta Co"]
    assert results[0].url == "https://acme.example"


@pytest.mark.asyncio
async def test_yacy_handles_empty_response(monkeypatch):
    engine = YaCyEngine()
    resp = _FakeResponse(status=200, json_data={"channels": []})
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **kw: _FakeSession(resp))
    results = await engine.search("x", limit=5)
    assert results == []


@pytest.mark.asyncio
async def test_whoogle_offline_returns_empty(monkeypatch):
    engine = WhoogleEngine(base_url="http://localhost:5000")
    resp = _FakeResponse(status=503)
    monkeypatch.setattr("aiohttp.ClientSession", lambda *a, **kw: _FakeSession(resp))
    results = await engine.search("x", limit=5)
    assert results == []


@pytest.mark.asyncio
async def test_engine_health_check_cache():
    class Dummy(SearchEngine):
        name = "dummy"
        def __init__(self):
            super().__init__()
            self.calls = 0
        async def _search(self, query, limit):
            return []
        async def _health_check(self):
            self.calls += 1
            return True

    d = Dummy()
    assert await d.health_check() is True
    assert await d.health_check() is True
    assert d.calls == 1