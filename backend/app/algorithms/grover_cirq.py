"""
Grover's Search Algorithm - native Cirq implementation.

This is a second, independent implementation of the same algorithm as
app/algorithms/grover.py, built directly on Cirq's Circuit/Simulator API
rather than Qiskit. It uses the identical oracle + diffuser construction
(built gate-by-gate, not a library primitive) and the identical optimal-
iteration-count formula, so the two implementations are directly
comparable: same problem, different quantum-computing framework. This
closes the gap where the capstone's "multi-framework" claim (Module 6)
previously only demonstrated Bell states in Cirq, never a real algorithm
end-to-end.

Business relevance (for the viva): see app/algorithms/grover.py. Same
quadratic query-complexity advantage, same claim-scoping caveat: this
compares NUMBER OF ORACLE QUERIES, not measured wall-clock speed.

BIT ORDER: unlike the Qiskit implementation, where the bitstring's
RIGHTMOST character is qubit 0, this Cirq implementation follows Cirq's
natural measurement order - the LEFTMOST character of a returned
bitstring corresponds to the FIRST qubit in cirq.LineQubit.range(n), i.e.
qubit 0. `marked_state` is read in that same left-to-right order, so the
implementation is internally consistent even though its convention
differs from the Qiskit version.
"""

import math
from typing import Dict, List
import cirq


def build_oracle(qubits: List[cirq.Qid], marked_state: str) -> List[cirq.Operation]:
    """
    Operations for an oracle that flips the phase of exactly one marked
    basis state.

    marked_state: a bitstring like "101", read left-to-right as
    qubits[0], qubits[1], ... (Cirq's natural order - see module docstring).
    """
    ops: List[cirq.Operation] = []

    for qubit, bit in zip(qubits, marked_state):
        if bit == "0":
            ops.append(cirq.X(qubit))

    if len(qubits) == 1:
        ops.append(cirq.Z(qubits[0]))
    else:
        ops.append(cirq.Z(qubits[-1]).controlled_by(*qubits[:-1]))

    for qubit, bit in zip(qubits, marked_state):
        if bit == "0":
            ops.append(cirq.X(qubit))

    return ops


def build_diffuser(qubits: List[cirq.Qid]) -> List[cirq.Operation]:
    """
    The 'diffuser' (inversion about the mean) - amplifies the marked
    state's probability after the oracle flips its phase.
    """
    ops: List[cirq.Operation] = []

    ops.extend(cirq.H(q) for q in qubits)
    ops.extend(cirq.X(q) for q in qubits)

    if len(qubits) == 1:
        ops.append(cirq.Z(qubits[0]))
    else:
        ops.append(cirq.Z(qubits[-1]).controlled_by(*qubits[:-1]))

    ops.extend(cirq.X(q) for q in qubits)
    ops.extend(cirq.H(q) for q in qubits)

    return ops


def optimal_iterations(num_qubits: int) -> int:
    """
    Same formula as the Qiskit version: the number of Grover iterations
    that maximizes success probability is approximately (pi/4) * sqrt(N),
    where N = 2^num_qubits.
    """
    n = 2 ** num_qubits
    return max(1, round((math.pi / 4) * math.sqrt(n)))


def run_grover_search_cirq(num_qubits: int, marked_state: str, shots: int = 1024) -> dict:
    """
    Full Grover's algorithm on Cirq: build circuit, run it, return results
    in the same shape as the Qiskit version (plus a framework tag and the
    bit-order note above).
    """
    if len(marked_state) != num_qubits:
        raise ValueError(f"marked_state must be {num_qubits} bits long, got '{marked_state}'")
    if not all(b in "01" for b in marked_state):
        raise ValueError(f"marked_state must contain only 0s and 1s, got '{marked_state}'")

    qubits = cirq.LineQubit.range(num_qubits)
    iterations = optimal_iterations(num_qubits)

    circuit = cirq.Circuit()
    circuit.append(cirq.H(q) for q in qubits)  # uniform superposition over all possible states

    oracle_ops = build_oracle(qubits, marked_state)
    diffuser_ops = build_diffuser(qubits)

    for _ in range(iterations):
        circuit.append(oracle_ops)
        circuit.append(diffuser_ops)

    circuit.append(cirq.measure(*qubits, key="result"))

    simulator = cirq.Simulator()
    result = simulator.run(circuit, repetitions=shots)
    measurements = result.measurements["result"]

    counts: Dict[str, int] = {}
    for row in measurements:
        bitstring = "".join(str(int(b)) for b in row)
        counts[bitstring] = counts.get(bitstring, 0) + 1

    total_states = 2 ** num_qubits
    classical_avg_lookups = total_states / 2  # average case, linear search
    quantum_oracle_calls = iterations

    return {
        "framework": "Cirq",
        "marked_state": marked_state,
        "num_qubits": num_qubits,
        "iterations_used": iterations,
        "circuit_diagram_text": str(circuit),
        "counts": counts,
        "probabilities": {k: round(v / shots, 4) for k, v in counts.items()},
        "success_probability": round(counts.get(marked_state, 0) / shots, 4),
        "bit_order_note": (
            "Bitstrings follow Cirq's natural measurement order: the leftmost "
            "character corresponds to qubit 0 (cirq.LineQubit(0)), unlike the "
            "Qiskit implementation of this algorithm, where the rightmost "
            "character is qubit 0."
        ),
        "query_complexity_comparison": {
            "search_space_size": total_states,
            "classical_avg_lookups_needed": classical_avg_lookups,
            "quantum_oracle_calls_needed": quantum_oracle_calls,
            "theoretical_query_reduction_factor": round(classical_avg_lookups / quantum_oracle_calls, 2) if quantum_oracle_calls > 0 else None,
            "claim_scope": (
                "This compares NUMBER OF ORACLE QUERIES, not measured execution "
                "time. Grover's algorithm's quadratic advantage (O(sqrt(N)) vs "
                "O(N) queries) is a query-complexity result, and it is what is "
                "shown here. It is NOT a claim that this run executed faster: on "
                "a classical simulator, simulating each quantum oracle call costs "
                "far more compute than one classical lookup would, so no wall-clock "
                "speed advantage exists or is measured on this hardware. Any real "
                "speed advantage would require physical quantum hardware at a "
                "scale where circuit simulation cost is no longer the bottleneck."
            ),
        },
    }
