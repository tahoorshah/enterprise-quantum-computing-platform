"""
Module 1 - Quantum Circuit Design Platform: core logic.

This is deliberately kept separate from the FastAPI router (router.py) so
the quantum logic can be tested/reused independently of the web layer —
a pattern worth being able to explain in the viva (separation of concerns).
"""

import time
import uuid
from datetime import datetime, timezone

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from app.quantum.schemas import CircuitRequest, CircuitResult, SUPPORTED_GATES


class InvalidCircuitError(Exception):
    """Raised when the requested circuit is invalid (bad gate, bad qubit index, etc.)."""
    pass


def validate_request(request: CircuitRequest) -> None:
    """
    Check the request makes sense BEFORE handing it to Qiskit.
    This gives clear, specific error messages instead of a raw Qiskit traceback.
    """
    for instruction in request.gates:
        gate_name = instruction.gate.lower()

        if gate_name not in SUPPORTED_GATES:
            raise InvalidCircuitError(
                f"Unknown gate '{instruction.gate}'. Supported gates: {list(SUPPORTED_GATES.keys())}"
            )

        spec = SUPPORTED_GATES[gate_name]

        if len(instruction.qubits) != spec["qubits"]:
            raise InvalidCircuitError(
                f"Gate '{gate_name}' requires exactly {spec['qubits']} qubit(s), "
                f"got {len(instruction.qubits)}: {instruction.qubits}"
            )

        for q in instruction.qubits:
            if q < 0 or q >= request.num_qubits:
                raise InvalidCircuitError(
                    f"Qubit index {q} is out of range for a {request.num_qubits}-qubit circuit "
                    f"(valid range: 0 to {request.num_qubits - 1})"
                )

        needed_params = spec["params"]
        given_params = len(instruction.params) if instruction.params else 0
        if given_params != needed_params:
            raise InvalidCircuitError(
                f"Gate '{gate_name}' requires {needed_params} parameter(s) (e.g. an angle in radians), "
                f"got {given_params}"
            )


def build_circuit(request: CircuitRequest) -> QuantumCircuit:
    """Translate a validated CircuitRequest into an actual Qiskit QuantumCircuit."""
    qc = QuantumCircuit(request.num_qubits, request.num_qubits)

    for instruction in request.gates:
        gate_name = instruction.gate.lower()
        qubits = instruction.qubits
        params = instruction.params or []

        # getattr() dynamically fetches the right method on the circuit object,
        # e.g. gate_name="h" -> qc.h, gate_name="cx" -> qc.cx
        gate_method = getattr(qc, gate_name)
        gate_method(*params, *qubits)

    if request.measure_all:
        qc.measure(range(request.num_qubits), range(request.num_qubits))

    return qc


def run_circuit(qc: QuantumCircuit, shots: int) -> dict:
    """Run the circuit on AerSimulator and return raw measurement counts."""
    simulator = AerSimulator()
    job = simulator.run(qc, shots=shots)
    result = job.result()
    return result.get_counts()


def counts_to_probabilities(counts: dict, shots: int) -> dict:
    """Convert raw shot counts into probabilities (0.0 to 1.0) for each outcome."""
    return {outcome: round(count / shots, 4) for outcome, count in counts.items()}


def execute_circuit_request(request: CircuitRequest) -> CircuitResult:
    """
    Full pipeline: validate -> build -> run -> package results.
    This is the single function the API router calls.
    """
    validate_request(request)

    start = time.perf_counter()
    qc = build_circuit(request)
    counts = run_circuit(qc, request.shots)
    elapsed_ms = (time.perf_counter() - start) * 1000

    return CircuitResult(
        execution_id=str(uuid.uuid4()),
        timestamp=datetime.now(timezone.utc),
        num_qubits=request.num_qubits,
        gates_applied=request.gates,
        shots=request.shots,
        circuit_diagram_text=str(qc.draw(output="text")),
        counts=counts,
        probabilities=counts_to_probabilities(counts, request.shots),
        execution_time_ms=round(elapsed_ms, 2),
    )
