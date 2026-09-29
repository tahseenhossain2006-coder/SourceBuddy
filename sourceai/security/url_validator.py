# sourceai/security/url_validator.py
"""
SSRF protection for outbound URL fetches.

Rejects:
  * non-HTTP(S) schemes
  * loopback (127.0.0.0/8, ::1)
  * private ranges (10/8, 172.16/12, 192.168/16)
  * link-local (169.254.0.0/16, fe80::/10) — includes cloud metadata
  * CGNAT (100.64.0.0/10)
  * documentation / reserved / multicast / broadcast
  * IPv6 private ranges (fc00::/7)
  * hostnames that resolve to any of the above
"""
from __future__ import annotations

import ipaddress
import logging
import socket
from typing import Optional
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Ranges that must never be reachable from a user-supplied URL.
# ---------------------------------------------------------------------------
BLOCKED_IPV4_NETWORKS = [
    ipaddress.ip_network("0.0.0.0/8"),          # "this network"
    ipaddress.ip_network("10.0.0.0/8"),         # RFC 1918 private
    ipaddress.ip_network("100.64.0.0/10"),      # CGNAT
    ipaddress.ip_network("127.0.0.0/8"),        # loopback
    ipaddress.ip_network("169.254.0.0/16"),     # link-local (AWS/GCP metadata)
    ipaddress.ip_network("172.16.0.0/12"),      # RFC 1918 private
    ipaddress.ip_network("192.0.0.0/24"),       # IETF protocol assignments
    ipaddress.ip_network("192.0.2.0/24"),       # TEST-NET-1
    ipaddress.ip_network("192.88.99.0/24"),     # 6to4 relay anycast
    ipaddress.ip_network("192.168.0.0/16"),     # RFC 1918 private
    ipaddress.ip_network("198.18.0.0/15"),      # benchmarking
    ipaddress.ip_network("198.51.100.0/24"),    # TEST-NET-2
    ipaddress.ip_network("203.0.113.0/24"),     # TEST-NET-3
    ipaddress.ip_network("224.0.0.0/4"),        # multicast
    ipaddress.ip_network("240.0.0.0/4"),        # reserved
    ipaddress.ip_network("255.255.255.255/32"), # broadcast
]

BLOCKED_IPV6_NETWORKS = [
    ipaddress.ip_network("::/128"),          # unspecified
    ipaddress.ip_network("::1/128"),         # loopback
    ipaddress.ip_network("::ffff:0:0/96"),   # IPv4-mapped — handled separately
    ipaddress.ip_network("64:ff9b::/96"),    # IPv4-IPv6 translation
    ipaddress.ip_network("100::/64"),        # discard-only
    ipaddress.ip_network("2001:db8::/32"),   # documentation
    ipaddress.ip_network("fc00::/7"),        # unique local
    ipaddress.ip_network("fe80::/10"),       # link-local
    ipaddress.ip_network("ff00::/8"),        # multicast
]

# Only HTTP and HTTPS are allowed for outbound fetches.
ALLOWED_SCHEMES = {"http", "https"}

# Hostnames that must never be resolved (defence in depth).
BLOCKED_HOSTNAMES = {
    "localhost",
    "ip6-localhost",
    "ip6-loopback",
    "metadata",
    "metadata.google.internal",
    "instance-data",
}


def _is_blocked_ip(ip_str: str) -> bool:
    """Return True if the IP is in any blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True  # malformed — treat as unsafe

    # Unwrap IPv4-mapped IPv6 (::ffff:127.0.0.1) so the IPv4 rules apply.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    if isinstance(ip, ipaddress.IPv4Address):
        return any(ip in net for net in BLOCKED_IPV4_NETWORKS)
    if isinstance(ip, ipaddress.IPv6Address):
        return any(ip in net for net in BLOCKED_IPV6_NETWORKS)
    return True


def _resolve_all_ips(hostname: str) -> list[str]:
    """
    Resolve a hostname to every IP it maps to (IPv4 and IPv6).

    Returns an empty list on failure.
    """
    try:
        infos = socket.getaddrinfo(hostname, None)
    except (socket.gaierror, OSError, UnicodeError):
        return []

    ips: list[str] = []
    seen: set[str] = set()
    for family, _type, _proto, _canon, sockaddr in infos:
        if family == socket.AF_INET:
            ip = sockaddr[0]
        elif family == socket.AF_INET6:
            ip = sockaddr[0]
        else:
            continue
        if ip not in seen:
            seen.add(ip)
            ips.append(ip)
    return ips


def is_safe_url(url: str) -> bool:
    """
    Return True if the URL is safe to fetch from the backend.

    Rejects non-HTTP(S), private/loopback/link-local/reserved IPs (both
    IPv4 and IPv6), and any hostname that resolves to a blocked IP.
    Never raises.
    """
    if not url or not isinstance(url, str):
        return False

    try:
        parsed = urlparse(url)
    except Exception:
        return False

    scheme = (parsed.scheme or "").lower()
    if scheme not in ALLOWED_SCHEMES:
        return False

    host = parsed.hostname
    if not host:
        return False

    host = host.strip().lower().rstrip(".")
    if host in BLOCKED_HOSTNAMES:
        return False

    # Case 1: host is already an IP literal.
    try:
        ip_obj = ipaddress.ip_address(host)
        return not _is_blocked_ip(str(ip_obj))
    except ValueError:
        pass  # not an IP — resolve below

    # Case 2: hostname — resolve and check every returned IP.
    ips = _resolve_all_ips(host)
    if not ips:
        return False

    for ip in ips:
        if _is_blocked_ip(ip):
            logger.debug("SSRF: %s resolves to blocked IP %s", url, ip)
            return False

    return True


def assert_safe_url(url: str) -> None:
    """
    Raise ValueError if the URL is not safe. Use in code that wants
    an explicit failure rather than a boolean.
    """
    if not is_safe_url(url):
        raise ValueError(f"Unsafe URL rejected: {url!r}")


def get_safe_host(url: str) -> Optional[str]:
    """Return the normalized hostname if safe, else None."""
    if not is_safe_url(url):
        return None
    try:
        return urlparse(url).hostname
    except Exception:
        return None