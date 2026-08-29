"""
API rate limiting - a security control against brute-force and abuse,
built on slowapi (which wraps the `limits` library).

Two tiers, sharing one Limiter instance:

  - LOGIN_RATE_LIMIT: a strict per-IP limit applied directly to
    POST /api/auth/login via @limiter.limit(), to resist credential-
    stuffing / brute-force password guessing.
  - DEFAULT_API_RATE_LIMIT: a looser per-IP, per-route limit applied to
    every other /api/* route via the `enforce_default_rate_limit`
    dependency below. Add `Depends(enforce_default_rate_limit)` to a
    router's `include_router(..., dependencies=[...])` list - the same
    wiring pattern main.py already uses for `Depends(get_current_user)` -
    and every endpoint on that router picks up the default limit without
    touching individual endpoint functions.

Rate-limit state lives in slowapi's default in-memory storage: per
process, not shared across replicas. That's a real limitation in the
Kubernetes deployment (infra/k8s/), where multiple backend pods would
each enforce the limit independently rather than sharing one global
counter - acceptable for this capstone POC (a determined attacker
distributed across pods could exceed the nominal limit), but worth
knowing if this were hardened further: `Limiter(storage_uri="redis://...")`
would share counters across pods using the Redis instance app/cache/
already talks to.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Generous enough for normal interactive UI use (including dashboard
# polling) while still bounding a runaway client from monopolising the
# shared quantum simulator or the DB/cache behind it.
DEFAULT_API_RATE_LIMIT = "100/minute"

# A legitimate user rarely needs more than a couple of login attempts
# per minute; this is low enough to make password guessing impractical
# without locking out someone who mistypes their password once or twice.
LOGIN_RATE_LIMIT = "5/minute"


@limiter.limit(DEFAULT_API_RATE_LIMIT)
async def enforce_default_rate_limit(request: Request) -> None:
    """
    FastAPI dependency that enforces DEFAULT_API_RATE_LIMIT wherever it's
    added to a router's `dependencies=[...]`. Returns nothing - it's used
    purely for the side effect of raising RateLimitExceeded when the
    caller's per-route budget is exhausted.
    """
    return None


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """
    Returns the same {"detail": ...} error shape every other error
    response in this API already uses (see the 401/422/500 handlers
    throughout the routers), instead of slowapi's default
    {"error": ...} shape - so the frontend's existing
    `data.detail || "Request failed (...)"` handling in api.js surfaces
    this message with no special-casing for 429s.
    """
    response = JSONResponse(
        status_code=429,
        content={
            "detail": (
                f"Rate limit exceeded ({exc.detail}). "
                "Please slow down and try again shortly."
            )
        },
    )
    return limiter._inject_headers(response, request.state.view_rate_limit)
