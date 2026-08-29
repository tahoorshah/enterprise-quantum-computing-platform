"""
Tests for API rate limiting (app/rate_limit.py, a slowapi-based security
control): a strict per-IP limit on POST /api/auth/login, and a looser
per-IP/per-route default limit on every other /api/* route.

Rate-limit counters live in slowapi's in-memory storage for the whole
app's lifetime, shared by the single TestClient/app instance every test
file in this suite reuses. An autouse fixture resets that storage before
each test here so these tests are deterministic regardless of how many
requests earlier test files already made against the same endpoints.
"""

from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import limiter, DEFAULT_API_RATE_LIMIT, LOGIN_RATE_LIMIT

client = TestClient(app)


def setup_function(_):
    limiter._storage.reset()


# ---- Strict login limit: brute-force resistance ----

def test_login_limit_value_is_strict():
    """5/minute - low enough to make password guessing impractical."""
    assert LOGIN_RATE_LIMIT == "5/minute"


def test_login_rate_limit_triggers_429_after_repeated_attempts():
    max_attempts = int(LOGIN_RATE_LIMIT.split("/")[0])

    responses = [
        client.post(
            "/api/auth/login",
            data={"username": "analyst", "password": "wrong-password"},
        )
        for _ in range(max_attempts)
    ]
    # All allowed attempts fail on bad credentials, not on the rate limit.
    for r in responses:
        assert r.status_code == 401

    limited = client.post(
        "/api/auth/login",
        data={"username": "analyst", "password": "wrong-password"},
    )
    assert limited.status_code == 429
    body = limited.json()
    assert "detail" in body
    assert "Rate limit exceeded" in body["detail"]


def test_login_rate_limit_also_applies_to_correct_credentials():
    """The limit guards the endpoint itself, not just failed attempts -
    otherwise an attacker could distinguish valid accounts by which
    requests get rate-limited."""
    max_attempts = int(LOGIN_RATE_LIMIT.split("/")[0])

    for _ in range(max_attempts):
        client.post(
            "/api/auth/login",
            data={"username": "analyst", "password": "changeme_demo_only"},
        )

    limited = client.post(
        "/api/auth/login",
        data={"username": "analyst", "password": "changeme_demo_only"},
    )
    assert limited.status_code == 429


# ---- Default limit: applied to the other /api routes ----

def test_default_rate_limit_value_is_sensible():
    assert DEFAULT_API_RATE_LIMIT == "100/minute"


def test_default_rate_limit_triggers_429_on_a_representative_api_route():
    """/api/quantum/gates is a cheap, static endpoint - a good stand-in
    for confirming the default-limit dependency wired onto every
    non-auth router (main.py's `_default_deps`) actually fires."""
    max_requests = int(DEFAULT_API_RATE_LIMIT.split("/")[0])

    for _ in range(max_requests):
        r = client.get("/api/quantum/gates")
        assert r.status_code == 200

    limited = client.get("/api/quantum/gates")
    assert limited.status_code == 429
    body = limited.json()
    assert "detail" in body
    assert "Rate limit exceeded" in body["detail"]


def test_default_rate_limit_is_tracked_independently_per_route():
    """Exhausting one route's budget must not affect a different route -
    the limit key is per-URL, not one pooled counter for the whole API."""
    max_requests = int(DEFAULT_API_RATE_LIMIT.split("/")[0])

    for _ in range(max_requests):
        client.get("/api/quantum/gates")
    assert client.get("/api/quantum/gates").status_code == 429

    # A different endpoint should be unaffected.
    assert client.get("/api/pqc/algorithms/classical").status_code == 200


# ---- 429 response shape ----

def test_health_and_root_are_not_rate_limited():
    """Infra endpoints (liveness probes, Prometheus scraping) never carry
    the default limit dependency, since it's only wired onto the /api/*
    module routers in main.py."""
    max_requests = int(DEFAULT_API_RATE_LIMIT.split("/")[0])
    for _ in range(max_requests + 5):
        assert client.get("/health").status_code == 200
