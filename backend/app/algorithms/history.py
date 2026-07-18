"""In-memory execution history for Module 3 (same pattern as Module 1)."""

from typing import Dict, List
from app.algorithms.schemas import AlgorithmResult

_history_store: Dict[str, AlgorithmResult] = {}


def save_result(result: AlgorithmResult) -> None:
    _history_store[result.execution_id] = result


def get_result(execution_id: str) -> AlgorithmResult | None:
    return _history_store.get(execution_id)


def list_history() -> List[dict]:
    results = sorted(_history_store.values(), key=lambda r: r.timestamp, reverse=True)
    return [
        {
            "execution_id": r.execution_id,
            "algorithm": r.algorithm,
            "timestamp": r.timestamp,
        }
        for r in results
    ]


def clear_history() -> int:
    count = len(_history_store)
    _history_store.clear()
    return count
