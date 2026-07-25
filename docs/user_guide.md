# User Guide

**Project:** Enterprise Quantum Computing Platform — QFT Bank
**Student:** Syed Muhammad Tahoor Ali
**Diploma:** EduQual Level 6, Diploma in Artificial Intelligence Operations (ANPP-OP)

---

## 1. Getting Started

Open the platform in a browser at the deployment URL (in the Kubernetes deployment, `http://<minikube-ip>:30080`). The application is a single-page web app with a sidebar listing the modules. A status indicator confirms the backend is reachable. Select a module from the sidebar to open its screen; each screen is self-contained and can be used independently.

This guide walks through each module as a user of the web interface. No command line is needed.

---

## 2. Quantum Circuit Designer

Builds and runs a quantum circuit and shows the measurement results.

**How to use it.** Choose the number of qubits. Add gates one at a time from the supported set (Hadamard, Pauli X/Y/Z, S, T, the rotation gates rx/ry/rz, and the multi-qubit CX, CZ, SWAP, and Toffoli). For each gate, specify the qubit indices it acts on — the input accepts a list such as `0, 1`. Rotation gates additionally take an angle. Set the number of shots (measurement repetitions), then run.

**What you see.** The Results panel shows a text rendering of the assembled circuit, a histogram of measured bitstrings, and the probability distribution. A classic first experiment is a Bell state: apply Hadamard to qubit 0, then CX from qubit 0 to qubit 1, and observe an approximately even split between `00` and `11` — the signature of entanglement.

---

## 3. Quantum Algorithms

Demonstrates four enterprise-relevant quantum algorithms, each with its own controls.

**Grover's search.** Enter the number of qubits and the target bitstring (for example `101`). Grover amplifies the marked state so it dominates the measured distribution, finding it in far fewer evaluations than checking each possibility in turn.

**Quantum Fourier Transform.** Enter a number of qubits and an input basis state (for example `110`). The QFT is the quantum analogue of the discrete Fourier transform and underlies several important algorithms.

**QAOA (Max-Cut).** Provide a graph as a set of edges and a node count, with optional layer count and iteration cap. QAOA searches for a good cut of the graph; the result shows the best partition found.

**VQE.** Enter a qubit count and iteration cap. The Variational Quantum Eigensolver estimates a lowest-energy (ground-state) value by iteratively adjusting circuit parameters.

**What you see.** Each run shows the algorithm's output and execution statistics. Because these are genuine simulations, results reflect real quantum behaviour rather than pre-set answers.

---

## 4. Financial Portfolio Optimization

Optimizes a simulated investment portfolio and benchmarks the quantum result against an exact classical answer.

**How to use it.** Set the number of assets (up to eight), the budget (exactly how many assets to select), and optionally the risk-aversion and other tuning parameters. A seed keeps the simulated market reproducible. Run the optimization.

**What you see.** Three panels. *Simulated Market Data* shows the generated assets with their returns and volatilities. *Classical (Brute Force)* shows the exact optimum found by checking every combination — feasible because the asset count is capped. *Quantum (QAOA)* shows the solution the quantum optimiser reached, and whether it matched the classical optimum. This side-by-side is deliberately honest: it lets you verify the quantum result against ground truth rather than asserting an unfalsifiable advantage.

---

## 5. Executive Operations Dashboard

Aggregates activity from the other modules for a leadership view. It runs no new quantum computation.

**What you see.** Success rates by module, experiment counts by module, and a recent-activity feed drawn from the shared execution history. This is the screen intended for non-technical stakeholders who want the state of the programme at a glance rather than the details of any single run.

---

## 6. Post-Quantum Cryptography Readiness

An educational and governance screen on the quantum threat to cryptography and the path to quantum-safe algorithms.

**What you see.** A reference of current public-key algorithms and their vulnerability to quantum attack; the NIST post-quantum standards (ML-KEM, ML-DSA, SLH-DSA, HQC); a conceptual demonstration of quantum phase estimation (the mechanism behind Shor's algorithm, which threatens current cryptography); a simulated inventory scan that assigns risk scores to systems; an organizational risk assessment; and a phased migration plan. Together these show why an organisation should begin planning for post-quantum cryptography before large-scale quantum computers arrive.

---

## 7. Multi-Framework Comparison

Demonstrates that results are correct across quantum frameworks, not an artefact of one library.

**What you see.** The same Bell state constructed and run in Qiskit, PennyLane, and Cirq, with the three results shown side by side. Agreement across all three confirms framework-independent correctness and satisfies the specification's requirement to demonstrate PennyLane and Cirq alongside Qiskit.

---

## 8. Classical ML vs Quantum Optimization

Compares a classical machine-learning approach to asset selection against the quantum approach.

**How to use it.** Set the asset count, budget, and the number of simulated market scenarios used to train the model. Run the comparison.

**What you see.** The model training summary, the classical ML prediction on a fresh evaluation market, and the exact optimum for comparison. This situates the quantum approach against a classical learned baseline as well as against brute force.

---

## 9. Market Analytics

Presents a simulated market through three complementary visualisations.

**How to use it.** Set the number of assets and a seed, then generate.

**What you see.** A Pandas-derived summary table (per-asset return, volatility, correlation, return/risk ratio); an interactive chart (hover for exact figures, drag to zoom, double-click to reset); and a static chart image suitable for embedding in a report. The three views answer different questions — the numbers, interactive exploration, and a fixed printable snapshot respectively.

---

## 10. Tips

- The seed fields make runs reproducible: the same seed always produces the same simulated market, which is useful when comparing runs or preparing a demonstration.
- Qubit and asset counts are capped to keep simulations fast on modest hardware and to keep the classical baselines exactly computable.
- Every run that produces history is recorded and will appear in the Executive Dashboard's aggregated view.
