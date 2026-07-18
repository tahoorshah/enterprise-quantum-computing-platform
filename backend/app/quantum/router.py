"""
Module 1 - Quantum Circuit Design Platform: API endpoints.

Endpoints:
    POST /api/quantum/execute        - build + run a circuit, return results
    GET  /api/quantum/history        - list past executions (summary)
    GET  /api/quantum/history/{id}   - full detail of one past execution
    DELETE /api/quantum/history      - clear all history
    GET  /api/quantum/gates          - list supported gates (for building a UI later)
"""

from fastapi import APIRouter, HTTPException

from app.quantum.schemas import CircuitRequest, CircuitResult, HistorySummary, SUPPORTED_GATES
from app.quantum.circuit_builder import execute_circuit_request, InvalidCircuitError
from app.quantum import history
from app.dashboard import metrics

router = APIRouter()


@router.post("/execute", response_model=CircuitResult)
def execute_circuit(request: CircuitRequest):
    """
    Build a quantum circuit from the given gates, run it on AerSimulator,
    and return the measurement counts + probabilities.
    """
    try:
        result = execute_circuit_request(request)
    except InvalidCircuitError as e:
        metrics.record_attempt("quantum_circuits", success=False)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        metrics.record_attempt("quantum_circuits", success=False)
        raise HTTPException(status_code=500, detail=f"Circuit execution failed: {e}")

    metrics.record_attempt("quantum_circuits", success=True)
    history.save_result(result)
    return result


@router.get("/history", response_model=list[HistorySummary])
def get_history():
    """List all past circuit executions, most recent first."""
    return history.list_history()


@router.get("/history/{execution_id}", response_model=CircuitResult)
def get_history_detail(execution_id: str):
    """Get full detail (diagram, counts, probabilities) for one past execution."""
    result = history.get_result(execution_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No execution found with id: {execution_id}")
    return result


@router.delete("/history")
def clear_history():
    """Wipe all execution history. Useful for demos/testing."""
    count = history.clear_history()
    return {"deleted": count}


@router.get("/gates")
def list_supported_gates():
    """List all supported gates and their requirements — useful for building a frontend form."""
    return SUPPORTED_GATES
