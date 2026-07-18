"""
Grover's Search Algorithm.

Built from textbook gate-level construction (oracle + diffuser), not a
high-level library call — this is deliberate so every gate can be
explained in the viva, and so we don't depend on library APIs that
shift between Qiskit versions.

Business relevance (for the viva): Grover's gives a quadratic speedup for
unstructured search — O(sqrt(N)) instead of O(N). In finance this maps to
searching unsorted transaction/fraud databases, or searching a solution
space in optimization problems faster than classical brute force.
"""

import math
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def build_oracle(num_qubits: int, marked_state: str) -> QuantumCircuit:
    """
    Build an oracle that flips the phase of exactly one marked basis state.

    marked_state: a bitstring like "101" (qiskit bit order: rightmost = qubit 0)
    """
    oracle = QuantumCircuit(num_qubits)

    # Flip qubits that should be 0 in the marked state, so the marked
    # state temporarily looks like all-1s (which is what our multi-controlled-Z
    # below targets).
    for i, bit in enumerate(reversed(marked_state)):
        if bit == "0":
            oracle.x(i)

    # Multi-controlled Z: flip the phase only when all qubits are |1>
    if num_qubits == 1:
        oracle.z(0)
    else:
        oracle.h(num_qubits - 1)
        oracle.mcx(list(range(num_qubits - 1)), num_qubits - 1)
        oracle.h(num_qubits - 1)

    # Undo the X flips
    for i, bit in enumerate(reversed(marked_state)):
        if bit == "0":
            oracle.x(i)

    return oracle


def build_diffuser(num_qubits: int) -> QuantumCircuit:
    """
    The 'diffuser' (inversion about the mean) - amplifies the marked
    state's probability after the oracle flips its phase.
    """
    diffuser = QuantumCircuit(num_qubits)

    diffuser.h(range(num_qubits))
    diffuser.x(range(num_qubits))

    if num_qubits == 1:
        diffuser.z(0)
    else:
        diffuser.h(num_qubits - 1)
        diffuser.mcx(list(range(num_qubits - 1)), num_qubits - 1)
        diffuser.h(num_qubits - 1)

    diffuser.x(range(num_qubits))
    diffuser.h(range(num_qubits))

    return diffuser


def optimal_iterations(num_qubits: int) -> int:
    """
    The number of Grover iterations that maximizes success probability
    is approximately (pi/4) * sqrt(N), where N = 2^num_qubits.
    """
    n = 2 ** num_qubits
    return max(1, round((math.pi / 4) * math.sqrt(n)))


def run_grover_search(num_qubits: int, marked_state: str, shots: int = 1024) -> dict:
    """
    Full Grover's algorithm: build circuit, run it, return results.
    """
    if len(marked_state) != num_qubits:
        raise ValueError(f"marked_state must be {num_qubits} bits long, got '{marked_state}'")
    if not all(b in "01" for b in marked_state):
        raise ValueError(f"marked_state must contain only 0s and 1s, got '{marked_state}'")

    iterations = optimal_iterations(num_qubits)

    qc = QuantumCircuit(num_qubits, num_qubits)
    qc.h(range(num_qubits))  # uniform superposition over all possible states

    oracle = build_oracle(num_qubits, marked_state)
    diffuser = build_diffuser(num_qubits)

    for _ in range(iterations):
        qc.compose(oracle, inplace=True)
        qc.compose(diffuser, inplace=True)

    qc.measure(range(num_qubits), range(num_qubits))

    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    total_states = 2 ** num_qubits
    classical_avg_lookups = total_states / 2  # average case, linear search
    quantum_lookups = iterations

    return {
        "marked_state": marked_state,
        "num_qubits": num_qubits,
        "iterations_used": iterations,
        "circuit_diagram_text": str(qc.draw(output="text")),
        "counts": counts,
        "probabilities": {k: round(v / shots, 4) for k, v in counts.items()},
        "success_probability": round(counts.get(marked_state, 0) / shots, 4),
        "classical_comparison": {
            "search_space_size": total_states,
            "classical_avg_lookups_needed": classical_avg_lookups,
            "quantum_oracle_calls_needed": quantum_lookups,
            "speedup_factor": round(classical_avg_lookups / quantum_lookups, 2) if quantum_lookups > 0 else None,
        },
    }
