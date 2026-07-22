"""
Market Analytics endpoints - Pandas-structured market data and
Matplotlib-generated static charts for reporting.

Endpoints:
    GET /api/analytics/market/{num_assets}        - labelled market table + summary stats (Pandas)
    GET /api/analytics/market/{num_assets}/chart  - risk-return scatter as base64 PNG (Matplotlib)
"""

from fastapi import APIRouter, HTTPException, Query
from app.analytics.market_analytics import market_summary, risk_return_chart_base64

router = APIRouter()


@router.get("/market/{num_assets}")
def get_market_analytics(num_assets: int, seed: int = Query(default=42)):
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    return market_summary(num_assets, seed=seed)


@router.get("/market/{num_assets}/chart")
def get_market_chart(num_assets: int, seed: int = Query(default=42)):
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    png_b64 = risk_return_chart_base64(num_assets, seed=seed)
    return {
        "num_assets": num_assets,
        "seed": seed,
        "format": "image/png;base64",
        "image_base64": png_b64,
    }
