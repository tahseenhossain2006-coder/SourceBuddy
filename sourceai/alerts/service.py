# sourceai/alerts/service.py
import json
import uuid
from datetime import datetime, timezone

from sourceai.storage.postgres import PostgresStorage
from sourceai.alerts.models import AlertResponse, AlertType


class AlertService:
    def __init__(self):
        self.db = PostgresStorage()

    async def create_alert(
        self,
        user_id: str,
        alert_type: AlertType,
        message: str,
        data: dict,
    ) -> AlertResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            alert_id = str(uuid.uuid4())
            # The `data` column is text/jsonb. asyncpg binds a str
            # cleanly; a raw dict fails.
            data_json = json.dumps(data or {}, default=str)
            await conn.execute(
                """
                INSERT INTO alerts
                  (id, user_id, type, message, data, read, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                alert_id,
                user_id,
                alert_type.value,
                message,
                data_json,
                False,
                datetime.now(timezone.utc),
            )
            row = await conn.fetchrow(
                "SELECT * FROM alerts WHERE id = $1", alert_id
            )
            return self._row_to_response(row)

    async def get_unread(self, user_id: str) -> list[AlertResponse]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT * FROM alerts
                 WHERE user_id = $1 AND read = false
                 ORDER BY created_at DESC
                """,
                user_id,
            )
            return [self._row_to_response(r) for r in rows]

    async def mark_read(self, alert_id: str, user_id: str) -> bool:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            result = await conn.execute(
                "UPDATE alerts SET read = true WHERE id = $1 AND user_id = $2",
                alert_id,
                user_id,
            )
            return result != "UPDATE 0"

    def _row_to_response(self, row) -> AlertResponse:
        # `data` may come back as a dict (if jsonb) or a str (if text).
        raw = row["data"]
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except (json.JSONDecodeError, TypeError):
                raw = {}
        return AlertResponse(
            id=str(row["id"]),
            user_id=str(row["user_id"]),
            type=AlertType(row["type"]),
            message=row["message"],
            data=raw or {},
            read=row["read"],
            created_at=(
                row["created_at"].isoformat()
                if hasattr(row["created_at"], "isoformat")
                else str(row["created_at"])
            ),
        )