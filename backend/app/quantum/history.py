"""
In-memory execution history for Module 1.

Deliberately simple for now — a Python dict, not a database. This gets
replaced with real Postgres persistence in a later step. Keeping this
in-memory first lets us prove Module 1's actual quantum logic works
before adding database complexity on top.

NOTE: this history is LOST every time the server restarts. That's
expected and fine for now — flag it clearly if it matters for a demo.
"""

from typing import Dict, List
from app.quantum.schemas import CircuitResult, HistorySummary

# execution_id -> full CircuitResult
_history_store: Dict[str, CircuitResult] = {}


def save_result(result: CircuitResult) -> None:
    _history_store[result.execution_id] = result


def get_result(execution_id: str) -> CircuitResult | None:
    return _history_store.get(execution_id)


def list_history() -> List[HistorySummary]:
    """Most recent first."""
    results = sorted(_history_store.values(), key=lambda r: r.timestamp, reverse=True)
    return [
        HistorySummary(
            execution_id=r.execution_id,
            timestamp=r.timestamp,
            num_qubits=r.num_qubits,
            num_gates=len(r.gates_applied),
            shots=r.shots,
        )
        for r in results
    ]


def clear_history() -> int:
    """Wipe everything. Returns count of deleted entries."""
    count = len(_history_store)
    _history_store.clear()
    return count
