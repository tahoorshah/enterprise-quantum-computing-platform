"""
Module 5 - quantum threat demonstration via Quantum Phase Estimation (QPE).

WHY QPE, NOT FULL SHOR'S ALGORITHM: implementing Shor's algorithm properly
requires building a controlled modular-exponentiation unitary from scratch,
which is a large, bug-prone undertaking even for tiny numbers. QPE is the
actual general-purpose subroutine Shor's algorithm is built on top of
(Shor's = QPE applied specifically to a modular-multiplication unitary).
Demonstrating QPE genuinely, correctly, and reusing Module 3's own QFT
code is more honest than a superficial "Shor's algorithm" demo that
either doesn't really work or hardcodes its answer.

Business relevance (for the viva): QPE/Shor's algorithm is THE reason
RSA and ECC (elliptic-curve cryptography) - which underpin almost all
of today's banking TLS connections, digital signatures, and key
exchange - are considered broken by a sufficiently large quantum
computer. This is the concrete technical justification for Module 5's
migration-planning content: the threat isn't hypothetical hand-waving,
it's this specific algorithmic capability.
"""

import math
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator

from app.algorithms.qft import build_qft_circuit


def build_qpe_circuit(theta: float, num_counting_qubits: int) -> QuantumCircuit:
    """
    Estimate an unknown phase theta (in [0, 1), representing an eigenvalue
    e^(2*pi*i*theta) of a unitary) using Quantum Phase Estimation.

    Here the unitary is a simple phase gate P(2*pi*theta) applied to a
    target qubit prepared in its eigenstate |1>. In Shor's algorithm, the
    unitary is instead modular multiplication by a random base 'a' mod N,
    and QPE recovers the PERIOD of that operation - which is what lets
    Shor's algorithm factor N. Same QPE machinery, different unitary.
    """
    qc = QuantumCircuit(num_counting_qubits + 1, num_counting_qubits)

    counting_qubits = list(range(num_counting_qubits))
    target_qubit = num_counting_qubits

    # Prepare target qubit in the |1> eigenstate of the phase gate
    qc.x(target_qubit)

    # Uniform superposition on counting qubits
    qc.h(counting_qubits)

    # Controlled-U^(2^k) for each counting qubit - this is where the
    # unknown phase gets "kicked back" into the counting register
    for k in range(num_counting_qubits):
        angle = 2 * math.pi * theta * (2 ** k)
        qc.cp(angle, k, target_qubit)

    # Inverse QFT on the counting register converts the phase information
    # into a directly measurable integer - REUSES Module 3's QFT code
    iqft = build_qft_circuit(num_counting_qubits, inverse=True)
    qc.compose(iqft, qubits=counting_qubits, inplace=True)

    qc.measure(counting_qubits, range(num_counting_qubits))
    return qc


def run_qpe_demo(theta: float, num_counting_qubits: int = 4, shots: int = 1024) -> dict:
    """
    Run QPE and check whether it correctly recovers the known input phase
    theta - demonstrating the real mechanism, not a fabricated result.
    """
    if not (0 <= theta < 1):
        raise ValueError(f"theta must be in [0, 1), got {theta}")
    if not (1 <= num_counting_qubits <= 8):
        raise ValueError("num_counting_qubits must be between 1 and 8")

    qc = build_qpe_circuit(theta, num_counting_qubits)

    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    # Convert each measured bitstring to its implied phase estimate
    max_value = 2 ** num_counting_qubits
    phase_estimates = {}
    for bitstring, count in counts.items():
        measured_int = int(bitstring, 2)
        estimated_theta = measured_int / max_value
        phase_estimates[bitstring] = {
            "measured_integer": measured_int,
            "estimated_theta": round(estimated_theta, 4),
            "count": count,
            "probability": round(count / shots, 4),
        }

    best_bitstring = max(counts, key=counts.get)
    best_estimate = phase_estimates[best_bitstring]["estimated_theta"]

    return {
        "true_theta": theta,
        "num_counting_qubits": num_counting_qubits,
        "precision": f"1/{max_value} = {round(1/max_value, 4)}",
        "circuit_diagram_text": str(qc.draw(output="text")),
        "counts": counts,
        "phase_estimates": phase_estimates,
        "most_likely_estimate": best_estimate,
        "estimation_error": round(abs(best_estimate - theta), 4),
        "explanation": (
            "Quantum Phase Estimation (QPE) is the general-purpose subroutine that Shor's "
            "algorithm applies to a modular-exponentiation unitary in order to find the period "
            "of that function, which is the step that allows Shor's algorithm to factor large "
            "numbers efficiently. This demo applies the same QPE machinery (reusing this "
            "platform's own QFT implementation from Module 3) to a simple phase gate with a "
            "known phase, to demonstrate that the mechanism genuinely recovers phase information "
            "rather than assuming it. RSA and ECC's security relies on factoring/discrete-log "
            "problems being hard for classical computers - QPE-based algorithms like Shor's "
            "break that assumption on a sufficiently large, fault-tolerant quantum computer."
        ),
    }
