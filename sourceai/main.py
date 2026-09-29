# sourceai/main.py
"""
Startup validation entry point.

Provides a `validate_startup()` function that checks required and optional
dependencies and returns a structured summary. Called from the FastAPI
lifespan on API startup.

Also exposes a minimal `app` for local smoke-testing:
    uvicorn sourceai.main:app --port 8001
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict

from sourceai.config.settings import settings
from sourceai.storage.postgres import PostgresStorage

logger = logging.getLogger(__name__)


async def _check_postgres() -> Dict[str, Any]:
    """Postgres is required. Returns {status, detail}."""
    try:
        db = PostgresStorage()
        await db.connect()
        row = await db.pool.fetchrow("SELECT 1 AS ok")
        await db.close()
        return {"status": "ok", "detail": f"connected (SELECT 1 -> {row['ok']})"}
    except Exception as exc:
        return {"status": "failed", "detail": str(exc)}


async def _check_redis() -> Dict[str, Any]:
    """Redis is optional. Returns {status, detail}."""
    try:
        import redis.asyncio as redis_asyncio
        client = await redis_asyncio.from_url(
            settings.REDIS_URL, encoding="utf-8", decode_responses=True
        )
        await client.ping()
        await client.aclose()
        return {"status": "ok", "detail": "connected"}
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


async def _check_searxng() -> Dict[str, Any]:
    """SearXNG is optional. Returns {status, detail}."""
    if not getattr(settings, "SEARXNG_ENABLED", False):
        return {"status": "disabled", "detail": "SEARXNG_ENABLED=false"}
    try:
        import aiohttp
        url = settings.SEARXNG_BASE_URL.rstrip("/") + "/"
        timeout = aiohttp.ClientTimeout(total=5.0)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    return {"status": "ok", "detail": f"HTTP 200 from {url}"}
                return {
                    "status": "unavailable",
                    "detail": f"HTTP {resp.status} from {url}",
                }
    except Exception as exc:
        return {"status": "unavailable", "detail": str(exc)}


async def validate_startup() -> Dict[str, Any]:
    """
    Run all startup checks and return a summary.

    Postgres is required — a failure here should abort startup.
    Redis and SearXNG are optional — failures are warnings.
    """
    results = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
        _check_searxng(),
    )
    summary = {
        "database": results[0],
        "redis": results[1],
        "searxng": results[2],
    }

    # Log a structured line
    logger.info(
        "Startup validation: database=%s redis=%s searxng=%s",
        summary["database"]["status"],
        summary["redis"]["status"],
        summary["searxng"]["status"],
    )

    if summary["database"]["status"] != "ok":
        logger.error(
            "Startup validation FAILED: database unavailable (%s)",
            summary["database"]["detail"],
        )
    if summary["redis"]["status"] != "ok":
        logger.warning(
            "Redis unavailable — degradation active: %s",
            summary["redis"]["detail"],
        )
    if summary["searxng"]["status"] == "unavailable":
        logger.warning(
            "SearXNG unavailable — search continues via DuckDuckGo / YaCy: %s",
            summary["searxng"]["detail"],
        )

    return summary


# ---------------------------------------------------------------------------
# Minimal local app — useful for `uvicorn sourceai.main:app` smoke tests.
# The production entry point is sourceai.api.main:app.
# ---------------------------------------------------------------------------

from fastapi import FastAPI  # noqa: E402

app = FastAPI(title="SourceAI (health only)")


@app.get("/")
def root():
    return {"status": "SourceAI API is running"}


@app.get("/health")
async def health():
    summary = await validate_startup()
    return {
        "status": "ok" if summary["database"]["status"] == "ok" else "degraded",
        "checks": summary,
    }
from sourceai.api.middleware import request_id_middleware
app.middleware("http")(request_id_middleware)