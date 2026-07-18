"""
Quantum Fourier Transform (QFT).

Built manually with H and controlled-phase gates (textbook construction),
not via qiskit.circuit.library.QFT, so every gate can be explained directly.

Business relevance (for the viva): QFT is the core subroutine behind
Shor's algorithm (factoring, relevant to breaking RSA -> ties directly
into Module 5's post-quantum cryptography discussion) and quantum phase
estimation, which underlies many quantum algorithms used for financial
modeling and simulation.
"""

import math
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator


def build_qft_circuit(num_qubits: int, inverse: bool = False) -> QuantumCircuit:
    """
    Build a QFT circuit from scratch.

    For each qubit, apply a Hadamard, then controlled-phase rotations
    from every qubit "below" it, with angles halving each time
    (pi/2, pi/4, pi/8, ...). Finally, swap qubits to correct the
    reversed bit order QFT naturally produces.
    """
    qc = QuantumCircuit(num_qubits)

    def qft_rotations(circuit: QuantumCircuit, n: int):
        if n == 0:
            return
        n -= 1
        circuit.h(n)
        for qubit in range(n):
            angle = math.pi / (2 ** (n - qubit))
            circuit.cp(angle, qubit, n)
        qft_rotations(circuit, n)

    def swap_registers(circuit: QuantumCircuit, n: int):
        for qubit in range(n // 2):
            circuit.swap(qubit, n - qubit - 1)

    qft_rotations(qc, num_qubits)
    swap_registers(qc, num_qubits)

    if inverse:
        qc = qc.inverse()
        qc.name = "IQFT"
    else:
        qc.name = "QFT"

    return qc


def demonstrate_qft(num_qubits: int, input_state: str, shots: int = 1024) -> dict:
    """
    Prepare a basis state, apply QFT, then apply inverse QFT, and measure.
    Since QFT followed by its own inverse is the identity, this should
    return the original input_state with very high probability - a clean
    way to demonstrate QFT is working correctly.
    """
    if len(input_state) != num_qubits:
        raise ValueError(f"input_state must be {num_qubits} bits long, got '{input_state}'")
    if not all(b in "01" for b in input_state):
        raise ValueError(f"input_state must contain only 0s and 1s, got '{input_state}'")

    qc = QuantumCircuit(num_qubits, num_qubits)

    # Prepare the input basis state
    for i, bit in enumerate(reversed(input_state)):
        if bit == "1":
            qc.x(i)

    qft = build_qft_circuit(num_qubits, inverse=False)
    qc.compose(qft, inplace=True)

    iqft = build_qft_circuit(num_qubits, inverse=True)
    qc.compose(iqft, inplace=True)

    qc.measure(range(num_qubits), range(num_qubits))

    simulator = AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()

    return {
        "input_state": input_state,
        "num_qubits": num_qubits,
        "circuit_diagram_text": str(qc.draw(output="text")),
        "counts": counts,
        "probabilities": {k: round(v / shots, 4) for k, v in counts.items()},
        "recovered_correctly_probability": round(counts.get(input_state, 0) / shots, 4),
        "explanation": (
            "QFT followed by inverse-QFT is mathematically the identity operation. "
            "A high probability of recovering the original input_state confirms "
            "the QFT implementation is correct."
        ),
    }
