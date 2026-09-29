"""Unit tests for the SearXNG engine (HTTP mocked)."""
import pytest

from sourceai.search.engines.searxng import SearXNGEngine


class _FakeResponse:
    def __init__(self, status=200, json_data=None, text=""):
        self.status = status
        self._json = json_data
        self._text = text

    async def json(self, content_type=None):
        return self._json

    async def text(self):
        return self._text

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeSession:
    def __init__(self, response):
        self._response = response
        self.last_get_url = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def get(self, url, **kw):
        self.last_get_url = url
        return self._response


def _patch_session(monkeypatch, response):
    holder = {}

    def factory(*a, **kw):
        s = _FakeSession(response)
        holder["session"] = s
        return s

    monkeypatch.setattr("aiohttp.ClientSession", factory)
    return holder


@pytest.mark.asyncio
async def test_searxng_parses_results(monkeypatch):
    payload = {
        "results": [
            {"title": "Acme", "url": "https://acme.example", "content": "We make things"},
            {"title": "Beta", "url": "https://beta.example", "content": "Another"},
        ]
    }
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data=payload))
    engine = SearXNGEngine(base_url="http://localhost:8080")
    results = await engine.search("widgets", limit=10)

    assert [r.title for r in results] == ["Acme", "Beta"]
    assert results[0].url == "https://acme.example"
    assert results[0].source_engine == "searxng"
    assert results[0].rank == 1
    assert results[1].rank == 2


@pytest.mark.asyncio
async def test_searxng_respects_limit(monkeypatch):
    payload = {"results": [
        {"title": f"r{i}", "url": f"https://e{i}.example", "content": ""}
        for i in range(20)
    ]}
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data=payload))
    engine = SearXNGEngine()
    results = await engine.search("x", limit=3)
    assert len(results) == 3


@pytest.mark.asyncio
async def test_searxng_empty_results(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data={"results": []}))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_missing_results_key(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data={"foo": "bar"}))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_malformed_json_object(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data=[]))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_skips_results_without_url(monkeypatch):
    payload = {"results": [
        {"title": "no url", "content": ""},
        {"title": "ok", "url": "https://ok.example", "content": "fine"},
        {"title": "not a dict"},          # will be filtered by isinstance check
        "not a dict at all",
    ]}
    _patch_session(monkeypatch, _FakeResponse(status=200, json_data=payload))
    engine = SearXNGEngine()
    results = await engine.search("x", limit=5)
    assert len(results) == 1
    assert results[0].url == "https://ok.example"


@pytest.mark.asyncio
async def test_searxng_http_500_returns_empty(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=500))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_http_429_returns_empty(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=429))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_http_503_returns_empty(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=503))
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_connection_error_returns_empty(monkeypatch):
    import aiohttp

    def factory(*a, **kw):
        raise aiohttp.ClientError("connection refused")

    monkeypatch.setattr("aiohttp.ClientSession", factory)
    engine = SearXNGEngine()
    assert await engine.search("x", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_empty_query(monkeypatch):
    engine = SearXNGEngine()
    assert await engine.search("", limit=5) == []
    assert await engine.search("   ", limit=5) == []


@pytest.mark.asyncio
async def test_searxng_url_encoded_query(monkeypatch):
    holder = _patch_session(
        monkeypatch,
        _FakeResponse(status=200, json_data={"results": []}),
    )
    engine = SearXNGEngine(base_url="http://localhost:8080")
    await engine.search("BLDC motor manufacturer India", limit=5)

    session = holder["session"]
    assert session.last_get_url is not None
    # spaces must be URL-encoded
    assert " " not in session.last_get_url
    assert "format=json" in session.last_get_url
    assert "BLDC" in session.last_get_url


@pytest.mark.asyncio
async def test_searxng_health_check_ok(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=200))
    engine = SearXNGEngine()
    assert await engine.health_check() is True


@pytest.mark.asyncio
async def test_searxng_health_check_down(monkeypatch):
    _patch_session(monkeypatch, _FakeResponse(status=503))
    engine = SearXNGEngine()
    assert await engine.health_check() is False


@pytest.mark.asyncio
async def test_searxng_health_check_connection_error(monkeypatch):
    import aiohttp

    def factory(*a, **kw):
        raise aiohttp.ClientError("no route")

    monkeypatch.setattr("aiohttp.ClientSession", factory)
    engine = SearXNGEngine()
    assert await engine.health_check() is False


def test_searxng_engine_name():
    assert SearXNGEngine.name == "searxng"


def test_searxng_constructor_strips_trailing_slash():
    engine = SearXNGEngine(base_url="http://localhost:8080/")
    assert engine.base_url == "http://localhost:8080"