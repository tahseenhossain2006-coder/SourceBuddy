# sourceai/watchlists/scheduler.py
"""
Background job: check every enabled watchlist every N minutes.

Uses APScheduler (already a project dependency).
"""
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from sourceai.config.settings import settings
from sourceai.storage.postgres import PostgresStorage
from sourceai.watchlists.service import WatchlistService

logger = logging.getLogger(__name__)


async def check_all_watchlists() -> None:
    """Fetch every enabled watchlist and run its check."""
    db = PostgresStorage()
    await db.connect()
    async with db.pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, user_id FROM watchlists WHERE enabled = TRUE"
        )

    logger.info("Scheduler: checking %d watchlists", len(rows))
    svc = WatchlistService()
    for row in rows:
        try:
            await svc.check(row["id"], str(row["user_id"]))
        except Exception:
            logger.exception(
                "Scheduled check failed for watchlist %s", row["id"]
            )


def start_scheduler() -> AsyncIOScheduler:
    """
    Create, configure, and start the scheduler.

    Call from FastAPI startup (see api/main.py lifespan).
    Returns the scheduler so it can be shut down later.
    """
    interval_minutes = int(
        getattr(settings, "WATCHLIST_CHECK_INTERVAL_MINUTES", 30)
    )

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_all_watchlists,
        "interval",
        minutes=interval_minutes,
        id="watchlist_check",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    logger.info(
        "Watchlist scheduler started (interval=%d min)", interval_minutes
    )
    return scheduler