"""
Market Analytics endpoints - Pandas-structured market data and
Matplotlib-generated static charts for reporting.

Endpoints:
    GET /api/analytics/market/{num_assets}        - labelled market table + summary stats (Pandas)
    GET /api/analytics/market/{num_assets}/chart  - risk-return scatter as base64 PNG (Matplotlib)
    GET /api/analytics/market/{num_assets}/interactive - interactive Plotly figure JSON
"""

from fastapi import APIRouter, HTTPException, Query
from app.analytics.market_analytics import market_summary, risk_return_chart_base64
from app.analytics.plotly_charts import risk_return_figure_json
from app.cache.cache import make_cache_key, get_cached, set_cached

router = APIRouter()

# Market data is a pure function of (num_assets, seed), so a cached
# response is never stale in any way that matters for this simulated
# demo market. 15 minutes just bounds how long a cache entry lingers
# after nobody's requesting that combination any more.
_ANALYTICS_CACHE_TTL_SECONDS = 900


@router.get("/market/{num_assets}")
def get_market_analytics(num_assets: int, seed: int = Query(default=42)):
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    cache_key = make_cache_key("analytics_market", num_assets=num_assets, seed=seed)
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    result = market_summary(num_assets, seed=seed)
    set_cached(cache_key, result, _ANALYTICS_CACHE_TTL_SECONDS)
    return result


@router.get("/market/{num_assets}/chart")
def get_market_chart(num_assets: int, seed: int = Query(default=42)):
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    cache_key = make_cache_key("analytics_market_chart", num_assets=num_assets, seed=seed)
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    png_b64 = risk_return_chart_base64(num_assets, seed=seed)
    result = {
        "num_assets": num_assets,
        "seed": seed,
        "format": "image/png;base64",
        "image_base64": png_b64,
    }
    set_cached(cache_key, result, _ANALYTICS_CACHE_TTL_SECONDS)
    return result


@router.get("/market/{num_assets}/interactive")
def get_market_interactive_chart(num_assets: int, seed: int = Query(default=42)):
    """
    Interactive Plotly figure JSON. The frontend hydrates this into a chart
    supporting hover, zoom, and pan - the exploratory counterpart to the
    static Matplotlib PNG served by /chart, which targets report export.
    """
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    cache_key = make_cache_key("analytics_market_interactive", num_assets=num_assets, seed=seed)
    cached = get_cached(cache_key)
    if cached is not None:
        return cached
    result = {
        "num_assets": num_assets,
        "seed": seed,
        "format": "plotly-figure-json",
        "figure": risk_return_figure_json(num_assets, seed=seed),
    }
    set_cached(cache_key, result, _ANALYTICS_CACHE_TTL_SECONDS)
    return result
