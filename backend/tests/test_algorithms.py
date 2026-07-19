"""
Tests for Module 3 - Quantum Algorithm Demonstration Platform.
Verifies the algorithms produce CORRECT results, not just that they run.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.algorithms.grover import run_grover_search
from app.algorithms.qft import demonstrate_qft
from app.algorithms.qaoa import run_qaoa_maxcut
from app.algorithms.vqe import run_vqe

client = TestClient(app)


# ---- Grover's ----

def test_grover_finds_marked_state():
    """Grover should return the marked state with high probability."""
    result = run_grover_search(num_qubits=3, marked_state="101", shots=1024)
    assert result["success_probability"] > 0.8
    # The marked state should be the most-measured outcome
    best = max(result["counts"], key=result["counts"].get)
    assert best == "101"


def test_grover_rejects_mismatched_marked_state_length():
    with pytest.raises(ValueError):
        run_grover_search(num_qubits=3, marked_state="10", shots=100)


# ---- QFT ----

def test_qft_roundtrip_recovers_input():
    """QFT followed by inverse-QFT must recover the original state ~100%."""
    result = demonstrate_qft(num_qubits=3, input_state="110", shots=1024)
    assert result["recovered_correctly_probability"] > 0.95


# ---- QAOA ----

def test_qaoa_finds_optimal_maxcut_on_triangle():
    """Triangle graph max-cut is 2; QAOA should reach it."""
    edges = [(0, 1), (1, 2), (0, 2)]
    result = run_qaoa_maxcut(edges, num_nodes=3, p=1, shots=256, max_iterations=20)
    assert result["best_cut_value"] == 2
    assert result["max_possible_cut_value"] == 3
    # Convergence history should be real (non-empty, measured)
    assert len(result["convergence_history"]) > 0


# ---- VQE ----

def test_vqe_converges_near_theoretical_minimum():
    """VQE on the Z-sum Hamiltonian should converge close to -num_qubits."""
    result = run_vqe(num_qubits=3, max_iterations=50)
    assert result["theoretical_minimum_energy"] == -3.0
    # Should get within a small tolerance
    assert result["converged_within"] < 0.1


# ---- API endpoints ----

def test_grover_endpoint():
    response = client.post("/api/algorithms/grover", json={
        "num_qubits": 2, "marked_state": "10", "shots": 256,
    })
    assert response.status_code == 200
    assert response.json()["algorithm"] == "grover"


def test_qft_endpoint():
    response = client.post("/api/algorithms/qft", json={
        "num_qubits": 2, "input_state": "10", "shots": 256,
    })
    assert response.status_code == 200
    assert response.json()["algorithm"] == "qft"


def test_vqe_endpoint():
    response = client.post("/api/algorithms/vqe", json={
        "num_qubits": 2, "max_iterations": 20,
    })
    assert response.status_code == 200
    assert response.json()["algorithm"] == "vqe"
