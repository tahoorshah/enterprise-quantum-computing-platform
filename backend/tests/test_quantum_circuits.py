"""
Tests for Module 1 - Quantum Circuit Design Platform.

Covers both the core circuit-building logic and the API endpoints.
Run with: pytest tests/test_quantum_circuits.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.quantum.circuit_builder import (
    execute_circuit_request, validate_request, InvalidCircuitError
)
from app.quantum.schemas import CircuitRequest, GateInstruction

client = TestClient(app)


# ---- Core logic tests ----

def test_bell_state_gives_correlated_outcomes():
    """A Bell state (H + CX) should only ever produce '00' or '11', never '01'/'10'."""
    req = CircuitRequest(
        num_qubits=2,
        gates=[
            GateInstruction(gate="h", qubits=[0]),
            GateInstruction(gate="cx", qubits=[0, 1]),
        ],
        shots=1024,
    )
    result = execute_circuit_request(req)
    # Only entangled outcomes should appear
    for outcome in result.counts:
        assert outcome in ("00", "11"), f"Unexpected outcome {outcome} in Bell state"
    # Both outcomes should occur (probabilistic, but with 1024 shots effectively certain)
    assert len(result.counts) == 2


def test_probabilities_sum_to_one():
    req = CircuitRequest(
        num_qubits=1,
        gates=[GateInstruction(gate="h", qubits=[0])],
        shots=2048,
    )
    result = execute_circuit_request(req)
    total = sum(result.probabilities.values())
    assert abs(total - 1.0) < 0.01


def test_invalid_gate_name_rejected():
    req = CircuitRequest(
        num_qubits=1,
        gates=[GateInstruction(gate="notagate", qubits=[0])],
        shots=100,
    )
    with pytest.raises(InvalidCircuitError):
        validate_request(req)


def test_qubit_index_out_of_range_rejected():
    req = CircuitRequest(
        num_qubits=2,
        gates=[GateInstruction(gate="h", qubits=[5])],
        shots=100,
    )
    with pytest.raises(InvalidCircuitError):
        validate_request(req)


def test_wrong_qubit_count_for_gate_rejected():
    # CX needs 2 qubits; giving 1 should fail
    req = CircuitRequest(
        num_qubits=2,
        gates=[GateInstruction(gate="cx", qubits=[0])],
        shots=100,
    )
    with pytest.raises(InvalidCircuitError):
        validate_request(req)


def test_rotation_gate_requires_parameter():
    # rx needs 1 param; giving none should fail
    req = CircuitRequest(
        num_qubits=1,
        gates=[GateInstruction(gate="rx", qubits=[0])],
        shots=100,
    )
    with pytest.raises(InvalidCircuitError):
        validate_request(req)


# ---- API endpoint tests ----

def test_execute_endpoint_success():
    response = client.post("/api/quantum/execute", json={
        "num_qubits": 2,
        "gates": [
            {"gate": "h", "qubits": [0]},
            {"gate": "cx", "qubits": [0, 1]},
        ],
        "shots": 512,
    })
    assert response.status_code == 200
    data = response.json()
    assert "counts" in data
    assert "circuit_diagram_text" in data
    assert data["num_qubits"] == 2


def test_execute_endpoint_invalid_gate_returns_422():
    response = client.post("/api/quantum/execute", json={
        "num_qubits": 1,
        "gates": [{"gate": "banana", "qubits": [0]}],
        "shots": 100,
    })
    assert response.status_code == 422


def test_gates_endpoint_lists_supported_gates():
    response = client.get("/api/quantum/gates")
    assert response.status_code == 200
    gates = response.json()
    # Spot-check a few expected gates
    for expected in ("h", "cx", "rx", "ccx"):
        assert expected in gates
