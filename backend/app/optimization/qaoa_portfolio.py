"""
Module 2 continued: QAOA circuit for the portfolio Ising Hamiltonian,
and the full pipeline tying market data -> QUBO -> QAOA -> comparison
against the classical brute-force optimum.

QAOA is a stochastic, sampling-based method: a single run is one draw, not
a result. The pipeline therefore runs the optimisation over several
independent trials and reports the distribution of outcomes (how often the
exact optimum was recovered, how often the cardinality constraint was
satisfied, and the spread of costs) rather than a single pass/fail.
"""

import time
from typing import List, Tuple
from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from scipy.optimize import minimize

from app.optimization.portfolio import (
    generate_simulated_market_data, build_qubo, qubo_to_ising,
    qubo_cost, brute_force_optimum, portfolio_metrics
)


def build_portfolio_qaoa_circuit(h, J, num_assets: int, gamma: float, beta: float, p: int = 1) -> QuantumCircuit:
    """
    QAOA circuit generalized for a weighted Ising Hamiltonian (unlike
    Module 3's Max-Cut version, which only had unweighted ZZ terms).

    Cost layer implements exp(-i*gamma*H) where H = sum h_i Z_i + sum J_ij Z_i Z_j:
      - RZ(2*gamma*h_i) on each qubit for the linear (h) terms
      - CX-RZ(2*gamma*J_ij)-CX on each pair for the quadratic (J) terms
    Mixer layer: RX(2*beta) on every qubit, same as standard QAOA.
    """
    qc = QuantumCircuit(num_assets, num_assets)
    qc.h(range(num_assets))

    for _ in range(p):
        # Linear terms
        for i in range(num_assets):
            if abs(h[i]) > 1e-12:
                qc.rz(2 * gamma * h[i], i)

        # Quadratic terms
        for i in range(num_assets):
            for j in range(i + 1, num_assets):
                if abs(J[i, j]) > 1e-12:
                    qc.cx(i, j)
                    qc.rz(2 * gamma * J[i, j], j)
                    qc.cx(i, j)

        # Mixer
        for q in range(num_assets):
            qc.rx(2 * beta, q)

    qc.measure(range(num_assets), range(num_assets))
    return qc


def selection_count(bitstring: str) -> int:
    """How many assets a bitstring actually selects (number of set bits)."""
    return sum(1 for b in bitstring if b == "1")


def run_qaoa_portfolio(h, J, offset: float, Q, num_assets: int, p: int = 1,
                        shots: int = 512, max_iterations: int = 30) -> dict:
    """
    Run QAOA against the portfolio Ising Hamiltonian, using real COBYLA
    optimization with genuine per-iteration circuit execution (same
    honesty standard as Module 3 - no fabricated convergence curves).
    """
    simulator = AerSimulator()
    convergence_history = []

    def objective(params):
        gamma, beta = float(params[0]), float(params[1])
        qc = build_portfolio_qaoa_circuit(h, J, num_assets, gamma, beta, p=p)
        result = simulator.run(qc, shots=shots).result()
        counts = result.get_counts()

        # Expected QUBO cost across all measured shots
        avg_cost = sum(qubo_cost(bitstring, Q) * count for bitstring, count in counts.items()) / shots

        convergence_history.append({
            "iteration": len(convergence_history) + 1,
            "gamma": round(gamma, 4),
            "beta": round(beta, 4),
            "expected_qubo_cost": round(avg_cost, 4),
        })

        return avg_cost  # we're minimizing cost directly, no sign flip needed here

    initial_params = [0.5, 0.5]

    opt_result = minimize(
        objective, initial_params, method="COBYLA",
        options={"maxiter": max_iterations, "rhobeg": 0.5},
    )

    best_gamma, best_beta = float(opt_result.x[0]), float(opt_result.x[1])
    final_qc = build_portfolio_qaoa_circuit(h, J, num_assets, best_gamma, best_beta, p=p)
    final_result = simulator.run(final_qc, shots=shots).result()
    final_counts = final_result.get_counts()
    best_bitstring = min(final_counts, key=lambda bs: qubo_cost(bs, Q))

    return {
        "iterations_run": len(convergence_history),
        "convergence_history": convergence_history,
        "optimal_gamma": round(best_gamma, 4),
        "optimal_beta": round(best_beta, 4),
        "best_bitstring_found": best_bitstring,
        "best_qubo_cost": round(qubo_cost(best_bitstring, Q), 4),
        "final_counts": final_counts,
        "circuit_diagram_text": str(final_qc.draw(output="text")),
    }


def run_portfolio_optimization(num_assets: int, budget: int, risk_aversion: float = 0.5,
                                penalty_weight: float = 2.0, shots: int = 512,
                                max_iterations: int = 30, p_layers: int = 1, seed: int = 42,
                                trials: int = 5) -> dict:
    """
    Full Module 2 pipeline: generate simulated market data, build the QUBO,
    solve classically (brute force, exact) AND via QAOA (quantum) over
    `trials` independent runs, then compare against real portfolio metrics.

    The classical brute force is deterministic and runs once - it is exact.
    QAOA is stochastic and runs `trials` times, so its reliability can be
    reported as a rate over repeated evaluation instead of a single outcome.
    """
    if num_assets > 8:
        raise ValueError("num_assets capped at 8 to keep brute-force comparison and QAOA runtime reasonable")
    if budget < 1 or budget >= num_assets:
        raise ValueError(f"budget must be between 1 and {num_assets - 1}")

    asset_names, expected_returns, covariance = generate_simulated_market_data(num_assets, seed=seed)
    Q = build_qubo(expected_returns, covariance, budget, risk_aversion, penalty_weight)
    h, J, offset = qubo_to_ising(Q)

    # Classical (exact, brute force) - deterministic, so a single run suffices
    start_classical = time.perf_counter()
    classical_bitstring, classical_cost = brute_force_optimum(Q)
    classical_time_ms = (time.perf_counter() - start_classical) * 1000
    classical_metrics = portfolio_metrics(classical_bitstring, expected_returns, covariance, asset_names)
    classical_selection_count = selection_count(classical_bitstring)

    # Quantum (QAOA) - stochastic, so repeat and report the distribution
    start_quantum = time.perf_counter()
    trial_records = []
    trial_raw = []

    for t in range(trials):
        qaoa_result = run_qaoa_portfolio(
            h, J, offset, Q, num_assets, p=p_layers,
            shots=shots, max_iterations=max_iterations,
        )
        bs = qaoa_result["best_bitstring_found"]
        n_selected = selection_count(bs)

        trial_records.append({
            "trial": t + 1,
            "bitstring": bs,
            "qubo_cost": qaoa_result["best_qubo_cost"],
            "assets_selected": n_selected,
            "cardinality_constraint_satisfied": n_selected == budget,
            "matched_classical_optimum": bs == classical_bitstring,
            "iterations_run": qaoa_result["iterations_run"],
        })
        trial_raw.append(qaoa_result)

    quantum_time_ms = (time.perf_counter() - start_quantum) * 1000

    # Best trial by QUBO cost - used for the detailed single-run view below
    best_index = min(range(trials), key=lambda i: trial_records[i]["qubo_cost"])
    best_trial = trial_raw[best_index]
    best_bitstring = best_trial["best_bitstring_found"]
    quantum_metrics = portfolio_metrics(best_bitstring, expected_returns, covariance, asset_names)

    matches = sum(1 for r in trial_records if r["matched_classical_optimum"])
    constraint_ok = sum(1 for r in trial_records if r["cardinality_constraint_satisfied"])
    costs = [r["qubo_cost"] for r in trial_records]
    mean_cost = sum(costs) / len(costs)

    return {
        "market_data": {
            "asset_names": asset_names,
            "expected_returns": [round(r, 4) for r in expected_returns.tolist()],
            "volatilities": [round(float(covariance[i, i] ** 0.5), 4) for i in range(num_assets)],
        },
        "problem_setup": {
            "num_assets": num_assets,
            "budget_assets_to_select": budget,
            "risk_aversion": risk_aversion,
            "penalty_weight": penalty_weight,
            "shots_per_circuit": shots,
            "max_optimizer_iterations": max_iterations,
            "qaoa_layers_p": p_layers,
            "market_data_seed": seed,
            "qaoa_trials": trials,
        },
        "classical_solution": {
            "method": "Brute force (exact, guaranteed optimal)",
            "bitstring": classical_bitstring,
            "qubo_cost": round(classical_cost, 4),
            "execution_time_ms": round(classical_time_ms, 3),
            "assets_selected": classical_selection_count,
            "cardinality_constraint_satisfied": classical_selection_count == budget,
            "portfolio_metrics": classical_metrics,
        },
        "quantum_solution": {
            "method": "QAOA (COBYLA-optimized, genuine per-iteration circuit execution)",
            "note_on_this_section": (
                "Detail shown is the single best trial of "
                f"{trials}, selected by lowest QUBO cost. Reliability across all "
                "trials is reported under repeated_evaluation."
            ),
            "bitstring": best_bitstring,
            "qubo_cost": best_trial["best_qubo_cost"],
            "total_execution_time_all_trials_ms": round(quantum_time_ms, 3),
            "iterations_run": best_trial["iterations_run"],
            "convergence_history": best_trial["convergence_history"],
            "optimal_gamma": best_trial["optimal_gamma"],
            "optimal_beta": best_trial["optimal_beta"],
            "circuit_diagram_text": best_trial["circuit_diagram_text"],
            "assets_selected": selection_count(best_bitstring),
            "cardinality_constraint_satisfied": selection_count(best_bitstring) == budget,
            "portfolio_metrics": quantum_metrics,
        },
        "repeated_evaluation": {
            "trials_run": trials,
            "per_trial": trial_records,
            "times_matched_classical_optimum": matches,
            "optimum_recovery_rate": round(matches / trials, 4),
            "times_cardinality_constraint_satisfied": constraint_ok,
            "cardinality_satisfaction_rate": round(constraint_ok / trials, 4),
            "qubo_cost_best": round(min(costs), 4),
            "qubo_cost_worst": round(max(costs), 4),
            "qubo_cost_mean": round(mean_cost, 4),
            "interpretation": (
                f"Across {trials} independent QAOA runs on identical inputs, the exact "
                f"optimum was recovered {matches} time(s). This rate describes this "
                "problem instance at this parameter setting on a simulator, and should "
                "not be generalised to other instances, larger asset counts, or hardware."
            ),
        },
        "comparison": {
            "quantum_matched_classical_optimum": best_bitstring == classical_bitstring,
            "cost_difference": round(best_trial["best_qubo_cost"] - classical_cost, 4),
            "note": (
                "For small problems like this, brute force is exact and typically faster in wall-clock "
                "time since it avoids simulator overhead. QAOA's advantage is theoretical: it doesn't "
                "need to enumerate all 2^n combinations, which matters as n grows far beyond what brute "
                "force can handle. This demo intentionally uses small n so results can be verified exactly. "
                "No speed advantage is claimed or measured here."
            ),
        },
    }
