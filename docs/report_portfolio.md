# Portfolio Optimization Report

**Project:** Enterprise Quantum Computing Platform — QFT Bank
**Student:** Syed Muhammad Tahoor Ali
**Diploma:** EduQual Level 6, Diploma in Artificial Intelligence Operations (ANPP-OP)
**Method:** QAOA (COBYLA-optimised) benchmarked against exact classical brute force

---

## 1. Purpose

This report documents a representative run of the Financial Portfolio Optimization module (Module 2), with the actual results produced by the platform. It shows how asset selection is mapped to a quantum-solvable problem, how the quantum optimiser performs against an exact classical baseline, and what the comparison honestly demonstrates. All figures are real output.

---

## 2. Problem Setup

A simulated market of six assets, from which exactly three are to be selected. Reproducible via seed.

| Asset | Expected Return | Volatility (Risk) |
|---|---|---|
| ASSET_A | 0.1484 | 0.2903 |
| ASSET_B | 0.1014 | 0.2965 |
| ASSET_C | 0.1602 | 0.1320 |
| ASSET_D | 0.1376 | 0.2126 |
| ASSET_E | 0.0532 | 0.1927 |
| ASSET_F | 0.1766 | 0.3317 |

Parameters: budget = 3 assets, risk aversion = 0.5, constraint penalty weight = 2.0.

**Method.** Asset selection is encoded as a QUBO (Quadratic Unconstrained Binary Optimisation) problem: each asset is a binary variable (selected or not), the objective rewards return and penalises risk (weighted by risk aversion), and a penalty term enforces the "select exactly three" constraint. The QUBO is converted to an Ising Hamiltonian, which QAOA optimises. The same QUBO is also solved exactly by classical brute force for comparison.

---

## 3. Classical Baseline (Exact)

| Property | Value |
|---|---|
| Method | Brute force (exact, guaranteed optimal) |
| Selected assets | ASSET_C, ASSET_D, ASSET_F |
| Bitstring | `101100` |
| QUBO cost | −18.3574 |
| Execution time | ~2.0 ms |

Brute force checks all 2⁶ = 64 combinations and is guaranteed to return the true optimum. It is feasible here precisely because the asset count is capped at eight, keeping the search space small enough to enumerate exactly. This exact baseline is what makes the quantum result verifiable rather than an unfalsifiable claim.

The selected portfolio (C, D, F) is intuitive: ASSET_C combines the highest return-per-unit-risk (0.1602 return at only 0.1320 volatility), while D and F add return, balanced against the risk penalty.

---

## 4. Quantum Result (QAOA)

| Property | Value |
|---|---|
| Method | QAOA, COBYLA-optimised, genuine per-iteration circuit execution |
| Selected assets | ASSET_C, ASSET_D, ASSET_F |
| Bitstring | `101100` |
| QUBO cost | −18.3574 |
| Optimiser iterations | 29 |
| Execution time | ~7100 ms |

**Convergence.** The COBYLA optimiser adjusted the QAOA circuit parameters (gamma, beta) across 29 iterations, with the expected QUBO cost improving as it searched. The early trajectory of the expected cost was approximately:

| Iteration | Expected QUBO cost |
|---|---|
| 1 | −9.14 |
| 2 | −9.98 |
| 3 | −10.44 |
| 4 | −17.20 |
| … | … (converging toward the optimum) |

This convergence data is produced by real per-iteration circuit execution on the simulator, not by a pre-computed curve. The improvement from −9.14 toward the optimal −18.36 is the optimiser genuinely learning better circuit parameters.

---

## 5. Comparison and Honest Assessment

| Metric | Result |
|---|---|
| Quantum matched classical optimum | **Yes** |
| Cost difference | 0.0 |
| Classical time | ~2 ms |
| Quantum time | ~7100 ms |

**The quantum solution exactly matched the classical optimum** — same assets, same bitstring, same cost, zero difference. This is the key correctness result: QAOA found the genuinely optimal portfolio.

On wall-clock time, brute force was roughly 3500× faster. This is stated plainly rather than hidden, because it is the honest picture for a problem of this size: brute force avoids simulator overhead, and for six assets there are only 64 combinations to check. QAOA's advantage is asymptotic — it does not need to enumerate all 2ⁿ combinations, which is what makes it relevant as n grows far beyond the range where brute force remains tractable. The demonstration deliberately uses a small n so that the quantum result can be checked exactly against ground truth; claiming a speed advantage at this scale would be false.

---

## 6. Business Relevance

For QFT Bank, this demonstrates a credible path: portfolio selection can be expressed as a QUBO and solved by a quantum optimiser that reaches the correct answer. At the scales where classical exact methods become infeasible, the quantum approach — and the approximate classical methods that would replace brute force as the baseline — become the only options. The value of this proof-of-concept is not a speed claim today but a demonstrated, correct, end-to-end quantum optimisation pipeline that scales in principle.

---

## 7. Reproducibility

The run is reproducible via the seed, which fixes the simulated market. It can be repeated through the Portfolio Optimization screen or the `POST /api/optimization/portfolio` endpoint with the same parameters. The classical baseline is deterministic; the quantum result is stable in outcome, with minor per-run variation in the optimiser trajectory.
