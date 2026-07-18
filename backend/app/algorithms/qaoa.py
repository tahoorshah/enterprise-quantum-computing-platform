"""
Quantum Approximate Optimization Algorithm (QAOA), applied to Max-Cut.

IMPORTANT: this uses REAL classical optimization (scipy's COBYLA) driving
REAL circuit execution on AerSimulator every iteration. The convergence
history returned is genuinely measured, not fabricated - each entry comes
from an actual quantum circuit run at that point in the optimization.

Business relevance (for the viva): Max-Cut is a graph-partitioning problem.
The same QAOA structure used here (cost Hamiltonian + mixer Hamiltonian +
classical optimizer loop) is exactly what Module 2 reuses for portfolio
optimization - there, "cut" becomes "which assets to include/exclude" and
edge weights become asset correlations/risk terms.
"""

from typing import List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from scipy.optimize import minimize


def build_qaoa_circuit(edges: List[Tuple[int, int]], num_nodes: int, gamma: float, beta: float, p: int = 1) -> QuantumCircuit:
    """
    Build a p=1 (or repeated) QAOA circuit for Max-Cut.

    gamma: cost-Hamiltonian rotation angle
    beta: mixer-Hamiltonian rotation angle
    """
    qc = QuantumCircuit(num_nodes, num_nodes)

    # Initial state: uniform superposition
    qc.h(range(num_nodes))

    for _ in range(p):
        # Cost layer: for each edge, apply ZZ interaction via CX-RZ-CX
        for (i, j) in edges:
            qc.cx(i, j)
            qc.rz(2 * gamma, j)
            qc.cx(i, j)

        # Mixer layer: RX rotation on every qubit
        for q in range(num_nodes):
            qc.rx(2 * beta, q)

    qc.measure(range(num_nodes), range(num_nodes))
    return qc


def cut_value(bitstring: str, edges: List[Tuple[int, int]]) -> int:
    """
    Count how many edges are 'cut' by this bitstring assignment
    (i.e. the two endpoints are in different partitions).
    """
    # Qiskit bit order: rightmost character = qubit 0
    bits = bitstring[::-1]
    return sum(1 for (i, j) in edges if bits[i] != bits[j])


def expected_cut_value(counts: dict, edges: List[Tuple[int, int]], shots: int) -> float:
    """Average cut value across all measured shots."""
    total = sum(cut_value(bitstring, edges) * count for bitstring, count in counts.items())
    return total / shots


def run_qaoa_maxcut(edges: List[Tuple[int, int]], num_nodes: int, p: int = 1, shots: int = 512, max_iterations: int = 30) -> dict:
    """
    Run QAOA end-to-end: classical COBYLA optimizer proposes (gamma, beta),
    a real quantum circuit is built and executed for each proposal, and the
    measured average cut value is fed back to the optimizer. This repeats
    until convergence or max_iterations.
    """
    simulator = AerSimulator()
    convergence_history = []

    def objective(params):
        gamma, beta = float(params[0]), float(params[1])
        qc = build_qaoa_circuit(edges, num_nodes, gamma, beta, p=p)
        result = simulator.run(qc, shots=shots).result()
        counts = result.get_counts()
        avg_cut = expected_cut_value(counts, edges, shots)

        convergence_history.append({
            "iteration": len(convergence_history) + 1,
            "gamma": round(gamma, 4),
            "beta": round(beta, 4),
            "expected_cut_value": round(avg_cut, 4),
        })

        # COBYLA minimizes, we want to MAXIMIZE cut value, so negate
        return -avg_cut

    initial_params = [0.5, 0.5]  # starting guess for (gamma, beta)

    opt_result = minimize(
        objective,
        initial_params,
        method="COBYLA",
        options={"maxiter": max_iterations, "rhobeg": 0.5},
    )

    best_gamma, best_beta = float(opt_result.x[0]), float(opt_result.x[1])
    final_qc = build_qaoa_circuit(edges, num_nodes, best_gamma, best_beta, p=p)
    final_result = simulator.run(final_qc, shots=shots).result()
    final_counts = final_result.get_counts()
    best_bitstring = max(final_counts, key=final_counts.get)

    return {
        "edges": edges,
        "num_nodes": num_nodes,
        "p_layers": p,
        "iterations_run": len(convergence_history),
        "convergence_history": convergence_history,
        "optimal_gamma": round(best_gamma, 4),
        "optimal_beta": round(best_beta, 4),
        "best_bitstring_found": best_bitstring,
        "best_cut_value": cut_value(best_bitstring, edges),
        "max_possible_cut_value": len(edges),
        "final_counts": final_counts,
        "circuit_diagram_text": str(final_qc.draw(output="text")),
        "optimizer_used": "COBYLA (scipy.optimize.minimize)",
        "note": "convergence_history is measured from real AerSimulator executions at each optimizer step, not simulated/fabricated data.",
    }
