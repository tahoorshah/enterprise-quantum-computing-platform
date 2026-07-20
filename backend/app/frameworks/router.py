"""
Module 6 - Multi-Framework Quantum Demonstration: API endpoint.

Exposes the cross-framework (Qiskit / PennyLane / Cirq) Bell-state
demonstration, satisfying the capstone stack requirement for all three
quantum frameworks.

Endpoint:
    GET /api/frameworks/compare   - run the Bell state on all 3 frameworks
"""

from fastapi import APIRouter, HTTPException, Query
from app.frameworks.multi_framework import run_all_frameworks

router = APIRouter()


@router.get("/compare")
def compare_frameworks(shots: int = Query(default=1024, ge=64, le=8192)):
    """
    Run the same Bell-state circuit on Qiskit, PennyLane, and Cirq and
    return each framework's measurement counts side by side, confirming
    they all produce the same (entangled) result.
    """
    try:
        return run_all_frameworks(shots=shots)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Framework comparison failed: {e}")
