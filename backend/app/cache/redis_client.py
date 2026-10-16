"""
Redis connection setup for the cache-aside layer.

DESIGN: same graceful-degradation pattern as app/database/connection.py.
If Redis is reachable at startup, caching is enabled. If it is NOT
reachable (misconfigured, down, or running outside Docker without a
Redis instance), the platform logs a warning and every cache lookup/
write becomes a silent no-op - endpoints fall back to computing
directly, exactly as the DB layer falls back to in-memory storage. A
cache is a performance optimization here, never a correctness
dependency, so nothing in this module raises.

REDIS_URL comes from the environment (set in .env / docker-compose),
defaulting to a local Redis if unset.
"""

import os
import logging
from typing import Optional

import redis

logger = logging.getLogger("qft.cache")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# These get set by init_redis(). If Redis is unreachable, _client stays
# None and REDIS_AVAILABLE stays False, so callers know to skip caching.
_client: Optional["redis.Redis"] = None
REDIS_AVAILABLE = False


def init_redis() -> bool:
    """
    Try to connect to Redis. Returns True if it's reachable, False if
    callers should treat the cache as unavailable. Never raises - a
    Redis problem must not crash the app.
    """
    global _client, REDIS_AVAILABLE

    try:
        client = redis.Redis.from_url(
            REDIS_URL,
            socket_connect_timeout=2,
            socket_timeout=2,
            decode_responses=True,
        )
        client.ping()  # from_url alone is lazy; ping actually exercises the connection
        _client = client
        REDIS_AVAILABLE = True
        logger.info("Redis connected: caching ENABLED.")
        return True
    except Exception as e:
        _client = None
        REDIS_AVAILABLE = False
        logger.warning(
            "Redis unavailable (%s). Caching DISABLED; endpoints will "
            "compute results directly.", type(e).__name__
        )
        return False


def get_client() -> Optional["redis.Redis"]:
    """Return the Redis client, or None if unavailable - callers must handle None."""
    if not REDIS_AVAILABLE:
        return None
    return _client
