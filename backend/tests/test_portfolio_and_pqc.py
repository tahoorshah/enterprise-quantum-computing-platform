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
