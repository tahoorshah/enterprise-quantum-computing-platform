"""
Shared execution metrics, tracked across Modules 1, 2, and 3.

WHY THIS EXISTS: each module's history store (history.py in quantum/,
algorithms/, optimization/) only saves SUCCESSFUL executions - failed
requests (bad gate name, invalid qubit index, etc.) raise an HTTPException
and are never persisted anywhere. If Module 4's "execution success rate"
KPI only looked at those history stores, it would always report 100% -
which is misleading, not an honest metric. This module tracks BOTH
successes and failures so the dashboard can report a genuine rate.
"""

from typing import Dict
from datetime import datetime, timezone

_counters: Dict[str, Dict[str, int]] = {
    "quantum_circuits": {"attempts": 0, "successes": 0, "failures": 0},
    "algorithms": {"attempts": 0, "successes": 0, "failures": 0},
    "portfolio_optimization": {"attempts": 0, "successes": 0, "failures": 0},
}

_startup_time = datetime.now(timezone.utc).isoformat()


def record_attempt(module: str, success: bool) -> None:
    """Call this once per API request, from within each module's router,
    after the request either succeeded or failed."""
    if module not in _counters:
        _counters[module] = {"attempts": 0, "successes": 0, "failures": 0}
    _counters[module]["attempts"] += 1
    if success:
        _counters[module]["successes"] += 1
    else:
        _counters[module]["failures"] += 1


def get_module_stats(module: str) -> Dict:
    stats = _counters.get(module, {"attempts": 0, "successes": 0, "failures": 0})
    attempts = stats["attempts"]
    success_rate = round(stats["successes"] / attempts, 4) if attempts > 0 else None
    return {**stats, "success_rate": success_rate}


def get_all_stats() -> Dict:
    return {module: get_module_stats(module) for module in _counters}


def get_startup_time() -> str:
    return _startup_time
