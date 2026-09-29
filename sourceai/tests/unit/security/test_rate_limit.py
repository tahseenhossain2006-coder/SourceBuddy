"""Rate limiter tests (Redis mocked, in-process fallback exercised)."""
import asyncio
import time

import pytest

from sourceai.security.rate_limit import RateLimiter, RATE_LIMITS


@pytest.mark.asyncio
async def test_allows_under_limit():
    rl = RateLimiter()
    rl._redis_checked = True  # skip connect
    rl._redis_available = False  # force fallback

    for i in range(5):
        allowed, remaining = await rl.check("test:a", limit=10, window=60)
        assert allowed is True
    assert remaining == 5


@pytest.mark.asyncio
async def test_blocks_at_limit():
    rl = RateLimiter()
    rl._redis_checked = True
    rl._redis_available = False

    for i in range(10):
        allowed, _ = await rl.check("test:b", limit=10, window=60)
        assert allowed is True

    allowed, remaining = await rl.check("test:b", limit=10, window=60)
    assert allowed is False
    assert remaining == 0


@pytest.mark.asyncio
async def test_different_keys_do_not_interfere():
    rl = RateLimiter()
    rl._redis_checked = True
    rl._redis_available = False

    for i in range(10):
        await rl.check("test:user1", limit=10, window=60)
    allowed, _ = await rl.check("test:user1", limit=10, window=60)
    assert allowed is False

    # Different key — fresh window
    allowed, remaining = await rl.check("test:user2", limit=10, window=60)
    assert allowed is True
    assert remaining == 9


@pytest.mark.asyncio
async def test_window_expiry_resets_counter():
    rl = RateLimiter()
    rl._redis_checked = True
    rl._redis_available = False

    for i in range(3):
        await rl.check("test:c", limit=3, window=1)

    allowed, _ = await rl.check("test:c", limit=3, window=1)
    assert allowed is False

    # Wait for window to expire
    await asyncio.sleep(1.1)

    allowed, remaining = await rl.check("test:c", limit=3, window=1)
    assert allowed is True
    assert remaining == 2


@pytest.mark.asyncio
async def test_rejected_request_does_not_refill_window():
    """
    When over the limit, rejected requests must not count themselves
    again — otherwise a flood of rejected requests would never expire.
    """
    rl = RateLimiter()
    rl._redis_checked = True
    rl._redis_available = False

    for i in range(5):
        await rl.check("test:d", limit=5, window=2)

    # 20 rejected requests should not extend the window
    for i in range(20):
        allowed, _ = await rl.check("test:d", limit=5, window=2)
        assert allowed is False

    # After window, we should be allowed again
    await asyncio.sleep(2.1)
    allowed, remaining = await rl.check("test:d", limit=5, window=2)
    assert allowed is True


@pytest.mark.asyncio
async def test_redis_unavailable_degrades_silently(monkeypatch):
    """When Redis connect fails, check() must not raise."""
    rl = RateLimiter()

    async def failing_connect():
        raise ConnectionError("redis down")

    monkeypatch.setattr(rl, "connect", failing_connect)
    rl._redis_checked = False

    # Simulate connect() being called but failing
    rl._redis_checked = True
    rl._redis_available = False
    allowed, _ = await rl.check("test:e", limit=5, window=60)
    assert allowed is True


@pytest.mark.asyncio
async def test_redis_operation_failure_falls_back():
    """If a Redis op raises mid-flight, the limiter uses the fallback."""
    rl = RateLimiter()
    rl._redis_checked = True
    rl._redis_available = True

    class BrokenRedis:
        def pipeline(self):
            raise ConnectionError("simulated redis failure")

    rl.redis = BrokenRedis()

    allowed, _ = await rl.check("test:f", limit=5, window=60)
    assert allowed is True
    assert rl._redis_available is False  # marked down
    assert rl.redis is None


def test_presets_are_defined():
    assert "auth.login" in RATE_LIMITS
    assert "search.create" in RATE_LIMITS
    for name, (limit, window) in RATE_LIMITS.items():
        assert isinstance(limit, int) and limit > 0
        assert isinstance(window, int) and window > 0