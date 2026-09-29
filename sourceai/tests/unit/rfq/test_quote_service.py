"""Quote service tests (DB-backed, full FK chain: user → search → supplier → quote)."""
import uuid

import pytest
import pytest_asyncio

from sourceai.quote.service import QuoteService
from sourceai.rfq.models import RFQCreate, RFQItem
from sourceai.rfq.service import RFQService
from sourceai.storage.postgres import PostgresStorage


@pytest_asyncio.fixture
async def db_chain():
    """
    Create user → search → supplier. Yields their IDs.
    Cleans up the whole chain on teardown (CASCADE removes dependent rows).
    """
    db = PostgresStorage()
    await db.connect()

    user_id = str(uuid.uuid4())
    search_id = str(uuid.uuid4())
    supplier_id = str(uuid.uuid4())
    email = f"test_{user_id[:8]}@example.com"

    async with db.pool.acquire() as conn:
        # users: only id/email/password_hash/is_active/is_admin required
        # (created_at, updated_at have defaults)
        await conn.execute(
            """
            INSERT INTO users (id, email, password_hash, is_active, is_admin)
            VALUES ($1, $2, $3, TRUE, FALSE)
            """,
            user_id, email, "$2b$12$placeholder_hash_for_tests",
        )
        # searches: id/user_id/query/status required; timestamps default
        await conn.execute(
            """
            INSERT INTO searches (id, user_id, query, status)
            VALUES ($1, $2, $3, 'completed')
            """,
            search_id, user_id, "test query",
        )
        # suppliers: search_id nullable FK; company_name nullable
        await conn.execute(
            """
            INSERT INTO suppliers (id, search_id, company_name)
            VALUES ($1, $2, $3)
            """,
            supplier_id, search_id, "Test Supplier",
        )

    try:
        yield {
            "user_id": user_id,
            "search_id": search_id,
            "supplier_id": supplier_id,
        }
    finally:
        async with db.pool.acquire() as conn:
            # Explicit deletes in dependency order. CASCADE also handles
            # these, but being explicit avoids surprises if a future schema
            # change drops the ON DELETE CASCADE.
            await conn.execute(
                "DELETE FROM quotes WHERE supplier_id = $1", supplier_id
            )
            await conn.execute(
                "DELETE FROM outreaches WHERE supplier_id = $1", supplier_id
            )
            await conn.execute(
                "DELETE FROM rfqs WHERE user_id = $1", user_id
            )
            await conn.execute(
                "DELETE FROM suppliers WHERE id = $1", supplier_id
            )
            await conn.execute(
                "DELETE FROM searches WHERE id = $1", search_id
            )
            await conn.execute("DELETE FROM users WHERE id = $1", user_id)
        await db.close()


async def _make_rfq(user_id: str) -> str:
    svc = RFQService()
    rfq = await svc.create_rfq(
        user_id,
        RFQCreate(
            title="Test RFQ",
            items=[RFQItem(product_name="Bottle", quantity=1000, unit="pcs")],
            suppliers=[],
            currency="USD",
        ),
    )
    return rfq.id


# ---------------------------------------------------------------------------
# Quote creation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_quote(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    quote = await svc.create(
        rfq_id,
        db_chain["supplier_id"],
        {
            "price": 2.5,
            "currency": "usd",
            "moq": 500,
            "lead_time": "2 weeks",
            "incoterms": "fob",
            "notes": "Bulk discount available",
        },
    )
    assert quote["currency"] == "USD"
    assert quote["price"] == "2.5"
    assert quote["incoterms"] == "FOB"
    assert quote["moq"] == "500"
    assert quote["lead_time"] == "2 weeks"
    assert quote["rfq_id"] == rfq_id
    assert quote["supplier_id"] == db_chain["supplier_id"]


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_quotes_for_rfq(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    await svc.create(rfq_id, db_chain["supplier_id"], {"price": 2.5, "currency": "USD"})
    await svc.create(rfq_id, db_chain["supplier_id"], {"price": 2.75, "currency": "USD"})
    quotes = await svc.list_for_rfq(rfq_id)
    assert len(quotes) == 2
    # Ordered by created_at DESC — most recent first
    assert quotes[0]["price"] == "2.75"


@pytest.mark.asyncio
async def test_get_quote_by_id(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    created = await svc.create(
        rfq_id, db_chain["supplier_id"], {"price": 2.5, "currency": "USD"}
    )
    fetched = await svc.get(created["id"])
    assert fetched is not None
    assert fetched["id"] == created["id"]


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quote_normalizes_currency_aliases(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    for alias, expected in [
        ("rs", "INR"), ("₹", "INR"), ("rupee", "INR"),
        ("$", "USD"), ("dollar", "USD"),
        ("€", "EUR"), ("£", "GBP"),
        ("rmb", "CNY"),
    ]:
        q = await svc.create(
            rfq_id, db_chain["supplier_id"],
            {"price": 100, "currency": alias},
        )
        assert q["currency"] == expected, f"alias={alias!r}"


@pytest.mark.asyncio
async def test_quote_rejects_nonstandard_incoterms(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    quote = await svc.create(
        rfq_id, db_chain["supplier_id"], {"incoterms": "not-a-real-term"}
    )
    assert quote["incoterms"] is None


@pytest.mark.asyncio
async def test_quote_accepts_standard_incoterms(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    for term in ("EXW", "FOB", "CIF", "DDP"):
        q = await svc.create(
            rfq_id, db_chain["supplier_id"], {"incoterms": term.lower()},
        )
        assert q["incoterms"] == term


@pytest.mark.asyncio
async def test_quote_numeric_moq_becomes_string(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    q = await svc.create(
        rfq_id, db_chain["supplier_id"], {"moq": 500},
    )
    assert q["moq"] == "500"
    assert isinstance(q["moq"], str)


@pytest.mark.asyncio
async def test_quote_numeric_price_becomes_string(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    q = await svc.create(
        rfq_id, db_chain["supplier_id"], {"price": 2.5},
    )
    assert q["price"] == "2.5"


# ---------------------------------------------------------------------------
# Evidence round-trip
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_quote_evidence_round_trips(db_chain):
    rfq_id = await _make_rfq(db_chain["user_id"])
    svc = QuoteService()
    evidence = {"source_url": "https://example.com/quote", "confidence": 0.9}
    created = await svc.create(
        rfq_id, db_chain["supplier_id"],
        {"price": 2.5, "evidence": evidence},
    )
    assert created["evidence"] == evidence

    fetched = await svc.get(created["id"])
    assert fetched["evidence"] == evidence