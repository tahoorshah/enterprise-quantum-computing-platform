"""
Tests for Module 2 (Portfolio Optimization) and Module 5 (PQC Readiness).
"""

import pytest
import numpy as np
from fastapi.testclient import TestClient
from app.main import app
from app.optimization.portfolio import (
    generate_simulated_market_data, build_qubo, qubo_to_ising,
    qubo_cost, brute_force_optimum
)
from app.optimization.qaoa_portfolio import run_portfolio_optimization
from app.pqc.quantum_threat_demo import run_qpe_demo
from app.pqc.inventory import generate_inventory

client = TestClient(app)


# ---- Module 2: Portfolio ----

def test_qubo_to_ising_conversion_is_consistent():
    """
    The QUBO and its Ising form must give the SAME cost for every bitstring.
    This is the exact bug that was caught during development - lock it down.
    """
    names, returns, cov = generate_simulated_market_data(num_assets=4, seed=42)
    Q = build_qubo(returns, cov, budget=2, risk_aversion=0.5, penalty_weight=2.0)
    h, J, offset = qubo_to_ising(Q)

    def ising_cost(bitstring):
        z = np.array([1 - 2 * int(b) for b in reversed(bitstring)])
        c = offset
        for i in range(len(z)):
            c += h[i] * z[i]
            for j in range(i + 1, len(z)):
                c += J[i, j] * z[i] * z[j]
        return c

    # Check ALL 16 bitstrings
    for combo in range(16):
        bitstring = format(combo, "04b")
        assert abs(qubo_cost(bitstring, Q) - ising_cost(bitstring)) < 1e-9


def test_brute_force_respects_cardinality_constraint():
    """With a penalty, the optimum should select exactly `budget` assets."""
    names, returns, cov = generate_simulated_market_data(num_assets=4, seed=42)
    Q = build_qubo(returns, cov, budget=2, risk_aversion=0.5, penalty_weight=2.0)
    best_bitstring, _ = brute_force_optimum(Q)
    assert best_bitstring.count("1") == 2


def test_qaoa_matches_classical_optimum():
    """On a small problem, QAOA should find the same optimum as brute force."""
    result = run_portfolio_optimization(
        num_assets=4, budget=2, shots=512, max_iterations=25, seed=42
    )
    assert result["comparison"]["quantum_matched_classical_optimum"] is True


def test_portfolio_market_data_reproducible():
    """Same seed must give identical market data."""
    n1, r1, c1 = generate_simulated_market_data(4, seed=42)
    n2, r2, c2 = generate_simulated_market_data(4, seed=42)
    assert n1 == n2
    assert np.allclose(r1, r2)
    assert np.allclose(c1, c2)


def test_portfolio_endpoint():
    response = client.post("/api/optimization/portfolio", json={
        "num_assets": 4, "budget": 2, "shots": 256, "max_iterations": 15,
    })
    assert response.status_code == 200


def test_portfolio_budget_exceeds_assets_rejected():
    response = client.post("/api/optimization/portfolio", json={
        "num_assets": 4, "budget": 4, "shots": 256, "max_iterations": 15,
    })
    assert response.status_code == 422


# ---- Module 5: PQC ----

def test_qpe_recovers_exact_phase():
    """QPE on an exactly-representable phase should recover it with zero error."""
    result = run_qpe_demo(theta=0.375, num_counting_qubits=3, shots=1024)
    assert result["estimation_error"] == 0.0
    assert result["most_likely_estimate"] == 0.375


def test_qpe_rejects_out_of_range_theta():
    with pytest.raises(ValueError):
        run_qpe_demo(theta=1.5, num_counting_qubits=3, shots=100)


def test_inventory_reproducible_per_seed():
    """Same seed must give identical inventory."""
    inv1 = generate_inventory(seed=42)
    inv2 = generate_inventory(seed=42)
    assert inv1 == inv2


def test_inventory_has_expected_fields():
    inv = generate_inventory(seed=42)
    assert len(inv) > 0
    required = {"system_id", "system_name", "current_algorithm",
                "quantum_risk_score", "migration_urgency"}
    assert required.issubset(inv[0].keys())


def test_pqc_classical_endpoint():
    response = client.get("/api/pqc/algorithms/classical")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_pqc_threat_demo_endpoint():
    response = client.post("/api/pqc/threat-demo", json={
        "theta": 0.25, "num_counting_qubits": 3, "shots": 512,
    })
    assert response.status_code == 200

def test_repeated_evaluation_runs_requested_number_of_trials():
    """QAOA is stochastic; the pipeline must report every trial, not just one."""
    from app.optimization.qaoa_portfolio import run_portfolio_optimization

    result = run_portfolio_optimization(num_assets=4, budget=2, shots=128, max_iterations=8, trials=3)
    repeated = result["repeated_evaluation"]

    assert repeated["trials_run"] == 3
    assert len(repeated["per_trial"]) == 3
    assert [r["trial"] for r in repeated["per_trial"]] == [1, 2, 3]


def test_repeated_evaluation_rates_are_consistent_with_trial_records():
    """Reported success rates must be derivable from the per-trial data, not asserted."""
    from app.optimization.qaoa_portfolio import run_portfolio_optimization

    result = run_portfolio_optimization(num_assets=4, budget=2, shots=128, max_iterations=8, trials=4)
    repeated = result["repeated_evaluation"]
    trials = repeated["per_trial"]

    expected_matches = sum(1 for t in trials if t["matched_classical_optimum"])
    expected_constraint = sum(1 for t in trials if t["cardinality_constraint_satisfied"])

    assert repeated["times_matched_classical_optimum"] == expected_matches
    assert repeated["optimum_recovery_rate"] == round(expected_matches / 4, 4)
    assert repeated["times_cardinality_constraint_satisfied"] == expected_constraint
    assert repeated["cardinality_satisfaction_rate"] == round(expected_constraint / 4, 4)

    costs = [t["qubo_cost"] for t in trials]
    assert repeated["qubo_cost_best"] == round(min(costs), 4)
    assert repeated["qubo_cost_worst"] == round(max(costs), 4)


def test_cardinality_constraint_is_reported_for_both_solutions():
    """Selection count must be explicit in the output, not left for the reader to count."""
    from app.optimization.qaoa_portfolio import run_portfolio_optimization

    result = run_portfolio_optimization(num_assets=4, budget=2, shots=128, max_iterations=8, trials=2)

    classical = result["classical_solution"]
    quantum = result["quantum_solution"]

    assert classical["assets_selected"] == 2
    assert classical["cardinality_constraint_satisfied"] is True
    assert "assets_selected" in quantum
    assert "cardinality_constraint_satisfied" in quantum


def test_classical_brute_force_is_exact_optimum_over_all_trials():
    """No QAOA trial may beat brute force — it enumerates every combination."""
    from app.optimization.qaoa_portfolio import run_portfolio_optimization

    result = run_portfolio_optimization(num_assets=4, budget=2, shots=128, max_iterations=8, trials=3)
    classical_cost = result["classical_solution"]["qubo_cost"]

    for trial in result["repeated_evaluation"]["per_trial"]:
        assert trial["qubo_cost"] >= classical_cost - 1e-6


def test_inventory_systems_have_accountable_owner():
    from app.pqc.inventory import generate_inventory

    inventory = generate_inventory(seed=42)
    for system in inventory:
        assert system["accountable_owner"], f"{system['system_id']} has no owner"
        assert "escalation" in system
        assert "review_frequency" in system["escalation"]


def test_immediate_systems_escalate_faster_than_low_urgency():
    from app.governance.roles import escalation_path

    immediate = escalation_path("IMMEDIATE")
    low = escalation_path("LOW")

    assert immediate["overdue_threshold_days"] < low["overdue_threshold_days"]


def test_migration_plan_phases_carry_governance():
    from app.pqc.inventory import generate_inventory
    from app.pqc.migration_plan import generate_migration_plan

    inventory = generate_inventory(seed=42)
    plan = generate_migration_plan(inventory)

    assert len(plan["phases"]) == 5
    for phase in plan["phases"]:
        assert phase["governance"]["required_approvals"], f"Phase {phase['phase']} has no approvers"
        assert phase["governance"]["exit_criteria"], f"Phase {phase['phase']} has no exit criteria"


def test_every_phase_requires_ciso_signoff():
    """CISO is accountable for the overall migration outcome - must appear in every phase."""
    from app.governance.roles import PHASE_APPROVAL_REQUIREMENTS

    for phase, roles in PHASE_APPROVAL_REQUIREMENTS.items():
        assert "CISO" in roles, f"Phase {phase} has no CISO sign-off"


def test_governance_model_discloses_single_operator_scope():
    """The proof-of-concept limitation must be stated, not implied."""
    from app.governance.roles import governance_model

    model = governance_model()
    assert "one" in model["scope_limitation"].lower() or "single" in model["scope_limitation"].lower()


def test_governance_endpoints_respond():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth.security import get_current_user

    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: {"username": "analyst", "role": "financial_analyst"}
    try:
        assert client.get("/api/governance/model").status_code == 200
        assert client.get("/api/governance/roles").status_code == 200
        assert client.get("/api/governance/phase/1").status_code == 200
        assert client.get("/api/governance/phase/99").status_code == 404
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_risk_register_entries_have_owner_and_mitigation():
    from app.governance.risk_register import get_risk_register

    risks = get_risk_register()
    assert len(risks) >= 15
    for r in risks:
        assert r["owner_role"], f"{r['id']} has no owner"
        assert r["mitigation"], f"{r['id']} has no mitigation statement"
        assert r["risk_score"] == r["likelihood"] * r["impact"]


def test_risk_register_covers_all_nine_mandatory_categories():
    """The rejection letter names these categories explicitly - all must be represented."""
    from app.governance.risk_register import get_risk_register

    required = {
        "Technical", "Financial", "Security", "Operational", "Data",
        "Quantum Computing", "Migration", "Availability", "Implementation",
    }
    risks = get_risk_register()
    present = {r["category"] for r in risks}
    missing = required - present
    assert not missing, f"Missing risk categories: {missing}"


def test_risk_register_summary_is_consistent_with_full_register():
    from app.governance.risk_register import get_risk_register, risk_register_summary

    risks = get_risk_register()
    summary = risk_register_summary()

    assert summary["total_risks"] == len(risks)
    assert sum(summary["by_rating"].values()) == len(risks)
    assert sum(summary["by_category"].values()) == len(risks)


def test_risk_register_endpoints_respond():
    from fastapi.testclient import TestClient
    from app.main import app
    from app.auth.security import get_current_user

    client = TestClient(app)
    app.dependency_overrides[get_current_user] = lambda: {"username": "analyst", "role": "financial_analyst"}
    try:
        full = client.get("/api/governance/risk-register")
        summary = client.get("/api/governance/risk-register/summary")
        assert full.status_code == 200
        assert summary.status_code == 200
        assert len(full.json()) == summary.json()["total_risks"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)
