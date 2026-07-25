# Quantum Experiment Report

**Project:** Enterprise Quantum Computing Platform — QFT Bank
**Student:** Syed Muhammad Tahoor Ali
**Diploma:** EduQual Level 6, Diploma in Artificial Intelligence Operations (ANPP-OP)
**Execution environment:** Qiskit Aer simulator, Kubernetes deployment (Minikube)

---

## 1. Purpose

This report documents representative quantum experiments run on the platform, with the actual results produced by the Qiskit Aer simulator. Its purpose is twofold: to demonstrate that the platform produces genuine quantum behaviour, and to record concrete, reproducible results that can be verified against theory. All figures below are real measured output, not illustrative values.

---

## 2. Experiment 1 — Bell State (Entanglement Verification)

**Objective.** Confirm the platform produces genuine quantum entanglement, the foundational two-qubit phenomenon.

**Circuit.** Two qubits. A Hadamard gate on qubit 0 creates superposition; a CNOT from qubit 0 to qubit 1 entangles them. Measured over 1024 shots.

**Measured result.**

| Outcome | Count | Proportion |
|---|---|---|
| `00` | 529 | 51.7% |
| `11` | 495 | 48.3% |
| `01` | 0 | 0% |
| `10` | 0 | 0% |

**Interpretation.** The two qubits are measured in the same state every time — either both 0 or both 1 — in an approximately even split, and the mixed outcomes `01` and `10` never occur. This is the exact signature of the Bell state (|00⟩ + |11⟩)/√2: the qubits are correlated such that measuring one determines the other, regardless of the ~50/50 split between the two joint outcomes. The complete absence of `01` and `10` confirms the entanglement is genuine rather than two independent coin-flips, which would have produced all four outcomes at ~25% each. Execution completed in approximately 12 ms.

This result is why the platform includes a standalone sanity check: before any higher-level result is trusted, the simulator is shown to produce correct, verifiable quantum behaviour on a known circuit.

---

## 3. Experiment 2 — Grover's Search

**Objective.** Demonstrate quantum search finding a marked item in an unstructured space faster than classical checking.

**Setup.** A 3-qubit search space (8 possible states). Target marked state: `101`. Measured over 1024 shots.

**Measured result.**

| Outcome | Count | Probability |
|---|---|---|
| `101` (target) | 980 | 95.7% |
| all seven others | 44 combined | 4.3% combined |

Grover applied 2 amplification iterations.

**Interpretation.** Grover's algorithm concentrated almost the entire probability mass — 95.7% — onto the single marked state after just 2 iterations, leaving the other seven states with negligible probability. Classically, finding a marked item in an unstructured set of 8 requires up to 8 checks (on average 4). Grover requires approximately √8 ≈ 3 evaluations; here 2 iterations sufficed to make the target overwhelmingly likely. This is the quadratic speed-up Grover provides: the number of iterations grows as the square root of the search-space size rather than linearly.

**Business relevance.** For QFT Bank, Grover-style search is relevant wherever an unstructured search dominates cost — for example scanning large transaction or key spaces. The quadratic speed-up does not break these problems open the way Shor's algorithm breaks factoring, but it is a genuine and general acceleration.

---

## 4. Reproducibility

Both experiments are deterministic in method and reproducible in behaviour. The Bell state always yields a two-outcome distribution over `00` and `11` with no mixed outcomes; Grover always concentrates probability on the marked state. Exact counts vary slightly between runs because measurement is probabilistic (1024 independent shots), but the distributions are stable. The experiments can be re-run through the web interface (Circuit Designer and Quantum Algorithms screens) or via the API endpoints `POST /api/quantum/execute` and `POST /api/algorithms/grover`.

---

## 5. Conclusion

The platform produces genuine, theory-consistent quantum results on the Qiskit Aer simulator. Entanglement is demonstrated cleanly (no leakage into impossible states), and Grover's quadratic search advantage is demonstrated concretely (95.7% concentration on the target in 2 iterations). These results establish that the higher-level applications built on the same simulator — portfolio optimization, algorithm demonstrations, and the PQC threat model — rest on correct quantum foundations rather than fabricated output.
