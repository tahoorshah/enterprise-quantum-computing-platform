"""
Execution history for Module 2 - now backed by the persistence layer.
Public function signatures unchanged; internals delegate to persistence.
"""

from typing import List
from app.optimization.schemas import PortfolioOptimizationResult
from app.database import persistence

_MODULE = "portfolio_optimization"


def save_result(result: PortfolioOptimizationResult) -> None:
    persistence.save_execution(
        module=_MODULE,
        execution_id=result.execution_id,
        result_json=result.model_dump(mode="json"),
        subtype=None,
    )


def get_result(execution_id: str) -> PortfolioOptimizationResult | None:
    rec = persistence.get_execution(_MODULE, execution_id)
    if rec is None:
        return None
    return PortfolioOptimizationResult(**rec["result_json"])


def list_history() -> List[dict]:
    """Most recent first. Same dict shape as before."""
    records = persistence.list_executions(_MODULE)
    out = []
    for rec in records:
        data = rec["result_json"]
        out.append({
            "execution_id": data["execution_id"],
            "timestamp": data["timestamp"],
            "num_assets": data.get("result", {}).get("problem_setup", {}).get("num_assets"),
            "matched_classical_optimum": data.get("result", {}).get("comparison", {}).get("quantum_matched_classical_optimum"),
        })
    return out


def clear_history() -> int:
    return 0
