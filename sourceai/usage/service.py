# sourceai/usage/service.py
import os
from datetime import datetime
from typing import Optional
import redis.asyncio as redis

from sourceai.usage.models import UsageRecord, UserQuota


class UsageService:
    def __init__(self):
        self.redis = None
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    async def connect(self):
        if self.redis is None:
            self.redis = await redis.from_url(self.redis_url)

    async def check_and_reserve(self, user_id: str, operation: str, cost: int = 1) -> bool:
        await self.connect()
        day_key = f"quota:{user_id}:{operation}:day:{datetime.utcnow().date()}"
        current = await self.redis.get(day_key) or 0
        limit = self._get_limit(user_id, operation)
        if int(current) + cost > limit:
            return False
        await self.redis.incr(day_key, cost)
        await self.redis.expire(day_key, 86400)
        return True

    def _get_limit(self, user_id: str, operation: str) -> int:
        defaults = {
            "search": int(os.getenv("MAX_USER_DAILY_SEARCHES", 10)),
            "llm_call": int(os.getenv("MAX_USER_DAILY_LLM_CALLS", 20)),
            "crawl": int(os.getenv("MAX_USER_DAILY_CRAWL_PAGES", 50)),
        }
        return defaults.get(operation, 10)

    async def record_usage(self, record: UsageRecord):
        # Placeholder for durable usage persistence — implement via PostgresStorage
        pass

    async def close(self):
        """Close the Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None