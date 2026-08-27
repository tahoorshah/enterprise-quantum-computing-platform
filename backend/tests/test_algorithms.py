"""
Tests for Module 3 - Quantum Algorithm Demonstration Platform.
Verifies the algorithms produce CORRECT results, not just that they run.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.algorithms.grover import run_grover_search
from app.algorithms.grover_cirq import run_grover_search_cirq
from app.algorithms.qft import demonstrate_qft
from app.algorithms.qaoa import run_qaoa_maxcut
from app.algorithms.vqe import run_vqe
from app.algorithms.vqe_pennylane import run_vqe_pennylane

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


# ---- Grover's (native Cirq) ----

def test_grover_cirq_finds_marked_state():
    """Native Cirq Grover should return the marked state with high probability."""
    result = run_grover_search_cirq(num_qubits=3, marked_state="101", shots=1024)
    assert result["framework"] == "Cirq"
    assert result["success_probability"] > 0.8
    best = max(result["counts"], key=result["counts"].get)
    assert best == "101"


def test_grover_cirq_rejects_mismatched_marked_state_length():
    with pytest.raises(ValueError):
        run_grover_search_cirq(num_qubits=3, marked_state="10", shots=100)


def test_grover_cirq_matches_qiskit_success_rate():
    """Both frameworks implement the same algorithm on the same problem,
    so their success probabilities should be close (not necessarily
    identical, since sampling noise differs)."""
    qiskit_result = run_grover_search(num_qubits=3, marked_state="110", shots=2048)
    cirq_result = run_grover_search_cirq(num_qubits=3, marked_state="110", shots=2048)
    assert abs(qiskit_result["success_probability"] - cirq_result["success_probability"]) < 0.15
    assert qiskit_result["iterations_used"] == cirq_result["iterations_used"]


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


# ---- VQE (native PennyLane) ----

def test_vqe_pennylane_converges_near_theoretical_minimum():
    """Native PennyLane VQE on the same Z-sum Hamiltonian should also
    converge close to -num_qubits."""
    result = run_vqe_pennylane(num_qubits=3, max_iterations=50)
    assert result["framework"] == "PennyLane"
    assert result["theoretical_minimum_energy"] == -3.0
    assert result["converged_within"] < 0.1


def test_vqe_pennylane_matches_qiskit_final_energy():
    """Both frameworks optimize the same ansatz against the same
    Hamiltonian with the same optimizer, so final energies should agree
    closely."""
    qiskit_result = run_vqe(num_qubits=2, max_iterations=50)
    pennylane_result = run_vqe_pennylane(num_qubits=2, max_iterations=50)
    assert abs(qiskit_result["final_energy"] - pennylane_result["final_energy"]) < 0.05


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


def test_grover_cirq_endpoint():
    response = client.post("/api/algorithms/grover-cirq", json={
        "num_qubits": 2, "marked_state": "10", "shots": 256,
    })
    assert response.status_code == 200
    assert response.json()["algorithm"] == "grover_cirq"


def test_vqe_pennylane_endpoint():
    response = client.post("/api/algorithms/vqe-pennylane", json={
        "num_qubits": 2, "max_iterations": 20,
    })
    assert response.status_code == 200
    assert response.json()["algorithm"] == "vqe_pennylane"


def test_grover_claim_is_scoped_to_query_complexity_not_wall_clock():
    """
    The rejection letter warned against overstating quantum-vs-classical
    performance. This checks the speedup claim is explicitly scoped to
    query count, not presented as measured execution speed.
    """
    from app.algorithms.grover import run_grover_search

    result = run_grover_search(num_qubits=3, marked_state="101", shots=256)
    comparison = result["query_complexity_comparison"]

    assert "theoretical_query_reduction_factor" in comparison
    assert "claim_scope" in comparison
    scope_text = comparison["claim_scope"].lower()
    assert "not" in scope_text and "wall-clock" in scope_text
    assert "oracle quer" in scope_text or "query" in scope_text


def test_grover_query_reduction_factor_matches_iteration_count():
    """The reduction factor must be derivable from the actual iteration count used, not asserted separately."""
    from app.algorithms.grover import run_grover_search

    result = run_grover_search(num_qubits=3, marked_state="011", shots=256)
    comparison = result["query_complexity_comparison"]

    expected = round(comparison["classical_avg_lookups_needed"] / comparison["quantum_oracle_calls_needed"], 2)
    assert comparison["theoretical_query_reduction_factor"] == expected
    assert comparison["quantum_oracle_calls_needed"] == result["iterations_used"]
