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


@router.get("/market/{num_assets}/interactive")
def get_market_interactive_chart(num_assets: int, seed: int = Query(default=42)):
    """
    Interactive Plotly figure JSON. The frontend hydrates this into a chart
    supporting hover, zoom, and pan - the exploratory counterpart to the
    static Matplotlib PNG served by /chart, which targets report export.
    """
    if num_assets < 2 or num_assets > 20:
        raise HTTPException(status_code=422, detail="num_assets must be between 2 and 20")
    return {
        "num_assets": num_assets,
        "seed": seed,
        "format": "plotly-figure-json",
        "figure": risk_return_figure_json(num_assets, seed=seed),
    }
