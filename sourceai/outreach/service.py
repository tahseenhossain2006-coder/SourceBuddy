import uuid
import asyncpg
from datetime import datetime
from sourceai.storage.postgres import PostgresStorage
from sourceai.outreach.models import OutreachCreate, OutreachResponse, OutreachStatus

class OutreachService:
    def __init__(self):
        self.db = PostgresStorage()

    async def create_outreach(self, user_id: str, data: OutreachCreate) -> OutreachResponse:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            # Verify ownership of rfq
            rfq = await conn.fetchrow("SELECT user_id FROM rfqs WHERE id = $1", data.rfq_id)
            if not rfq or rfq["user_id"] != user_id:
                raise ValueError("RFQ not found or not owned")
            id = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO outreaches (id, rfq_id, supplier_id, subject, message, status, created_at)
                   VALUES ($1, $2, $3, $4, $5, $6, $7)""",
                id, data.rfq_id, data.supplier_id, data.subject, data.message,
                OutreachStatus.DRAFT.value, datetime.utcnow()
            )
            row = await conn.fetchrow("SELECT * FROM outreaches WHERE id = $1", id)
            return self._row_to_response(row)

    async def approve(self, outreach_id: str, user_id: str) -> bool:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            # Verify ownership via rfq
            row = await conn.fetchrow(
                """SELECT o.id FROM outreaches o
                   JOIN rfqs r ON o.rfq_id = r.id
                   WHERE o.id = $1 AND r.user_id = $2""",
                outreach_id, user_id
            )
            if not row:
                return False
            await conn.execute(
                "UPDATE outreaches SET status = $1, updated_at = $2 WHERE id = $3",
                OutreachStatus.APPROVED.value, datetime.utcnow(), outreach_id
            )
            return True

    async def send(self, outreach_id: str, user_id: str) -> bool:
        # In reality, this would call an email provider.
        # For MVP, we just mark as sent.
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                """SELECT o.id FROM outreaches o
                   JOIN rfqs r ON o.rfq_id = r.id
                   WHERE o.id = $1 AND r.user_id = $2""",
                outreach_id, user_id
            )
            if not row:
                return False
            await conn.execute(
                "UPDATE outreaches SET status = $1, sent_at = $2, updated_at = $3 WHERE id = $4",
                OutreachStatus.SENT.value, datetime.utcnow(), datetime.utcnow(), outreach_id
            )
            return True

    def _row_to_response(self, row) -> OutreachResponse:
        return OutreachResponse(
            id=row["id"],
            rfq_id=row["rfq_id"],
            supplier_id=row["supplier_id"],
            status=OutreachStatus(row["status"]),
            message=row["message"],
            subject=row["subject"],
            sent_at=row.get("sent_at"),
            created_at=row["created_at"]
        )