# sourceai/api/middleware.py
"""
Rate-limit middleware.

Consults the Redis-backed RateLimiter from sourceai.security.rate_limit
on every request. When the limit for a route class is exceeded, returns
429 with a Retry-After header.

When Redis is unavailable, the limiter degrades to in-process (per-worker)
and this middleware continues to function — it just loses cross-worker
coordination.
"""
from __future__ import annotations

import logging
import re

from fastapi import Request
from fastapi.responses import JSONResponse

from sourceai.security.rate_limit import RateLimiter, RATE_LIMITS

logger = logging.getLogger(__name__)

_limiter: RateLimiter | None = None


def _get_limiter() -> RateLimiter:
    global _limiter
    if _limiter is None:
        _limiter = RateLimiter()
    return _limiter


# Route path -> rate-limit key
_PATH_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^/auth/login/?$"),                "auth.login"),
    (re.compile(r"^/auth/register/?$"),             "auth.register"),
    (re.compile(r"^/api/v1/search/?$"),             "search.create"),
    (re.compile(r"^/api/v1/search/[^/]+/?$"),       "search.get"),
    (re.compile(r"^/api/v1/rfqs/?$"),               "rfq.create"),
    (re.compile(r"^/api/v1/watchlists/?$"),         "watchlist.mutate"),
    (re.compile(r"^/api/v1/watchlists/[^/]+/?$"),   "watchlist.mutate"),
    (re.compile(r"^/api/v1/export"),                "export.download"),
]


def _limit_key_for(path: str) -> str | None:
    for pattern, key in _PATH_RULES:
        if pattern.match(path):
            return key
    return None


def _client_id(request: Request) -> str:
    """Identify the caller. Prefer user_id from auth, else remote IP."""
    user_id = getattr(request.state, "user_id", None)
    if user_id:
        return f"user:{user_id}"
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return f"ip:{fwd.split(',')[0].strip()}"
    return f"ip:{request.client.host if request.client else 'unknown'}"


async def rate_limit_middleware(request: Request, call_next):
    """
    ASGI middleware. `request` is a FastAPI Request. Returns Response.
    """
    path = request.url.path
    key = _limit_key_for(path)

    if key is None or key not in RATE_LIMITS:
        return await call_next(request)

    limit, window = RATE_LIMITS[key]
    limiter = _get_limiter()
    bucket_key = f"ratelimit:{key}:{_client_id(request)}"

    try:
        allowed, remaining = await limiter.check(bucket_key, limit, window)
    except Exception:
        # If the limiter itself fails, fail-open. Never block on
        # infrastructure problems.
        logger.exception("Rate limiter failed; allowing request")
        return await call_next(request)

    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Rate limit exceeded", "retry_after": window},
            headers={"Retry-After": str(window)},
        )

    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response
# Append to sourceai/api/middleware.py
from sourceai.observability.logging import new_request_id


async def request_id_middleware(request, call_next):
    rid = request.headers.get("x-request-id") or new_request_id()
    new_request_id()  # set for this context
    request.state.request_id = rid
    response = await call_next(request)
    response.headers["X-Request-ID"] = rid
    return response