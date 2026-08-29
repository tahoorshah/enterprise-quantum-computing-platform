"""
Generic cache-aside layer over Redis, used by any module with an
expensive, parameter-deterministic computation (QAOA portfolio
optimization, market analytics).

Cache-aside: callers first call get_cached(key); on a miss they compute
the result themselves and call set_cached(key, result, ttl) to populate
it for next time. This module never computes anything itself - that
keeps it reusable across unrelated result shapes (a portfolio
optimization payload looks nothing like a market analytics table).

DEGRADATION: every operation here is best-effort. If Redis is
unreachable - either because init_redis() never connected, or because a
previously-healthy connection drops mid-session - get_cached returns
None (forcing a live compute, exactly like a cache miss) and set_cached
is a silent no-op. Nothing here ever raises into a caller, mirroring how
app/database/persistence.py falls back to in-memory storage on a DB
failure rather than taking the endpoint down.
"""

import hashlib
import json
import logging
from typing import Any, Optional

from fastapi.encoders import jsonable_encoder

from app.cache import redis_client

logger = logging.getLogger("qft.cache")


def make_cache_key(prefix: str, **params: Any) -> str:
    """
    Deterministic cache key derived from request parameters: identical
    params (regardless of keyword-argument order) always hash to the same
    key, and any different param produces a different one.
    """
    payload = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"qft:cache:{prefix}:{digest}"


def get_cached(key: str) -> Optional[Any]:
    """Return the cached value for `key`, or None on a miss or if caching is unavailable."""
    client = redis_client.get_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as e:
        logger.warning("Redis GET failed (%s); computing directly.", type(e).__name__)
        return None


def set_cached(key: str, value: Any, ttl_seconds: int) -> None:
    """Store `value` under `key` with a TTL. No-op if caching is unavailable."""
    client = redis_client.get_client()
    if client is None:
        return
    try:
        # jsonable_encoder mirrors the conversion FastAPI already applies
        # when serializing the same value as an HTTP response, so anything
        # that's a valid endpoint response (numpy scalars, Qiskit Counts,
        # etc.) is guaranteed to also be cacheable here.
        client.setex(key, ttl_seconds, json.dumps(jsonable_encoder(value)))
    except Exception as e:
        logger.warning("Redis SET failed (%s); result not cached.", type(e).__name__)
