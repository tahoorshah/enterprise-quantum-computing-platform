"""In-memory execution history for Module 2 (same pattern as Modules 1 and 3)."""

from typing import Dict, List
from app.optimization.schemas import PortfolioOptimizationResult

_history_store: Dict[str, PortfolioOptimizationResult] = {}


def save_result(result: PortfolioOptimizationResult) -> None:
    _history_store[result.execution_id] = result


def get_result(execution_id: str) -> PortfolioOptimizationResult | None:
    return _history_store.get(execution_id)


def list_history() -> List[dict]:
    results = sorted(_history_store.values(), key=lambda r: r.timestamp, reverse=True)
    return [
        {
            "execution_id": r.execution_id,
            "timestamp": r.timestamp,
            "num_assets": r.result.get("problem_setup", {}).get("num_assets"),
            "matched_classical_optimum": r.result.get("comparison", {}).get("quantum_matched_classical_optimum"),
        }
        for r in results
    ]


def clear_history() -> int:
    count = len(_history_store)
    _history_store.clear()
    return count
