"""
Module 2 - Financial Portfolio Optimization Platform: API endpoints.

Endpoints:
    POST /api/optimization/portfolio       - run classical vs QAOA portfolio optimization
    GET  /api/optimization/history         - list past optimization runs
    GET  /api/optimization/history/{id}    - full detail of one past run
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.optimization.schemas import PortfolioOptimizationRequest, PortfolioOptimizationResult
from app.optimization.qaoa_portfolio import run_portfolio_optimization
from app.optimization import history

router = APIRouter()


@router.post("/portfolio", response_model=PortfolioOptimizationResult)
def optimize_portfolio(request: PortfolioOptimizationRequest):
    if request.budget >= request.num_assets:
        raise HTTPException(
            status_code=422,
            detail=f"budget ({request.budget}) must be less than num_assets ({request.num_assets})"
        )

    try:
        result_data = run_portfolio_optimization(
            num_assets=request.num_assets,
            budget=request.budget,
            risk_aversion=request.risk_aversion,
            penalty_weight=request.penalty_weight,
            shots=request.shots,
            max_iterations=request.max_iterations,
            p_layers=request.p_layers,
            seed=request.seed,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {e}")

    result = PortfolioOptimizationResult(
        execution_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        result=result_data,
    )
    history.save_result(result)
    return result


@router.get("/history")
def get_history():
    return history.list_history()


@router.get("/history/{execution_id}", response_model=PortfolioOptimizationResult)
def get_history_detail(execution_id: str):
    result = history.get_result(execution_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No execution found with id: {execution_id}")
    return result
