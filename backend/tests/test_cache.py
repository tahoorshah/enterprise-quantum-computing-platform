"""
Tests for the Redis cache-aside layer (app/cache) and its wiring into
the portfolio optimization (Module 2) and market analytics endpoints.

Redis isn't running in the test environment, so these tests substitute a
tiny in-process fake client for app.cache.redis_client's module-level
client rather than requiring a real Redis instance - this still
exercises the exact get_cached/set_cached code path a real connection
would, including the graceful-degradation branches when Redis is absent
or errors on use.
"""

import redis as redis_module
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.cache import redis_client
from app.cache.cache import make_cache_key, get_cached, set_cached
import app.analytics.router as analytics_router
import app.optimization.router as optimization_router

client = TestClient(app)


class FakeRedis:
    """Minimal in-memory stand-in for the get/setex calls cache.py makes."""

    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def setex(self, key, ttl, value):
        self.store[key] = value


class BrokenRedis:
    """Simulates Redis becoming unreachable mid-session (errors on every call)."""

    def get(self, key):
        raise ConnectionError("simulated redis outage")

    def setex(self, key, ttl, value):
        raise ConnectionError("simulated redis outage")


class UnpingableRedis:
    """Simulates Redis being unreachable at startup (connect/ping fails)."""

    def ping(self):
        raise redis_module.ConnectionError("simulated: redis unreachable")


@pytest.fixture(autouse=True)
def _reset_redis_state():
    """Every test starts from a known, disconnected cache state and the
    module-level globals are restored afterwards so other test files
    (which never touch app.cache) aren't affected by ordering."""
    original_client = redis_client._client
    original_available = redis_client.REDIS_AVAILABLE
    redis_client._client = None
    redis_client.REDIS_AVAILABLE = False
    yield
    redis_client._client = original_client
    redis_client.REDIS_AVAILABLE = original_available


def _enable_fake_redis():
    redis_client._client = FakeRedis()
    redis_client.REDIS_AVAILABLE = True


# ---- make_cache_key ----

def test_cache_key_is_deterministic_regardless_of_kwarg_order():
    assert make_cache_key("x", a=1, b=2) == make_cache_key("x", b=2, a=1)


def test_cache_key_differs_for_different_params():
    assert make_cache_key("x", a=1) != make_cache_key("x", a=2)


def test_cache_key_differs_for_different_prefix():
    assert make_cache_key("x", a=1) != make_cache_key("y", a=1)


# ---- init_redis(): unreachable at startup ----

def test_init_redis_falls_back_gracefully_when_unreachable(monkeypatch):
    monkeypatch.setattr(redis_client.redis.Redis, "from_url", lambda *a, **k: UnpingableRedis())

    result = redis_client.init_redis()

    assert result is False
    assert redis_client.REDIS_AVAILABLE is False
    assert redis_client.get_client() is None


# ---- get_cached / set_cached: direct unit coverage ----

def test_set_then_get_cached_round_trips():
    _enable_fake_redis()
    key = make_cache_key("unit_test", n=1)

    assert get_cached(key) is None  # miss before set
    set_cached(key, {"value": 42}, ttl_seconds=60)
    assert get_cached(key) == {"value": 42}


def test_get_cached_returns_none_when_redis_unavailable():
    # REDIS_AVAILABLE is False by default from the fixture
    assert get_cached(make_cache_key("unit_test", n=1)) is None


def test_set_cached_is_noop_when_redis_unavailable():
    key = make_cache_key("unit_test", n=2)
    set_cached(key, {"value": 1}, ttl_seconds=60)  # must not raise
    assert get_cached(key) is None


def test_get_and_set_cached_degrade_gracefully_on_redis_errors():
    """Redis reachable at startup but erroring on use (e.g. dropped connection) must not break callers."""
    redis_client._client = BrokenRedis()
    redis_client.REDIS_AVAILABLE = True

    key = make_cache_key("unit_test", n=3)
    assert get_cached(key) is None  # doesn't raise
    set_cached(key, {"value": 1}, ttl_seconds=60)  # doesn't raise


# ---- Analytics endpoint: cache hit ----

def test_analytics_endpoint_cache_hit_skips_recompute(monkeypatch):
    _enable_fake_redis()

    call_count = {"n": 0}
    original = analytics_router.market_summary

    def counting_market_summary(*args, **kwargs):
        call_count["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(analytics_router, "market_summary", counting_market_summary)

    r1 = client.get("/api/analytics/market/5?seed=7")
    r2 = client.get("/api/analytics/market/5?seed=7")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert call_count["n"] == 1  # second request served from cache, not recomputed


def test_analytics_endpoint_different_params_are_not_conflated(monkeypatch):
    _enable_fake_redis()

    r5 = client.get("/api/analytics/market/5?seed=7")
    r6 = client.get("/api/analytics/market/6?seed=7")

    assert len(r5.json()["assets"]) == 5
    assert len(r6.json()["assets"]) == 6


# ---- Analytics endpoint: Redis-unavailable fallback ----

def test_analytics_endpoint_works_when_redis_unavailable(monkeypatch):
    # fixture already leaves REDIS_AVAILABLE False / no client
    call_count = {"n": 0}
    original = analytics_router.market_summary

    def counting_market_summary(*args, **kwargs):
        call_count["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(analytics_router, "market_summary", counting_market_summary)

    r1 = client.get("/api/analytics/market/5?seed=11")
    r2 = client.get("/api/analytics/market/5?seed=11")

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json() == r2.json()
    assert call_count["n"] == 2  # no cache available: computed directly both times


def test_analytics_endpoint_survives_redis_erroring_mid_session():
    """Redis was reachable at startup but every call now raises - the
    endpoint must still serve a correct response instead of 500ing."""
    redis_client._client = BrokenRedis()
    redis_client.REDIS_AVAILABLE = True

    r = client.get("/api/analytics/market/5?seed=13")

    assert r.status_code == 200
    assert len(r.json()["assets"]) == 5


# ---- Portfolio optimization endpoint: cache hit ----

def test_portfolio_endpoint_cache_hit_skips_recompute(monkeypatch):
    _enable_fake_redis()

    call_count = {"n": 0}
    original = optimization_router.run_portfolio_optimization

    def counting_run(*args, **kwargs):
        call_count["n"] += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(optimization_router, "run_portfolio_optimization", counting_run)

    payload = {
        "num_assets": 4, "budget": 2, "shots": 256,
        "max_iterations": 15, "seed": 99, "trials": 1,
    }
    r1 = client.post("/api/optimization/portfolio", json=payload)
    r2 = client.post("/api/optimization/portfolio", json=payload)

    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json()["result"] == r2.json()["result"]
    assert call_count["n"] == 1  # second request served from cache, not recomputed


# ---- Portfolio optimization endpoint: Redis-unavailable fallback ----

def test_portfolio_endpoint_works_when_redis_unavailable():
    # fixture already leaves REDIS_AVAILABLE False / no client
    payload = {
        "num_assets": 4, "budget": 2, "shots": 256,
        "max_iterations": 15, "seed": 100, "trials": 1,
    }
    r = client.post("/api/optimization/portfolio", json=payload)
    assert r.status_code == 200


def test_portfolio_endpoint_survives_redis_erroring_mid_session():
    redis_client._client = BrokenRedis()
    redis_client.REDIS_AVAILABLE = True

    payload = {
        "num_assets": 4, "budget": 2, "shots": 256,
        "max_iterations": 15, "seed": 101, "trials": 1,
    }
    r = client.post("/api/optimization/portfolio", json=payload)
    assert r.status_code == 200


# ---- /health surfaces cache status ----

def test_health_reports_cache_unavailable_by_default():
    r = client.get("/health")
    body = r.json()
    assert body["cache"] is False
    assert body["cache_backend"].startswith("none")


def test_health_reports_cache_available_when_connected():
    _enable_fake_redis()
    r = client.get("/health")
    body = r.json()
    assert body["cache"] is True
    assert body["cache_backend"] == "redis"
