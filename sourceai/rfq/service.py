# sourceai/rfq/service.py
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sourceai.storage.postgres import PostgresStorage
from sourceai.rfq.models import RFQCreate, RFQResponse, RFQStatus

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# State machine definition (module level)
# ------------------------------------------------------------------
VALID_TRANSITIONS: Dict[str, set] = {
    RFQStatus.DRAFT.value:              {RFQStatus.APPROVED.value, RFQStatus.CANCELLED.value},
    RFQStatus.APPROVED.value:           {RFQStatus.SENDING.value, RFQStatus.CANCELLED.value},
    RFQStatus.SENDING.value:            {RFQStatus.SENT.value, RFQStatus.CANCELLED.value},
    RFQStatus.SENT.value:               {RFQStatus.WAITING.value, RFQStatus.CANCELLED.value},
    RFQStatus.WAITING.value:            {RFQStatus.PARTIAL_RESPONSE.value,
                                         RFQStatus.COMPLETED.value,
                                         RFQStatus.CANCELLED.value},
    RFQStatus.PARTIAL_RESPONSE.value:   {RFQStatus.COMPLETED.value, RFQStatus.CANCELLED.value},
    RFQStatus.COMPLETED.value:          set(),
    RFQStatus.CANCELLED.value:          set(),
}


class RFQService:
    def __init__(self):
        self.db = PostgresStorage()

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    async def create_rfq(self, user_id: str, data: RFQCreate) -> RFQResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            rfq_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            # `items` is List[RFQItem] — a list of Pydantic models. asyncpg
            # cannot bind that to jsonb, so serialize to a JSON string.
            items_json = json.dumps(
                [item.model_dump() for item in data.items],
                default=str,
            )
            suppliers_json = json.dumps(data.suppliers, default=str)

            await conn.execute(
                """
                INSERT INTO rfqs
                  (id, user_id, title, description, items, suppliers,
                   deadline, delivery_location, currency, status,
                   created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                """,
                rfq_id,
                user_id,
                data.title,
                data.description,
                items_json,
                suppliers_json,
                data.deadline,
                data.delivery_location,
                data.currency,
                RFQStatus.DRAFT.value,
                now,
                now,
            )
            row = await conn.fetchrow("SELECT * FROM rfqs WHERE id = $1", rfq_id)
            return self._row_to_response(row)

    async def get_rfq(self, rfq_id: str, user_id: str) -> Optional[RFQResponse]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM rfqs WHERE id = $1 AND user_id = $2",
                rfq_id, user_id,
            )
            return self._row_to_response(row) if row else None

    async def list_rfqs(self, user_id: str) -> List[RFQResponse]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM rfqs WHERE user_id = $1 ORDER BY created_at DESC",
                user_id,
            )
            return [self._row_to_response(r) for r in rows]

    async def delete_rfq(self, rfq_id: str, user_id: str) -> bool:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM rfqs WHERE id = $1 AND user_id = $2",
                rfq_id, user_id,
            )
            return result != "DELETE 0"

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------
    async def transition(
        self, rfq_id: str, user_id: str, new_status: RFQStatus
    ) -> RFQResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM rfqs WHERE id = $1 AND user_id = $2",
                rfq_id, user_id,
            )
            if not row:
                raise ValueError("RFQ not found or not owned by user")

            current = row["status"]
            target = new_status.value

            allowed = VALID_TRANSITIONS.get(current, set())
            if target not in allowed:
                raise ValueError(
                    f"Invalid transition: '{current}' → '{target}'. "
                    f"Allowed: {sorted(allowed) or 'none'}"
                )

            now = datetime.now(timezone.utc)

            # sent_at / completed_at are optional per-transition
            extra_col = None
            if target == RFQStatus.SENT.value:
                extra_col = "sent_at"
            elif target == RFQStatus.COMPLETED.value:
                extra_col = "completed_at"

            if extra_col:
                sql = (
                    f"UPDATE rfqs SET status = $1, updated_at = $2, "
                    f"{extra_col} = $3 WHERE id = $4 AND user_id = $5"
                )
                await conn.execute(sql, target, now, now, rfq_id, user_id)
            else:
                sql = (
                    "UPDATE rfqs SET status = $1, updated_at = $2 "
                    "WHERE id = $3 AND user_id = $4"
                )
                await conn.execute(sql, target, now, rfq_id, user_id)

            updated = await conn.fetchrow(
                "SELECT * FROM rfqs WHERE id = $1", rfq_id
            )
            return self._row_to_response(updated)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_response(row) -> RFQResponse:
        def _iso(v):
            return v.isoformat() if hasattr(v, "isoformat") else v

        def _decode_items(v):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return v or []

        def _decode_suppliers(v):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return []
            return v or []

        return RFQResponse(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            title=row["title"],
            status=RFQStatus(row["status"]),
            items=_decode_items(row["items"]),
            suppliers=_decode_suppliers(row["suppliers"]),
            deadline=row.get("deadline"),
            created_at=row["created_at"],
            updated_at=row.get("updated_at"),
            sent_at=row.get("sent_at"),
            completed_at=row.get("completed_at"),
        )