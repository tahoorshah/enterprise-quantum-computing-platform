"""
Execution history for Module 1 - now backed by the persistence layer
(PostgreSQL when available, in-memory fallback otherwise).

Public function signatures (save_result, get_result, list_history,
clear_history) are UNCHANGED so the router doesn't need modifying. Only
the internals now delegate to app.database.persistence.
"""

from typing import List
from app.quantum.schemas import CircuitResult, HistorySummary
from app.database import persistence

_MODULE = "quantum_circuits"


def save_result(result: CircuitResult) -> None:
    # Store the full result as JSON via the persistence layer.
    # model_dump(mode="json") makes datetimes etc. JSON-serializable.
    persistence.save_execution(
        module=_MODULE,
        execution_id=result.execution_id,
        result_json=result.model_dump(mode="json"),
        subtype=None,
    )


def get_result(execution_id: str) -> CircuitResult | None:
    rec = persistence.get_execution(_MODULE, execution_id)
    if rec is None:
        return None
    return CircuitResult(**rec["result_json"])


def list_history() -> List[HistorySummary]:
    """Most recent first. Returns HistorySummary objects, same as before."""
    records = persistence.list_executions(_MODULE)
    summaries = []
    for rec in records:
        data = rec["result_json"]
        summaries.append(
            HistorySummary(
                execution_id=data["execution_id"],
                timestamp=data["timestamp"],
                num_qubits=data["num_qubits"],
                num_gates=len(data["gates_applied"]),
                shots=data["shots"],
            )
        )
    return summaries


def clear_history() -> int:
    """Kept for API compatibility. With persistence, clearing is a no-op
    stub that reports 0 - we don't want an API call wiping the real
    database. (A dedicated admin path could be added later if needed.)"""
    return 0
