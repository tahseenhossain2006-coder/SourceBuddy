# sourceai/quote/service.py
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sourceai.storage.postgres import PostgresStorage

logger = logging.getLogger(__name__)

_CURRENCY_ALIASES = {
    "inr": "INR", "rs": "INR", "rs.": "INR", "₹": "INR",
    "rupee": "INR", "rupees": "INR",
    "usd": "USD", "$": "USD", "dollar": "USD", "dollars": "USD",
    "eur": "EUR", "€": "EUR", "euro": "EUR", "euros": "EUR",
    "gbp": "GBP", "£": "GBP", "pound": "GBP", "pounds": "GBP",
    "cny": "CNY", "rmb": "CNY", "¥": "CNY", "yuan": "CNY",
}

_INCOTERMS = {"EXW", "FOB", "CIF", "CFR", "DDP", "DAP", "FCA", "CPT", "CIP"}


class QuoteService:
    def __init__(self):
        self.db = PostgresStorage()

    async def create(
        self,
        rfq_id: str,
        supplier_id: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            quote_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)

            normalized = self._normalize(data)
            await conn.execute(
                """
                INSERT INTO quotes
                  (id, rfq_id, supplier_id, price, currency, moq,
                   lead_time, payment_terms, shipping_terms, incoterms,
                   validity, notes, evidence, created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10,
                        $11, $12, $13, $14, $15)
                """,
                quote_id,
                rfq_id,
                supplier_id,
                normalized["price"],
                normalized["currency"],
                normalized["moq"],
                normalized["lead_time"],
                normalized["payment_terms"],
                normalized["shipping_terms"],
                normalized["incoterms"],
                normalized["validity"],
                normalized["notes"],
                json.dumps(normalized["evidence"], default=str),
                now,
                now,
            )
            row = await conn.fetchrow(
                "SELECT * FROM quotes WHERE id = $1", quote_id
            )
            return self._row_to_dict(row)

    async def list_for_rfq(self, rfq_id: str) -> List[Dict[str, Any]]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT * FROM quotes WHERE rfq_id = $1 ORDER BY created_at DESC",
                rfq_id,
            )
            return [self._row_to_dict(r) for r in rows]

    async def get(self, quote_id: str) -> Optional[Dict[str, Any]]:
        await self.db.connect()
        async with self.db.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM quotes WHERE id = $1", quote_id
            )
            return self._row_to_dict(row) if row else None

    # ------------------------------------------------------------------
    @staticmethod
    def _normalize(data: Dict[str, Any]) -> Dict[str, Any]:
        price = data.get("price")
        if isinstance(price, (int, float)):
            price = str(price)

        currency_raw = (data.get("currency") or "").strip().lower()
        currency = _CURRENCY_ALIASES.get(currency_raw, currency_raw.upper() or None)

        incoterms = (data.get("incoterms") or "").strip().upper() or None
        if incoterms and incoterms not in _INCOTERMS:
            incoterms = None

        moq = data.get("moq")
        if isinstance(moq, (int, float)):
            moq = str(int(moq))

        return {
            "price": price,
            "currency": currency,
            "moq": moq,
            "lead_time": data.get("lead_time"),
            "payment_terms": data.get("payment_terms"),
            "shipping_terms": data.get("shipping_terms"),
            "incoterms": incoterms,
            "validity": data.get("validity"),
            "notes": data.get("notes"),
            "evidence": data.get("evidence") or {},
        }

    @staticmethod
    def _row_to_dict(row) -> Dict[str, Any]:
        def _iso(v):
            return v.isoformat() if hasattr(v, "isoformat") else v

        def _json(v):
            if isinstance(v, str):
                try:
                    return json.loads(v)
                except Exception:
                    return {}
            return v or {}

        return {
            "id": str(row["id"]),
            "rfq_id": str(row["rfq_id"]),
            "supplier_id": str(row["supplier_id"]),
            "price": row.get("price"),
            "currency": row.get("currency"),
            "moq": row.get("moq"),
            "lead_time": row.get("lead_time"),
            "payment_terms": row.get("payment_terms"),
            "shipping_terms": row.get("shipping_terms"),
            "incoterms": row.get("incoterms"),
            "validity": _iso(row.get("validity")),
            "notes": row.get("notes"),
            "evidence": _json(row.get("evidence")),
            "created_at": _iso(row.get("created_at")),
            "updated_at": _iso(row.get("updated_at")),
        }