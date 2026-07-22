"""
Execution history for Module 7 - backed by the shared persistence layer
(PostgreSQL when available, in-memory fallback otherwise). Mirrors the
pattern used by Modules 1, 2, and 3.
"""

from typing import List
from app.ml.schemas import MLComparisonResult
from app.database import persistence

_MODULE = "ml_portfolio"


def save_result(result: MLComparisonResult) -> None:
    persistence.save_execution(
        module=_MODULE,
        execution_id=result.execution_id,
        result_json=result.model_dump(mode="json"),
        subtype=None,
    )


def get_result(execution_id: str) -> MLComparisonResult | None:
    rec = persistence.get_execution(_MODULE, execution_id)
    if rec is None:
        return None
    return MLComparisonResult(**rec["result_json"])


def list_history() -> List[dict]:
    """Most recent first."""
    records = persistence.list_executions(_MODULE)
    out = []
    for rec in records:
        data = rec["result_json"]
        result = data.get("result", {})
        asset_names = result.get("evaluation_market", {}).get("asset_names", [])
        out.append({
            "execution_id": data["execution_id"],
            "timestamp": data["timestamp"],
            "num_assets": len(asset_names) if asset_names else None,
            "ml_matched_optimum": result.get("comparison", {}).get("ml_matched_exact_optimum"),
            "test_accuracy": result.get("training", {}).get("test_accuracy"),
        })
    return out
