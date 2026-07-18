"""
Module 3 - Quantum Algorithm Demonstration Platform: API endpoints.

Endpoints:
    POST /api/algorithms/grover   - Grover's search
    POST /api/algorithms/qft      - Quantum Fourier Transform demo
    POST /api/algorithms/qaoa     - QAOA on Max-Cut
    POST /api/algorithms/vqe      - VQE ground-state energy
    GET  /api/algorithms/history  - list past executions of any algorithm
"""

import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from app.algorithms.schemas import GroverRequest, QFTRequest, QAOARequest, VQERequest, AlgorithmResult
from app.algorithms.grover import run_grover_search
from app.algorithms.qft import demonstrate_qft
from app.algorithms.qaoa import run_qaoa_maxcut
from app.algorithms.vqe import run_vqe
from app.algorithms import history

router = APIRouter()


def _wrap_and_save(algorithm_name: str, result_data: dict) -> AlgorithmResult:
    result = AlgorithmResult(
        algorithm=algorithm_name,
        execution_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc).isoformat(),
        result=result_data,
    )
    history.save_result(result)
    return result


@router.post("/grover", response_model=AlgorithmResult)
def grover_search(request: GroverRequest):
    try:
        result_data = run_grover_search(request.num_qubits, request.marked_state, request.shots)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grover execution failed: {e}")
    return _wrap_and_save("grover", result_data)


@router.post("/qft", response_model=AlgorithmResult)
def qft_demo(request: QFTRequest):
    try:
        result_data = demonstrate_qft(request.num_qubits, request.input_state, request.shots)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QFT execution failed: {e}")
    return _wrap_and_save("qft", result_data)


@router.post("/qaoa", response_model=AlgorithmResult)
def qaoa_maxcut(request: QAOARequest):
    try:
        edges = [tuple(e) for e in request.edges]
        result_data = run_qaoa_maxcut(
            edges, request.num_nodes, p=request.p_layers,
            shots=request.shots, max_iterations=request.max_iterations
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QAOA execution failed: {e}")
    return _wrap_and_save("qaoa", result_data)


@router.post("/vqe", response_model=AlgorithmResult)
def vqe_ground_state(request: VQERequest):
    try:
        result_data = run_vqe(request.num_qubits, request.max_iterations)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"VQE execution failed: {e}")
    return _wrap_and_save("vqe", result_data)


@router.get("/history")
def get_history():
    return history.list_history()


@router.get("/history/{execution_id}", response_model=AlgorithmResult)
def get_history_detail(execution_id: str):
    result = history.get_result(execution_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"No execution found with id: {execution_id}")
    return result
