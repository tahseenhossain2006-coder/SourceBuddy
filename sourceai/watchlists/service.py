# sourceai/watchlists/service.py
import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from sourceai.storage.postgres import PostgresStorage
from sourceai.watchlists.models import (
    WatchlistCreate,
    WatchlistResponse,
    WatchlistCheckResult,
    WatchType,
)

logger = logging.getLogger(__name__)


class WatchlistService:
    def __init__(self):
        self.db = PostgresStorage()

    # ------------------------------------------------------------------ CRUD
    async def create(self, user_id: str, data: WatchlistCreate) -> WatchlistResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            watch_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO watchlists
                  (id, user_id, type, target_id, condition, enabled, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                watch_id,
                user_id,
                data.type.value,
                data.target_id,
                data.condition,
                True,
                datetime.now(timezone.utc),
            )
            row = await conn.fetchrow(
                "SELECT * FROM watchlists WHERE id = $1", watch_id
            )
            return self._row_to_response(row)

    async def get_all(self, user_id: str) -> list[WatchlistResponse]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM watchlists WHERE user_id = $1 ORDER BY created_at DESC",
                user_id,
            )
            return [self._row_to_response(r) for r in rows]

    async def delete(self, watch_id: str, user_id: str) -> bool:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM watchlists WHERE id = $1 AND user_id = $2",
                watch_id,
                user_id,
            )
            return result != "DELETE 0"

    # ------------------------------------------------------------ check
    async def check(self, watch_id: str, user_id: str) -> WatchlistCheckResult:
        """
        Fetch the watched target, hash its normalized content, and compare
        to the stored hash. On change, create an alert and update the hash.
        """
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM watchlists WHERE id = $1 AND user_id = $2",
                watch_id,
                user_id,
            )

        if row is None:
            raise ValueError("Watchlist not found")

        watch_type = row["type"]
        target_id = row["target_id"]

        try:
            content, error = await self._fetch_content(watch_type, target_id)
        except Exception as exc:
            logger.exception("Watchlist check failed for %s", watch_id)
            content, error = None, str(exc)

        if error is not None or content is None:
            await self._update_checked(watch_id, None, None)
            return WatchlistCheckResult(
                watchlist_id=watch_id,
                changed=False,
                alert_created=False,
                last_hash=row.get("last_hash") or "",
                checked_at=datetime.now(timezone.utc).isoformat(),
                error=error or "No content fetched",
            )

        new_hash = self._hash(content)
        old_hash = row.get("last_hash")

        changed = False
        alert_created = False

        if old_hash is None:
            # First check — establish baseline. No alert.
            pass
        elif old_hash != new_hash:
            changed = True
            alert_created = await self._create_change_alert(
                user_id=user_id,
                watch_type=watch_type,
                watch_id=watch_id,
                target_id=target_id,
                old_hash=old_hash,
                new_hash=new_hash,
                snippet=content[:400],
            )

        await self._update_checked(watch_id, new_hash, content[:400])

        return WatchlistCheckResult(
            watchlist_id=watch_id,
            changed=changed,
            alert_created=alert_created,
            last_hash=new_hash,
            checked_at=datetime.now(timezone.utc).isoformat(),
            error=None,
        )

    # ------------------------------------------------------------ internals
    @staticmethod
    def _hash(text: str) -> str:
        """Deterministic SHA-256 of whitespace-normalized, lowercased text."""
        normalized = re.sub(r"\s+", " ", text or "").strip().lower()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    async def _fetch_content(
        self, watch_type: str, target_id: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Fetch the raw content of a watched target.

        URL targets → crawl the page HTML.
        Supplier / product targets → look up the DB row.
        """
        if target_id.startswith(("http://", "https://")):
            from sourceai.crawling.manager import CrawlManager
            crawler = CrawlManager()
            results = await crawler.crawl([target_id])
            if not results:
                return None, "Fetch failed"
            r = results[0]
            if r.error:
                return None, r.error
            if not r.html:
                return None, "Empty response"
            return r.html, None

        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            if watch_type in ("supplier", "product"):
                row = await conn.fetchrow(
                    "SELECT company_name, website, country, location, moq, price, currency "
                    "FROM suppliers WHERE id = $1",
                    target_id,
                )
            else:
                row = None

            if row is None:
                return None, "Target not found"

            return "|".join(str(v or "") for v in row.values()), None

    async def _create_change_alert(
        self,
        user_id: str,
        watch_type: str,
        watch_id: str,
        target_id: str,
        old_hash: str,
        new_hash: str,
        snippet: str,
    ) -> bool:
        try:
            from sourceai.alerts.service import AlertService
            from sourceai.alerts.models import AlertType

            type_map = {
                "supplier": AlertType.SUPPLIER_CHANGE,
                "product": AlertType.SUPPLIER_CHANGE,
                "price": AlertType.PRICE_CHANGE,
                "moq": AlertType.MOQ_CHANGE,
                "rfq": AlertType.RFQ_RESPONSE,
            }
            alert_type = type_map.get(watch_type, AlertType.SUPPLIER_CHANGE)

            await AlertService().create_alert(
                user_id=user_id,
                alert_type=alert_type,
                message=f"Change detected in watched {watch_type} ({target_id[:60]})",
                data={
                    "watchlist_id": watch_id,
                    "target_id": target_id,
                    "old_hash": old_hash,
                    "new_hash": new_hash,
                    "snippet": snippet,
                },
            )
            return True
        except Exception:
            logger.exception("Failed to create change alert")
            return False

    async def _update_checked(
        self, watch_id: str, new_hash: Optional[str], snippet: Optional[str]
    ) -> None:
        async with self.db.pool.acquire() as conn:
            if new_hash is not None:
                await conn.execute(
                    """
                    UPDATE watchlists
                       SET last_hash = $1,
                           last_checked = $2,
                           last_content_snippet = $3
                     WHERE id = $4
                    """,
                    new_hash,
                    datetime.now(timezone.utc),
                    snippet,
                    watch_id,
                )
            else:
                await conn.execute(
                    "UPDATE watchlists SET last_checked = $1 WHERE id = $2",
                    datetime.now(timezone.utc),
                    watch_id,
                )

    # ------------------------------------------------------------ mapping
    @staticmethod
    def _row_to_response(row) -> WatchlistResponse:
        def _iso(value):
            return value.isoformat() if hasattr(value, "isoformat") else value

        return WatchlistResponse(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            type=WatchType(row["type"]),
            target_id=row["target_id"],
            condition=row.get("condition"),
            last_hash=row.get("last_hash"),
            last_checked=(
                _iso(row.get("last_checked"))
                if row.get("last_checked")
                else None
            ),
            created_at=_iso(row["created_at"]),
        )