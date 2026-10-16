"""
Module 6 - Multi-Framework Quantum Demonstration: API endpoints.

Endpoints:
    GET /api/frameworks/compare         - both demos on all 3 frameworks + validation
    GET /api/frameworks/bell            - Bell state comparison only
    GET /api/frameworks/superposition   - superposition comparison only
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from app.frameworks.multi_framework import (
    run_all_frameworks,
    run_bell_comparison,
    run_superposition_comparison,
)

router = APIRouter()


@router.get("/compare")
def compare_frameworks(shots: int = Query(default=1024, ge=64, le=8192), seed: Optional[int] = Query(default=None)):
    try:
        return run_all_frameworks(shots=shots, seed=seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Framework comparison failed: {e}")


@router.get("/bell")
def compare_bell(shots: int = Query(default=1024, ge=64, le=8192), seed: Optional[int] = Query(default=None)):
    try:
        return run_bell_comparison(shots=shots, seed=seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bell comparison failed: {e}")


@router.get("/superposition")
def compare_superposition(shots: int = Query(default=1024, ge=64, le=8192), seed: Optional[int] = Query(default=None)):
    try:
        return run_superposition_comparison(shots=shots, seed=seed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Superposition comparison failed: {e}")
