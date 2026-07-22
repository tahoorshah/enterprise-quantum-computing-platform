"""
Module 7 - Classical Machine Learning vs Quantum Optimization: API endpoints.

Endpoints:
    POST /api/ml/compare              - train ML on simulated markets, compare vs exact optimum
    GET  /api/ml/history              - list past ML comparison runs
    GET  /api/ml/history/{id}         - full detail of one past run
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.ml.schemas import MLComparisonRequest, MLComparisonResult
from app.ml.ml_selector import run_ml_vs_quantum
from app.ml import history
from app.dashboard import metrics

router = APIRouter()


@router.post("/compare", response_model=MLComparisonResult)
def compare_ml_vs_quantum(request: MLComparisonRequest):
    if request.budget >= request.num_assets:
        metrics.record_attempt("ml_portfolio", success=False)
        raise HTTPException(
            status_code=422,
            detail=f"budget ({request.budget}) must be less than num_assets ({request.num_assets})"
        )

    try:
        result_data = run_ml_vs_quantum(
            num_assets=request.num_assets,
            budget=request.budget,
            risk_aversion=request.risk_aversion,
            penalty_weight=request.penalty_weight,
            num_scenarios=request.num_scenarios,
            eval_seed=request.eval_seed,
        )
    except ValueError as e:
        metrics.record_attempt("ml_portfolio", success=False)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        metrics.record_attempt("ml_portfolio", success=False)
        raise HTTPException(status_code=500, detail=f"ML comparison failed: {e}")

    metrics.record_attempt("ml_portfolio", success=True)
    result = MLComparisonResult(
        execution_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        result=result_data,
    )
    history.save_result(result)
    return result


@router.get("/history")
def get_history():
    return history.list_history()


@router.get("/history/{execution_id}", response_model=MLComparisonResult)
def get_history_detail(execution_id: str):
    result = history.get_result(execution_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No execution found with id: {execution_id}")
    return result
