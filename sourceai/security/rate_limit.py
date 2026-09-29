# sourceai/security/rate_limit.py
"""
Redis-backed sliding-window rate limiter with in-process fallback.

If Redis is unavailable, the limiter degrades to a per-process dict so the
application keeps working (loses cross-worker coordination but never
crashes because of Redis).
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Optional, Tuple

from sourceai.config.settings import settings

logger = logging.getLogger(__name__)


class _InProcessBackend:
    """
    Minimal fallback when Redis is unavailable.

    Stores a deque of timestamps per key. Prunes on each check.
    Not shared between processes — weaker than Redis but never fails.
    """

    def __init__(self) -> None:
        self._buckets: Dict[str, Deque[float]] = defaultdict(deque)

    async def hit_and_count(self, key: str, window: float) -> int:
        now = time.time()
        bucket = self._buckets[key]
        cutoff = now - window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        bucket.append(now)
        return len(bucket)

    async def count_only(self, key: str, window: float) -> int:
        now = time.time()
        bucket = self._buckets[key]
        cutoff = now - window
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        return len(bucket)


class RateLimiter:
    def __init__(self) -> None:
        self.redis = None
        self._fallback = _InProcessBackend()
        self._redis_checked = False
        self._redis_available = False

    async def connect(self) -> None:
        """Connect to Redis. Failure is logged, not raised."""
        try:
            import redis.asyncio as redis_asyncio
            self.redis = await redis_asyncio.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Ping to confirm the connection actually works
            await self.redis.ping()
            self._redis_available = True
            logger.info("RateLimiter: Redis backend connected")
        except Exception as exc:
            self.redis = None
            self._redis_available = False
            logger.warning(
                "RateLimiter: Redis unavailable (%s); using in-process fallback",
                exc,
            )
        finally:
            self._redis_checked = True

    async def check(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> Tuple[bool, int]:
        """
        Record a hit for `key` and report whether it is within the limit.

        Returns:
            (allowed, remaining)
        """
        if not self._redis_checked:
            await self.connect()

        if self._redis_available and self.redis is not None:
            try:
                return await self._check_redis(key, limit, window)
            except Exception as exc:
                logger.warning(
                    "RateLimiter: Redis op failed (%s); falling back", exc
                )
                self._redis_available = False
                self.redis = None

        # Fallback path
        count = await self._fallback.hit_and_count(key, window)
        allowed = count <= limit
        remaining = max(0, limit - count)
        return allowed, remaining

    async def _check_redis(
        self, key: str, limit: int, window: int
    ) -> Tuple[bool, int]:
        now = time.time()
        cutoff = now - window

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, cutoff)
        pipe.zcard(key)
        results = await pipe.execute()
        current_count = int(results[1] or 0)

        if current_count >= limit:
            # Over limit — do NOT record the hit, so a flood of rejected
            # requests does not permanently fill the window.
            return False, 0

        # Under limit — record this hit.
        pipe = self.redis.pipeline()
        pipe.zadd(key, {str(now): now})
        pipe.expire(key, window)
        await pipe.execute()

        count_after = current_count + 1
        allowed = count_after <= limit
        remaining = max(0, limit - count_after)
        return allowed, remaining

    async def close(self) -> None:
        if self.redis is not None:
            try:
                await self.redis.aclose()
            except Exception:
                pass
            self.redis = None
            self._redis_available = False


# ---------------------------------------------------------------------------
# Per-route presets (used by the middleware / route handlers)
# ---------------------------------------------------------------------------

RATE_LIMITS = {
    "auth.login":       (10, 60),     # 10 attempts per minute
    "auth.register":    (5,  60),     # 5 registrations per minute
    "search.create":    (30, 60),     # 30 searches per minute
    "search.get":       (120, 60),    # 120 reads per minute
    "export.download":  (5,  60),     # 5 exports per minute
    "rfq.create":       (20, 60),     # 20 RFQs per minute
    "watchlist.mutate": (30, 60),     # 30 watchlist changes per minute
}