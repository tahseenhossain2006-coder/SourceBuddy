# sourceai/storage/postgres.py
import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

import asyncpg

logger = logging.getLogger(__name__)


class PostgresStorage:
    def __init__(self) -> None:
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()
        self._loop_id: Optional[int] = None

    async def connect(self) -> None:
        """Create the pool if missing or if the running event loop changed."""
        current_loop_id = id(asyncio.get_running_loop())

        # If the pool exists but was created on a different event loop,
        # it's unusable. Drop the reference and rebuild.
        if self.pool is not None and self._loop_id != current_loop_id:
            logger.info(
                "Event loop changed (%s -> %s); rebuilding Postgres pool",
                self._loop_id, current_loop_id,
            )
            self.pool = None
            self._loop_id = None

        if self.pool is not None:
            return

        async with self._lock:
            # Re-check after acquiring the lock.
            current_loop_id = id(asyncio.get_running_loop())
            if self.pool is not None and self._loop_id == current_loop_id:
                return

            from sourceai.config.settings import settings

            dsn = getattr(settings, "DATABASE_URL", None) or os.getenv("DATABASE_URL", "")
            if not dsn:
                raise RuntimeError("DATABASE_URL is not set")
            dsn = dsn.replace("postgresql+asyncpg://", "postgresql://")

            self.pool = await asyncpg.create_pool(dsn, min_size=1, max_size=5)
            self._loop_id = current_loop_id
            logger.info("PostgresStorage pool created (loop=%s)", current_loop_id)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None
            self._loop_id = None
            logger.info("PostgresStorage pool closed")

    async def _get_pool(self) -> asyncpg.Pool:
        await self.connect()
        assert self.pool is not None
        return self.pool

    async def save_search(
        self,
        query: str,
        plan: Dict[str, Any],
        suppliers: List[Dict[str, Any]],
    ) -> None:
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            search_id = await conn.fetchval(
                """
                INSERT INTO searches (query, plan, status, created_at, updated_at)
                VALUES ($1, $2, 'completed', NOW(), NOW())
                RETURNING id
                """,
                query,
                plan,
            )
            for s in suppliers:
                await conn.execute(
                    """
                    INSERT INTO suppliers
                      (search_id, company_name, website, country, location, moq, price,
                       currency, metadata, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                    """,
                    search_id,
                    s.get("company_name") or s.get("name"),
                    s.get("website"),
                    s.get("country"),
                    s.get("location"),
                    str(s.get("moq")) if s.get("moq") is not None else None,
                    str(s.get("price")) if s.get("price") is not None else None,
                    s.get("currency"),
                    s.get("metadata", {}),
                )