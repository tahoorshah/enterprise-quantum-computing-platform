"""
Cross-framework validation tests (Module 6).

Tests use a fixed seed so results are exactly reproducible - a suite that
occasionally fails on unlucky sampling is weak evidence for the rejection
letter's "testing coverage" concern; a deterministic one is strong evidence.
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.frameworks.multi_framework import (
    counts_to_probabilities,
    total_variation_distance,
    sampling_tolerance,
    run_bell_comparison,
    run_superposition_comparison,
    run_all_frameworks,
)

client = TestClient(app)

SHOTS = 1024
SEED = 12345


def test_counts_to_probabilities_covers_full_outcome_space():
    probs = counts_to_probabilities({"00": 50, "11": 50}, num_qubits=2)

    assert set(probs) == {"00", "01", "10", "11"}
    assert probs["01"] == 0.0
    assert probs["10"] == 0.0
    assert probs["00"] == pytest.approx(0.5)
    assert sum(probs.values()) == pytest.approx(1.0)


def test_total_variation_distance_is_zero_for_identical_distributions():
    p = {"0": 0.5, "1": 0.5}
    assert total_variation_distance(p, dict(p)) == pytest.approx(0.0)


def test_total_variation_distance_is_one_for_disjoint_distributions():
    p = {"0": 1.0, "1": 0.0}
    q = {"0": 0.0, "1": 1.0}
    assert total_variation_distance(p, q) == pytest.approx(1.0)


def test_validation_would_reject_a_disagreeing_framework():
    """A skewed 99/1 split is still 'only correlated outcomes' but must fail agreement."""
    skewed = counts_to_probabilities({"00": 99, "11": 1}, num_qubits=2)
    theoretical = {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.5}

    distance = total_variation_distance(skewed, theoretical)
    assert distance > sampling_tolerance(shots=1024, num_outcomes=4)


def test_sampling_tolerance_tightens_as_shots_increase():
    assert sampling_tolerance(4096, 4) < sampling_tolerance(256, 4)


def test_bell_state_agrees_across_all_three_frameworks():
    result = run_bell_comparison(shots=SHOTS, seed=SEED)
    validation = result["validation"]

    assert set(result["results"]) == {"qiskit", "pennylane", "cirq"}
    assert validation["all_agree_with_theory"], validation["distance_from_theory"]
    assert validation["all_agree_with_each_other"], validation["pairwise_distance_between_frameworks"]


def test_bell_state_never_produces_forbidden_outcomes():
    result = run_bell_comparison(shots=SHOTS, seed=SEED)

    assert result["no_forbidden_outcomes"]
    for framework, observed in result["forbidden_outcomes_observed"].items():
        assert observed == {}, f"{framework} produced a forbidden outcome"


def test_superposition_agrees_across_all_three_frameworks():
    result = run_superposition_comparison(shots=SHOTS, seed=SEED)
    validation = result["validation"]

    assert set(result["results"]) == {"qiskit", "pennylane", "cirq"}
    assert validation["all_agree_with_theory"], validation["distance_from_theory"]
    assert validation["all_agree_with_each_other"], validation["pairwise_distance_between_frameworks"]


def test_pairwise_comparison_covers_every_framework_pair():
    result = run_bell_comparison(shots=SHOTS, seed=SEED)
    pairs = result["validation"]["pairwise_distance_between_frameworks"]

    assert len(pairs) == 3
    assert set(pairs) == {"cirq_vs_pennylane", "cirq_vs_qiskit", "pennylane_vs_qiskit"}


def test_run_all_frameworks_reports_both_demonstrations():
    result = run_all_frameworks(shots=SHOTS, seed=SEED)

    assert set(result["demonstrations"]) == {"bell_state", "superposition"}
    assert result["frameworks_compared"] == ["Qiskit", "PennyLane", "Cirq"]
    assert result["cross_framework_validation_passed"]


def test_compare_endpoint_returns_validation():
    response = client.get(f"/api/frameworks/compare?shots={SHOTS}&seed={SEED}")

    assert response.status_code == 200
    body = response.json()
    assert body["cross_framework_validation_passed"] is True
    assert "validation" in body["demonstrations"]["bell_state"]


def test_bell_and_superposition_endpoints_work_independently():
    bell = client.get(f"/api/frameworks/bell?shots={SHOTS}&seed={SEED}")
    sup = client.get(f"/api/frameworks/superposition?shots={SHOTS}&seed={SEED}")

    assert bell.status_code == 200
    assert sup.status_code == 200
    assert bell.json()["demonstration"] == "Bell state (entanglement)"
    assert sup.json()["demonstration"] == "Single-qubit superposition"


def test_seeded_run_is_exactly_reproducible():
    """Same seed, same inputs -> identical counts. Proves determinism, not just agreement."""
    first = run_bell_comparison(shots=SHOTS, seed=SEED)
    second = run_bell_comparison(shots=SHOTS, seed=SEED)

    assert first["results"]["qiskit"]["counts"] == second["results"]["qiskit"]["counts"]
    assert first["results"]["cirq"]["counts"] == second["results"]["cirq"]["counts"]
