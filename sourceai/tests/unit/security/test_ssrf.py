"""SSRF protection tests for is_safe_url."""
import socket
import pytest

from sourceai.security.url_validator import (
    is_safe_url,
    assert_safe_url,
    get_safe_host,
)


# ---------------------------------------------------------------------------
# Blocked: loopback / localhost
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://localhost",
    "http://localhost/",
    "http://localhost:8080/path",
    "http://LOCALHOST/",
    "http://localhost./",
    "http://127.0.0.1/",
    "http://127.0.0.1:8000/",
    "http://127.1/",
    "http://0.0.0.0/",
    "http://[::1]/",
    "http://[0:0:0:0:0:0:0:1]/",
    "http://ip6-localhost/",
])
def test_ssrf_blocks_loopback(url):
    assert is_safe_url(url) is False


# ---------------------------------------------------------------------------
# Blocked: cloud metadata
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://169.254.169.254/",
    "http://169.254.169.254/latest/meta-data/",
    "http://metadata.google.internal/",
    "http://instance-data/",
])
def test_ssrf_blocks_cloud_metadata(url):
    assert is_safe_url(url) is False


# ---------------------------------------------------------------------------
# Blocked: private RFC 1918 + link-local + reserved
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "http://10.0.0.1/",
    "http://10.255.255.255/",
    "http://172.16.0.1/",
    "http://172.31.255.255/",
    "http://192.168.0.1/",
    "http://192.168.1.1/admin",
    "http://100.64.0.1/",
    "http://198.18.0.1/",
    "http://192.0.2.1/",
    "http://203.0.113.1/",
    "http://224.0.0.1/",
    "http://255.255.255.255/",
    "http://[fc00::1]/",
    "http://[fe80::1]/",
])
def test_ssrf_blocks_private_and_reserved(url):
    assert is_safe_url(url) is False


# ---------------------------------------------------------------------------
# Blocked: bad schemes
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "file:///etc/passwd",
    "ftp://example.com/",
    "gopher://localhost/",
    "dict://localhost:11211/",
    "javascript:alert(1)",
    "data:text/html,<script>",
])
def test_ssrf_blocks_bad_schemes(url):
    assert is_safe_url(url) is False


# ---------------------------------------------------------------------------
# Blocked: malformed
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "",
    "   ",
    "not a url",
    "http://",
    "https://",
    None,
])
def test_ssrf_blocks_malformed(url):
    assert is_safe_url(url) is False


# ---------------------------------------------------------------------------
# Allowed: public URLs
#
# Split into two tests:
#   * IP-literal URLs — no DNS needed
#   * Hostname URLs — DNS mocked so the test is deterministic and does not
#     depend on live network state
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url", [
    "https://1.1.1.1/",   # Cloudflare DNS resolver (public IP)
    "https://8.8.8.8/",   # Google DNS (public IP)
])
def test_ssrf_allows_public_ip_urls(url):
    # Host is already an IP — no DNS resolution involved.
    assert is_safe_url(url) is True


@pytest.mark.parametrize("url,resolved_ip", [
    ("https://example.com", "93.184.216.34"),
    ("https://www.google.com/search?q=test", "142.250.185.78"),
    (
        "https://dir.indiamart.com/impcat/stainless-steel-bottle.html",
        "104.18.20.155",
    ),
    ("https://www.tradeindia.com/", "104.18.20.155"),
    ("http://example.com:8080/path", "93.184.216.34"),
])
def test_ssrf_allows_public_hostnames(monkeypatch, url, resolved_ip):
    """Public hostnames resolving to public IPs must be allowed.

    DNS is mocked so the test does not depend on live network state.
    """
    def fake_getaddrinfo(host, *a, **kw):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (resolved_ip, 0))]

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert is_safe_url(url) is True


# ---------------------------------------------------------------------------
# DNS rebinding: hostname resolving to private IP
# ---------------------------------------------------------------------------

def test_ssrf_blocks_hostname_resolving_to_private_ip(monkeypatch):
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, *args, **kwargs):
        if host == "evil.example":
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 0)),
            ]
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert is_safe_url("http://evil.example/") is False


def test_ssrf_blocks_if_any_resolved_ip_is_private(monkeypatch):
    """Even if one A record is public, a private one must block."""
    real_getaddrinfo = socket.getaddrinfo

    def fake_getaddrinfo(host, *args, **kwargs):
        if host == "mixed.example":
            return [
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 0)),
                (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.1", 0)),
            ]
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", fake_getaddrinfo)
    assert is_safe_url("http://mixed.example/") is False


# ---------------------------------------------------------------------------
# assert_safe_url and get_safe_host
# ---------------------------------------------------------------------------

def test_assert_safe_url_raises_on_unsafe():
    with pytest.raises(ValueError):
        assert_safe_url("http://127.0.0.1/")


def test_assert_safe_url_passes_on_safe():
    assert_safe_url("https://example.com/")  # no raise


def test_get_safe_host_returns_none_for_unsafe():
    assert get_safe_host("http://127.0.0.1/") is None


def test_get_safe_host_returns_host_for_safe():
    assert get_safe_host("https://example.com/path") == "example.com"
