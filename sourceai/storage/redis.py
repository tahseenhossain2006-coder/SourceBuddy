# sourceai/storage/redis.py
"""
Redis-backed cache with in-process fallback.

If Redis is unavailable at connect time or during an operation, every
method degrades to a no-op / in-process dict. Callers never see a
Redis-specific exception.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Optional

logger = logging.getLogger(__name__)


class _InProcessCache:
    """Simple TTL dict — used when Redis is unavailable."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        entry = self._data.get(key)
        if not entry:
            return None
        expires_at, value = entry
        if expires_at and expires_at < time.time():
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        self._data[key] = (time.time() + ttl, value)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)


class RedisCache:
    """
    Cache facade.

    Tries Redis first. On connect failure or per-op error, degrades to an
    in-process dict for the lifetime of the process. Every method is safe
    to call when Redis is down.
    """

    def __init__(self) -> None:
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._fallback = _InProcessCache()
        self._checked = False
        self._available = False

    async def connect(self) -> None:
        """Attempt to connect. Failure is logged, not raised."""
        try:
            import redis.asyncio as redis_asyncio
            self.redis = await redis_asyncio.from_url(
                self.redis_url, encoding="utf-8", decode_responses=True
            )
            await self.redis.ping()
            self._available = True
            logger.info("RedisCache: connected")
        except Exception as exc:
            self.redis = None
            self._available = False
            logger.warning(
                "RedisCache: Redis unavailable (%s); using in-process fallback",
                exc,
            )
        finally:
            self._checked = True

    async def _ensure(self) -> None:
        if not self._checked:
            await self.connect()

    # ------------------------------------------------------------------
    async def get(self, key: str) -> Optional[Any]:
        await self._ensure()
        if self._available and self.redis is not None:
            try:
                data = await self.redis.get(key)
                if data:
                    return json.loads(data)
                return None
            except Exception as exc:
                logger.warning("RedisCache.get failed (%s); falling back", exc)
                self._available = False
                self.redis = None
        return self._fallback.get(key)

    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        await self._ensure()
        if self._available and self.redis is not None:
            try:
                await self.redis.set(key, json.dumps(value, default=str), ex=ttl)
                return
            except Exception as exc:
                logger.warning("RedisCache.set failed (%s); falling back", exc)
                self._available = False
                self.redis = None
        self._fallback.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        await self._ensure()
        if self._available and self.redis is not None:
            try:
                await self.redis.delete(key)
                return
            except Exception as exc:
                logger.warning("RedisCache.delete failed (%s); falling back", exc)
                self._available = False
                self.redis = None
        self._fallback.delete(key)

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a counter. Falls back to in-process on error."""
        await self._ensure()
        if self._available and self.redis is not None:
            try:
                return await self.redis.incr(key, amount)
            except Exception as exc:
                logger.warning("RedisCache.incr failed (%s); falling back", exc)
                self._available = False
                self.redis = None
        # Fallback: read-modify-write on the in-process dict
        current = self._fallback.get(key) or 0
        if not isinstance(current, int):
            current = 0
        new_value = current + amount
        self._fallback.set(key, new_value, ttl=3600)
        return new_value

    async def expire(self, key: str, ttl: int) -> None:
        await self._ensure()
        if self._available and self.redis is not None:
            try:
                await self.redis.expire(key, ttl)
                return
            except Exception as exc:
                logger.warning("RedisCache.expire failed (%s); falling back", exc)
                self._available = False
                self.redis = None
        # Fallback: re-set with new TTL
        value = self._fallback.get(key)
        if value is not None:
            self._fallback.set(key, value, ttl)

    async def close(self) -> None:
        if self.redis is not None:
            try:
                await self.redis.aclose()
            except Exception:
                pass
            self.redis = None
            self._available = False