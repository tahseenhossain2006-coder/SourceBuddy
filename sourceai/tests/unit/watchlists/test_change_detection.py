"""Watchlist change-detection tests (DB-backed, with a real test user)."""
import uuid

import pytest
import pytest_asyncio

from sourceai.alerts.service import AlertService
from sourceai.storage.postgres import PostgresStorage
from sourceai.watchlists.models import WatchlistCreate, WatchType
from sourceai.watchlists.service import WatchlistService


@pytest_asyncio.fixture
async def user_id():
    """
    Create a real user so FK-constrained tables accept inserts.
    Cleanup removes the user and any rows that reference it.
    """
    db = PostgresStorage()
    await db.connect()
    uid = str(uuid.uuid4())
    email = f"test_{uid[:8]}@example.com"

    async with db.pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO users (id, email, password_hash, is_active, is_admin)
            VALUES ($1, $2, $3, TRUE, FALSE)
            """,
            uid,
            email,
            "$2b$12$placeholder_hash_for_tests",
        )

    try:
        yield uid
    finally:
        async with db.pool.acquire() as conn:
            await conn.execute("DELETE FROM alerts WHERE user_id = $1", uid)
            await conn.execute("DELETE FROM watchlists WHERE user_id = $1", uid)
            await conn.execute("DELETE FROM users WHERE id = $1", uid)
        await db.close()


# ---------------------------------------------------------------------------
# Watchlist CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_watchlist(user_id):
    svc = WatchlistService()
    resp = await svc.create(
        user_id,
        WatchlistCreate(type=WatchType.SUPPLIER, target_id="https://example.com/x"),
    )
    assert resp.id
    assert resp.user_id == user_id
    assert resp.type == WatchType.SUPPLIER
    assert resp.last_hash is None
    assert resp.last_checked is None

    await svc.delete(resp.id, user_id)


# ---------------------------------------------------------------------------
# Change detection
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_check_establishes_baseline_no_alert(user_id, monkeypatch):
    svc = WatchlistService()

    async def fake_fetch(self, watch_type, target_id):
        return "MOQ 500 pieces\nPrice 100 INR", None
    monkeypatch.setattr(WatchlistService, "_fetch_content", fake_fetch)

    resp = await svc.create(
        user_id,
        WatchlistCreate(type=WatchType.SUPPLIER, target_id="https://example.com/a"),
    )
    result = await svc.check(resp.id, user_id)

    assert result.changed is False
    assert result.alert_created is False
    assert result.error is None
    assert len(result.last_hash) == 64

    alerts = await AlertService().get_unread(user_id)
    assert len(alerts) == 0

    await svc.delete(resp.id, user_id)


@pytest.mark.asyncio
async def test_no_alert_on_unchanged_content(user_id, monkeypatch):
    svc = WatchlistService()
    content = "MOQ 500 pieces\nPrice 100 INR"

    async def fake_fetch(self, watch_type, target_id):
        return content, None
    monkeypatch.setattr(WatchlistService, "_fetch_content", fake_fetch)

    resp = await svc.create(
        user_id,
        WatchlistCreate(type=WatchType.SUPPLIER, target_id="https://example.com/b"),
    )
    await svc.check(resp.id, user_id)
    result = await svc.check(resp.id, user_id)

    assert result.changed is False
    assert result.alert_created is False

    alerts = await AlertService().get_unread(user_id)
    assert len(alerts) == 0

    await svc.delete(resp.id, user_id)


@pytest.mark.asyncio
async def test_alert_on_changed_content(user_id, monkeypatch):
    svc = WatchlistService()
    content_holder = {"text": "MOQ 500 pieces\nPrice 100 INR"}

    async def fake_fetch(self, watch_type, target_id):
        return content_holder["text"], None
    monkeypatch.setattr(WatchlistService, "_fetch_content", fake_fetch)

    resp = await svc.create(
        user_id,
        WatchlistCreate(type=WatchType.PRICE, target_id="https://example.com/c"),
    )
    await svc.check(resp.id, user_id)

    content_holder["text"] = "MOQ 500 pieces\nPrice 150 INR"

    result = await svc.check(resp.id, user_id)
    assert result.changed is True
    assert result.alert_created is True

    alerts = await AlertService().get_unread(user_id)
    assert len(alerts) == 1
    assert alerts[0].user_id == user_id
    assert alerts[0].type.value == "price_change"

    await svc.delete(resp.id, user_id)


@pytest.mark.asyncio
async def test_whitespace_change_does_not_trigger_alert(user_id, monkeypatch):
    svc = WatchlistService()
    content_holder = {"text": "MOQ 500 pieces"}

    async def fake_fetch(self, watch_type, target_id):
        return content_holder["text"], None
    monkeypatch.setattr(WatchlistService, "_fetch_content", fake_fetch)

    resp = await svc.create(
        user_id,
        WatchlistCreate(type=WatchType.SUPPLIER, target_id="https://example.com/d"),
    )
    await svc.check(resp.id, user_id)

    content_holder["text"] = "  moq   500  pieces \n"
    result = await svc.check(resp.id, user_id)

    assert result.changed is False
    assert result.alert_created is False

    await svc.delete(resp.id, user_id)


@pytest.mark.asyncio
async def test_check_missing_watchlist_raises(user_id):
    svc = WatchlistService()
    with pytest.raises(ValueError):
        await svc.check(str(uuid.uuid4()), user_id)


# ---------------------------------------------------------------------------
# Hash behavior (no DB)
# ---------------------------------------------------------------------------

def test_hash_is_deterministic():
    h1 = WatchlistService._hash("MOQ 500 pieces")
    h2 = WatchlistService._hash("MOQ 500 pieces")
    assert h1 == h2
    assert len(h1) == 64


def test_hash_normalizes_whitespace_and_case():
    h1 = WatchlistService._hash("MOQ   500\nPieces")
    h2 = WatchlistService._hash("moq 500 pieces")
    assert h1 == h2


def test_hash_changes_on_edit():
    h1 = WatchlistService._hash("MOQ 500 pieces")
    h2 = WatchlistService._hash("MOQ 1000 pieces")
    assert h1 != h2


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_alert_mark_read(user_id):
    from sourceai.alerts.models import AlertType
    svc = AlertService()
    alert = await svc.create_alert(
        user_id=user_id,
        alert_type=AlertType.PRICE_CHANGE,
        message="test",
        data={},
    )
    assert alert.read is False

    marked = await svc.mark_read(alert.id, user_id)
    assert marked is True

    unread = await svc.get_unread(user_id)
    assert all(a.id != alert.id for a in unread)
@pytest.mark.asyncio
async def test_scheduler_runs_without_error(monkeypatch):
    """The scheduled check_all_watchlists must run cleanly with zero rows."""
    from sourceai.watchlists import scheduler
    # Empty the watchlists table for this test's user is not needed —
    # check_all_watchlists tolerates zero rows.
    await scheduler.check_all_watchlists()    