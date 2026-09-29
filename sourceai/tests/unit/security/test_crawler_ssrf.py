"""Crawler security tests: redirect-to-private, oversized response."""
import socket

import pytest

from sourceai.crawling.manager import CrawlManager


# ---------------------------------------------------------------------------
# Fake HTTP layer
# ---------------------------------------------------------------------------

class _FakeContent:
    def __init__(self, chunks):
        self._chunks = chunks

    async def iter_chunked(self, size):
        for c in self._chunks:
            yield c


class _FakeResponse:
    def __init__(self, status=200, headers=None, body_chunks=None):
        self.status = status
        self.headers = headers or {}
        self.content = _FakeContent(body_chunks or [])
        self.url = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False


class _FakeSession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *a):
        return False

    def get(self, url, allow_redirects=True, **kw):
        self.calls.append(url)
        if not self._responses:
            raise AssertionError(f"unexpected GET to {url}")
        return self._responses.pop(0)


def _patch_client_session(monkeypatch, session):
    class _CtxManager:
        async def __aenter__(self_):
            return session

        async def __aexit__(self_, *a):
            return False

    monkeypatch.setattr(
        "aiohttp.ClientSession",
        lambda *a, **kw: _CtxManager(),
    )


def _patch_dns(monkeypatch, hostname, ip):
    """Make `hostname` resolve to `ip` without hitting real DNS."""
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, *a, **kw):
        if host == hostname:
            family = socket.AF_INET6 if ":" in ip else socket.AF_INET
            return [(family, socket.SOCK_STREAM, 6, "", (ip, 0))]
        return real_getaddrinfo(host, *a, **kw)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)


# ---------------------------------------------------------------------------
# Redirect to private / metadata
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawler_refuses_redirect_to_private_ip(monkeypatch):
    _patch_dns(monkeypatch, "public.example", "93.184.216.34")

    resp = _FakeResponse(
        status=302,
        headers={"location": "http://127.0.0.1/"},
    )
    session = _FakeSession([resp])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager()
    results = await crawler.crawl(["https://public.example/page"])

    assert len(results) == 1
    r = results[0]
    assert r.html is None
    assert r.error is not None
    assert "Unsafe redirect" in r.error or "127.0.0.1" in r.error
    assert all("127.0.0.1" not in call for call in session.calls)


@pytest.mark.asyncio
async def test_crawler_refuses_redirect_to_metadata(monkeypatch):
    _patch_dns(monkeypatch, "public.example", "93.184.216.34")

    resp = _FakeResponse(
        status=302,
        headers={"location": "http://169.254.169.254/latest/meta-data/"},
    )
    session = _FakeSession([resp])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager()
    results = await crawler.crawl(["https://public.example/page"])
    assert len(results) == 1
    assert results[0].html is None
    assert results[0].error is not None


# ---------------------------------------------------------------------------
# Oversized response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawler_rejects_oversized_response(monkeypatch):
    _patch_dns(monkeypatch, "example.com", "93.184.216.34")

    chunks = [b"x" * 8192 for _ in range(20)]
    resp = _FakeResponse(
        status=200,
        headers={"content-type": "text/html; charset=utf-8"},
        body_chunks=chunks,
    )
    session = _FakeSession([resp])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager(max_size=10_000, timeout=5, max_concurrent=1)
    results = await crawler.crawl(["https://example.com/big"])

    assert len(results) == 1
    r = results[0]
    assert r.html is None, "oversized response must not return truncated HTML"
    assert r.error is not None
    assert "too large" in r.error.lower()
    assert r.bytes > 10_000


@pytest.mark.asyncio
async def test_crawler_accepts_response_under_cap(monkeypatch):
    _patch_dns(monkeypatch, "example.com", "93.184.216.34")

    chunks = [b"<html><body>" + b"x" * 600 + b"</body></html>"]
    resp = _FakeResponse(
        status=200,
        headers={"content-type": "text/html; charset=utf-8"},
        body_chunks=chunks,
    )
    session = _FakeSession([resp])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager(max_size=1_000_000, timeout=5, max_concurrent=1)

    async def _no_render(url):
        return None
    monkeypatch.setattr(crawler, "_playwright_render", _no_render)

    results = await crawler.crawl(["https://example.com/small"])

    assert len(results) == 1
    assert results[0].html is not None
    assert "<html>" in results[0].html
    assert results[0].error is None


# ---------------------------------------------------------------------------
# Initial URL blocked before any HTTP
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawler_blocks_initial_private_url(monkeypatch):
    session = _FakeSession([])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager()
    results = await crawler.crawl(["http://127.0.0.1/"])
    assert results == []
    assert session.calls == []


@pytest.mark.asyncio
async def test_crawler_blocks_ipv6_loopback_initial(monkeypatch):
    session = _FakeSession([])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager()
    results = await crawler.crawl(["http://[::1]/"])
    assert results == []
    assert session.calls == []


# ---------------------------------------------------------------------------
# Content-type rejection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_crawler_rejects_non_html_content_type(monkeypatch):
    _patch_dns(monkeypatch, "example.com", "93.184.216.34")

    resp = _FakeResponse(
        status=200,
        headers={"content-type": "application/pdf"},
        body_chunks=[b"%PDF-1.4"],
    )
    session = _FakeSession([resp])
    _patch_client_session(monkeypatch, session)

    crawler = CrawlManager()
    results = await crawler.crawl(["https://example.com/doc.pdf"])
    assert len(results) == 1
    assert results[0].html is None
    assert results[0].error == "Unsupported content type"