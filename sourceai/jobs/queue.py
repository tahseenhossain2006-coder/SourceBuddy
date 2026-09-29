# sourceai/jobs/queue.py
import json
import uuid
from datetime import datetime
from typing import Optional
import redis.asyncio as redis
from sourceai.config.settings import settings

class JobQueue:
    def __init__(self):
        self.redis = None

    async def connect(self):
        self.redis = await redis.from_url(settings.REDIS_URL)

    async def enqueue(self, job_type: str, payload: dict) -> str:
        if not self.redis:
            await self.connect()
        job_id = str(uuid.uuid4())
        await self.redis.hset(f"job:{job_id}", mapping={
            "id": job_id,
            "type": job_type,
            "payload": json.dumps(payload),
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
        })
        await self.redis.lpush(f"queue:{job_type}", job_id)
        return job_id

    async def dequeue(self, job_type: str, timeout: int = 5) -> Optional[dict]:
        if not self.redis:
            await self.connect()
        res = await self.redis.brpop(f"queue:{job_type}", timeout=timeout)
        if not res:
            return None
        _, job_id = res
        data = await self.redis.hgetall(f"job:{job_id}")
        await self.redis.hset(f"job:{job_id}", "status", "running")
        return {k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()}