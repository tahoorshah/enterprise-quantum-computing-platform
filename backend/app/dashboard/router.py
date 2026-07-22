"""
Module 4 - Executive Quantum Operations Dashboard: API endpoints.

This module does NOT run any new quantum computations. It aggregates and
summarizes data already produced by Modules 1 (Circuit Design), 2
(Portfolio Optimization), and 3 (Algorithm Demos) - reading from their
existing in-memory history stores and the shared metrics counters.

Endpoints:
    GET /api/dashboard/overview   - top-level KPIs across all modules
    GET /api/dashboard/kpis       - executive-focused KPI subset
    GET /api/dashboard/history    - merged, chronological history across all modules
    GET /api/dashboard/report     - full research progress report (all sections combined)
"""

from fastapi import APIRouter
from datetime import datetime, timezone

from app.dashboard import metrics
from app.quantum import history as quantum_history
from app.algorithms import history as algorithms_history
from app.optimization import history as optimization_history

router = APIRouter()


def _resource_utilization() -> dict:
    """
    'Quantum resource utilization' - approximated here as total qubits
    simulated across all executed circuits (Module 1) and algorithm runs
    (Module 3), since this is a simulator-based platform with no real
    quantum hardware queue/allocation to measure instead.
    """
    quantum_entries = quantum_history.list_history()
    total_qubits_module1 = sum(e.num_qubits for e in quantum_entries)

    # Module 3 doesn't store num_qubits in its lightweight history summary,
    # so we report execution counts by algorithm type instead - still a
    # genuine utilization signal, just at a different granularity.
    algo_entries = algorithms_history.list_history()
    algo_counts = {}
    for e in algo_entries:
        algo_counts[e["algorithm"]] = algo_counts.get(e["algorithm"], 0) + 1

    return {
        "module1_total_qubits_simulated": total_qubits_module1,
        "module1_total_circuits_executed": len(quantum_entries),
        "module3_executions_by_algorithm": algo_counts,
        "module3_total_algorithm_runs": len(algo_entries),
    }


@router.get("/overview")
def dashboard_overview():
    """Top-level snapshot: execution counts, success rates, resource use."""
    quantum_count = len(quantum_history.list_history())
    algo_count = len(algorithms_history.list_history())
    portfolio_count = len(optimization_history.list_history())

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "platform_uptime_since": metrics.get_startup_time(),
        "total_experiments_recorded": quantum_count + algo_count + portfolio_count,
        "experiments_by_module": {
            "module1_quantum_circuits": quantum_count,
            "module2_portfolio_optimization": portfolio_count,
            "module3_algorithm_demos": algo_count,
        },
        "success_rates_by_module": metrics.get_all_stats(),
        "resource_utilization": _resource_utilization(),
    }


@router.get("/kpis")
def executive_kpis():
    """A tighter, executive-facing subset of the overview - the numbers
    a non-technical exec would actually want on a summary screen."""
    stats = metrics.get_all_stats()
    total_attempts = sum(s["attempts"] for s in stats.values())
    total_successes = sum(s["successes"] for s in stats.values())
    overall_success_rate = round(total_successes / total_attempts, 4) if total_attempts > 0 else None

    portfolio_entries = optimization_history.list_history()
    portfolio_match_count = sum(1 for e in portfolio_entries if e.get("matched_classical_optimum"))

    return {
        "total_quantum_experiments_run": total_attempts,
        "overall_success_rate": overall_success_rate,
        "portfolio_optimizations_run": len(portfolio_entries),
        "portfolio_optimizations_matching_classical_optimum": portfolio_match_count,
        "portfolio_quantum_classical_agreement_rate": (
            round(portfolio_match_count / len(portfolio_entries), 4) if portfolio_entries else None
        ),
    }


@router.get("/history")
def merged_history():
    """
    Chronologically merged history across all three modules, most recent
    first - lets an executive see everything that's been run, in order,
    without needing to check three separate module dashboards.
    """
    entries = []

    for e in quantum_history.list_history():
        entries.append({
            "module": "quantum_circuits",
            "execution_id": e.execution_id,
            "timestamp": e.timestamp.isoformat() if hasattr(e.timestamp, "isoformat") else str(e.timestamp),
            "summary": f"{e.num_qubits}-qubit circuit, {e.num_gates} gates, {e.shots} shots",
        })

    for e in algorithms_history.list_history():
        entries.append({
            "module": "algorithm_demo",
            "execution_id": e["execution_id"],
            "timestamp": e["timestamp"],
            "summary": f"{e['algorithm']} algorithm demonstration",
        })

    for e in optimization_history.list_history():
        entries.append({
            "module": "portfolio_optimization",
            "execution_id": e["execution_id"],
            "timestamp": e["timestamp"],
            "summary": f"{e['num_assets']}-asset portfolio optimization",
        })

    entries.sort(key=lambda x: x["timestamp"], reverse=True)
    return entries


@router.get("/report")
def research_progress_report():
    """
    A full research progress report combining KPIs, resource utilization,
    and recent activity into one document-style response - intended as
    the data source for a generated PDF/executive report, per the
    capstone's 'Executive research dashboards' and 'Research progress
    reports' requirements (Section 4, Module 4).
    """
    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "overview": dashboard_overview(),
        "executive_kpis": executive_kpis(),
        "recent_activity": merged_history()[:10],
        "notes": (
            "Execution history is persisted through the platform's persistence "
            "layer: PostgreSQL when the database is reachable, with automatic "
            "in-memory fallback if it is not (graceful degradation). The active "
            "backend is reported by the /health endpoint's storage_backend field."
        ),
    }
