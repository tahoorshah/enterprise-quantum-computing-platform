"""
Module 6 - Multi-Framework Quantum Demonstration.

The capstone technology stack requires Qiskit, PennyLane, AND Cirq. The
main platform is built on Qiskit; this module demonstrates the SAME
quantum computations implemented in PennyLane and Cirq as well, and
validates that all three agree with each other and with theory.

Two demonstrations, each implemented in all three frameworks:
  1. Bell state (entanglement) - H on qubit 0, CNOT to qubit 1.
     Expected: ~50/50 between |00> and |11>, never |01> or |10>.
  2. Single-qubit superposition - H on one qubit.
     Expected: ~50/50 between |0> and |1>.

VALIDATION METHOD: each framework's shot counts are converted to
probabilities and compared (a) against the theoretical distribution and
(b) pairwise against each other, using total variation distance, with a
tolerance derived from finite-shot sampling error.

DETERMINISM: an optional `seed` parameter fixes each simulator's RNG.
Without it, results vary run to run like real sampling. With it (used by
the test suite), results are exactly reproducible - a test suite that
occasionally fails on unlucky sampling is weak evidence; a seeded one
that always passes on the same inputs is strong evidence.
"""

import itertools
import math
from typing import Dict, List, Optional


# ============================================================
# QISKIT implementations
# ============================================================
def bell_state_qiskit(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    qc = QuantumCircuit(2, 2)
    qc.h(0)
    qc.cx(0, 1)
    qc.measure([0, 1], [0, 1])

    simulator = AerSimulator(seed_simulator=seed) if seed is not None else AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()
    return {
        "framework": "Qiskit",
        "counts": {k: v for k, v in counts.items()},
        "diagram": str(qc.draw(output="text")),
    }


def superposition_qiskit(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    from qiskit import QuantumCircuit
    from qiskit_aer import AerSimulator

    qc = QuantumCircuit(1, 1)
    qc.h(0)
    qc.measure([0], [0])

    simulator = AerSimulator(seed_simulator=seed) if seed is not None else AerSimulator()
    result = simulator.run(qc, shots=shots).result()
    counts = result.get_counts()
    return {
        "framework": "Qiskit",
        "counts": {k: v for k, v in counts.items()},
        "diagram": str(qc.draw(output="text")),
    }


# ============================================================
# PENNYLANE implementations
# ============================================================
def bell_state_pennylane(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    import pennylane as qml

    dev = qml.device("default.qubit", wires=2, seed=seed)

    @qml.set_shots(shots=shots)
    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(wires=0)
        qml.CNOT(wires=[0, 1])
        return qml.counts()

    raw = circuit()
    counts = {str(k): int(v) for k, v in raw.items()}
    return {
        "framework": "PennyLane",
        "counts": counts,
        "diagram": qml.draw(circuit)(),
    }


def superposition_pennylane(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    import pennylane as qml

    dev = qml.device("default.qubit", wires=1, seed=seed)

    @qml.set_shots(shots=shots)
    @qml.qnode(dev)
    def circuit():
        qml.Hadamard(wires=0)
        return qml.counts()

    raw = circuit()
    counts = {str(k): int(v) for k, v in raw.items()}
    return {
        "framework": "PennyLane",
        "counts": counts,
        "diagram": qml.draw(circuit)(),
    }


# ============================================================
# CIRQ implementations
# ============================================================
def bell_state_cirq(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    import cirq

    q0, q1 = cirq.LineQubit.range(2)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.CNOT(q0, q1),
        cirq.measure(q0, q1, key="result"),
    )

    simulator = cirq.Simulator(seed=seed)
    result = simulator.run(circuit, repetitions=shots)
    measurements = result.measurements["result"]
    counts: Dict[str, int] = {}
    for row in measurements:
        bitstring = "".join(str(int(b)) for b in row)
        counts[bitstring] = counts.get(bitstring, 0) + 1

    return {
        "framework": "Cirq",
        "counts": counts,
        "diagram": str(circuit),
    }


def superposition_cirq(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    import cirq

    q0 = cirq.LineQubit(0)
    circuit = cirq.Circuit(
        cirq.H(q0),
        cirq.measure(q0, key="result"),
    )

    simulator = cirq.Simulator(seed=seed)
    result = simulator.run(circuit, repetitions=shots)
    measurements = result.measurements["result"]
    counts: Dict[str, int] = {}
    for row in measurements:
        bitstring = "".join(str(int(b)) for b in row)
        counts[bitstring] = counts.get(bitstring, 0) + 1

    return {
        "framework": "Cirq",
        "counts": counts,
        "diagram": str(circuit),
    }


# ============================================================
# CROSS-FRAMEWORK VALIDATION
# ============================================================
def counts_to_probabilities(counts: Dict[str, int], num_qubits: int) -> Dict[str, float]:
    """Normalise shot counts to probabilities over the full outcome space."""
    total = sum(counts.values())
    all_outcomes = ["".join(bits) for bits in itertools.product("01", repeat=num_qubits)]
    return {o: counts.get(o, 0) / total if total else 0.0 for o in all_outcomes}


def total_variation_distance(p: Dict[str, float], q: Dict[str, float]) -> float:
    """TVD = 0.5 * sum |p(x) - q(x)|. 0 = identical, 1 = disjoint."""
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in keys)


def sampling_tolerance(shots: int, num_outcomes: int) -> float:
    """Tolerance for TVD between two independent finite-shot samples, with a 3x safety factor."""
    return 3 * (num_outcomes / (4 * math.sqrt(shots)))


def validate_agreement(framework_results: Dict[str, Dict], theoretical: Dict[str, float],
                       num_qubits: int, shots: int) -> Dict:
    """Compare every framework against theory and against each other."""
    num_outcomes = 2 ** num_qubits
    tolerance = sampling_tolerance(shots, num_outcomes)

    probabilities = {
        name: counts_to_probabilities(r["counts"], num_qubits)
        for name, r in framework_results.items()
    }

    vs_theory = {
        name: round(total_variation_distance(probs, theoretical), 5)
        for name, probs in probabilities.items()
    }

    pairwise = {}
    names = sorted(probabilities)
    for a, b in itertools.combinations(names, 2):
        pairwise[f"{a}_vs_{b}"] = round(
            total_variation_distance(probabilities[a], probabilities[b]), 5
        )

    max_theory_dev = max(vs_theory.values()) if vs_theory else 0.0
    max_pairwise_dev = max(pairwise.values()) if pairwise else 0.0

    return {
        "method": "Total variation distance between normalised shot distributions",
        "tolerance": round(tolerance, 5),
        "tolerance_basis": (
            f"Derived from sampling error at {shots} shots over {num_outcomes} "
            "outcomes, with a 3x safety factor. Tightens as shots increase."
        ),
        "observed_probabilities": {
            name: {k: round(v, 4) for k, v in probs.items()}
            for name, probs in probabilities.items()
        },
        "theoretical_probabilities": theoretical,
        "distance_from_theory": vs_theory,
        "pairwise_distance_between_frameworks": pairwise,
        "max_deviation_from_theory": round(max_theory_dev, 5),
        "max_deviation_between_frameworks": round(max_pairwise_dev, 5),
        "all_agree_with_theory": max_theory_dev <= tolerance,
        "all_agree_with_each_other": max_pairwise_dev <= tolerance,
    }


def run_bell_comparison(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    """Bell state across all three frameworks, with statistical validation."""
    results = {
        "qiskit": bell_state_qiskit(shots, seed=seed),
        "pennylane": bell_state_pennylane(shots, seed=seed),
        "cirq": bell_state_cirq(shots, seed=seed),
    }

    theoretical = {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.5}
    validation = validate_agreement(results, theoretical, num_qubits=2, shots=shots)

    forbidden_observed = {
        name: {o: c for o, c in r["counts"].items() if o in ("01", "10")}
        for name, r in results.items()
    }
    no_forbidden = all(not v for v in forbidden_observed.values())

    return {
        "demonstration": "Bell state (entanglement)",
        "circuit": "H on qubit 0, CNOT(0 -> 1)",
        "shots": shots,
        "results": results,
        "validation": validation,
        "forbidden_outcomes_observed": forbidden_observed,
        "no_forbidden_outcomes": no_forbidden,
    }


def run_superposition_comparison(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    """Single-qubit superposition across all three frameworks."""
    results = {
        "qiskit": superposition_qiskit(shots, seed=seed),
        "pennylane": superposition_pennylane(shots, seed=seed),
        "cirq": superposition_cirq(shots, seed=seed),
    }

    theoretical = {"0": 0.5, "1": 0.5}
    validation = validate_agreement(results, theoretical, num_qubits=1, shots=shots)

    return {
        "demonstration": "Single-qubit superposition",
        "circuit": "H on qubit 0",
        "shots": shots,
        "results": results,
        "validation": validation,
    }


def run_all_frameworks(shots: int = 1024, seed: Optional[int] = None) -> Dict:
    """Run both demonstrations on all three frameworks and report agreement."""
    bell = run_bell_comparison(shots, seed=seed)
    superposition = run_superposition_comparison(shots, seed=seed)

    all_valid = (
        bell["validation"]["all_agree_with_theory"]
        and bell["validation"]["all_agree_with_each_other"]
        and bell["no_forbidden_outcomes"]
        and superposition["validation"]["all_agree_with_theory"]
        and superposition["validation"]["all_agree_with_each_other"]
    )

    return {
        "frameworks_compared": ["Qiskit", "PennyLane", "Cirq"],
        "shots_per_framework": shots,
        "demonstrations": {
            "bell_state": bell,
            "superposition": superposition,
        },
        "cross_framework_validation_passed": all_valid,
        "explanation": (
            "The same two circuits were implemented independently in Qiskit, "
            "PennyLane, and Cirq. Each framework's measured shot distribution "
            "was normalised and compared against the theoretical distribution "
            "and against the other frameworks using total variation distance, "
            "with a tolerance derived from finite-shot sampling error. Agreement "
            "within that tolerance indicates the results are framework-independent. "
            "This validates correctness on simulators only; it says nothing about "
            "behaviour on physical quantum hardware, where noise dominates."
        ),
    }
