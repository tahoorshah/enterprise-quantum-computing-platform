"""
Variational Quantum Eigensolver (VQE).

Finds the approximate ground-state (minimum) energy of a given Hamiltonian
using a parametrized quantum circuit (ansatz) plus REAL classical
optimization (scipy COBYLA). Uses exact statevector expectation values
(not sampling) since that is standard practice for small VQE demos and
keeps convergence behavior clean to explain in the viva.

Business relevance (for the viva): VQE is the standard near-term algorithm
for finding ground-state energies of Hamiltonians on noisy quantum
hardware. In finance, the same variational structure (parametrized
circuit + classical optimizer loop) is used for portfolio risk
minimization - Module 2 reuses this exact pattern, just with a
Hamiltonian built from covariance/return data instead of a toy problem.
"""

from typing import List
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, SparsePauliOp
from scipy.optimize import minimize


def build_ansatz(num_qubits: int, params: List[float]) -> QuantumCircuit:
    """
    A simple hardware-efficient ansatz: one layer of RY rotations
    (one parameter per qubit) followed by a ladder of CX entangling gates.
    """
    qc = QuantumCircuit(num_qubits)

    for q in range(num_qubits):
        qc.ry(params[q], q)

    for q in range(num_qubits - 1):
        qc.cx(q, q + 1)

    return qc


def expectation_value(qc: QuantumCircuit, hamiltonian: SparsePauliOp) -> float:
    """
    Compute <psi|H|psi> exactly using the statevector (no sampling noise).
    Appropriate for small demo problems; for larger real problems this
    would be estimated via repeated measurement (shots) instead.
    """
    statevector = Statevector.from_instruction(qc)
    return float(statevector.expectation_value(hamiltonian).real)


def default_demo_hamiltonian(num_qubits: int) -> SparsePauliOp:
    """
    A simple, well-understood demo Hamiltonian: sum of Z operators on
    each qubit, e.g. for 2 qubits: H = Z⊗I + I⊗Z.
    Its exact ground-state energy is -num_qubits (all qubits in |1>),
    which makes it easy to verify VQE actually converged correctly.
    """
    terms = []
    for q in range(num_qubits):
        pauli_string = ["I"] * num_qubits
        pauli_string[q] = "Z"
        # SparsePauliOp reads left-to-right as qubit (n-1)...qubit 0
        terms.append(("".join(reversed(pauli_string)), 1.0))
    return SparsePauliOp.from_list(terms)


def run_vqe(num_qubits: int, max_iterations: int = 50) -> dict:
    """
    Run VQE end-to-end against the default demo Hamiltonian.
    """
    hamiltonian = default_demo_hamiltonian(num_qubits)
    convergence_history = []

    def objective(params):
        qc = build_ansatz(num_qubits, params)
        energy = expectation_value(qc, hamiltonian)
        convergence_history.append({
            "iteration": len(convergence_history) + 1,
            "energy": round(energy, 6),
        })
        return energy

    initial_params = [0.1] * num_qubits

    opt_result = minimize(
        objective,
        initial_params,
        method="COBYLA",
        options={"maxiter": max_iterations, "rhobeg": 0.5},
    )

    final_params = [float(p) for p in opt_result.x]
    final_qc = build_ansatz(num_qubits, final_params)
    final_energy = expectation_value(final_qc, hamiltonian)

    theoretical_minimum = -float(num_qubits)  # exact ground state energy for this Hamiltonian

    return {
        "num_qubits": num_qubits,
        "hamiltonian_description": f"Sum of Pauli-Z on each of {num_qubits} qubits",
        "iterations_run": len(convergence_history),
        "convergence_history": convergence_history,
        "final_parameters": [round(p, 4) for p in final_params],
        "final_energy": round(final_energy, 6),
        "theoretical_minimum_energy": theoretical_minimum,
        "converged_within": round(abs(final_energy - theoretical_minimum), 6),
        "circuit_diagram_text": str(final_qc.draw(output="text")),
        "optimizer_used": "COBYLA (scipy.optimize.minimize)",
        "note": "convergence_history is measured from real statevector expectation values at each optimizer step, not simulated/fabricated data.",
    }
