"""
Execution history for Module 3 - now backed by the persistence layer.
Public function signatures unchanged; internals delegate to persistence.
"""

from typing import List
from app.algorithms.schemas import AlgorithmResult
from app.database import persistence

_MODULE = "algorithms"


def save_result(result: AlgorithmResult) -> None:
    persistence.save_execution(
        module=_MODULE,
        execution_id=result.execution_id,
        result_json=result.model_dump(mode="json"),
        subtype=result.algorithm,  # grover / qft / qaoa / vqe
    )


def get_result(execution_id: str) -> AlgorithmResult | None:
    rec = persistence.get_execution(_MODULE, execution_id)
    if rec is None:
        return None
    return AlgorithmResult(**rec["result_json"])


def list_history() -> List[dict]:
    """Most recent first. Same dict shape as before: execution_id, algorithm, timestamp."""
    records = persistence.list_executions(_MODULE)
    return [
        {
            "execution_id": rec["result_json"]["execution_id"],
            "algorithm": rec["result_json"]["algorithm"],
            "timestamp": rec["result_json"]["timestamp"],
        }
        for rec in records
    ]


def clear_history() -> int:
    return 0
