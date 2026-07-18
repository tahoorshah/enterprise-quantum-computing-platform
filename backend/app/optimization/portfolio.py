"""
Module 2 - Financial Portfolio Optimization Platform.

Maps portfolio selection (which assets to include, given a fixed budget
of how many to pick) onto a QUBO (Quadratic Unconstrained Binary
Optimization) problem, then an Ising Hamiltonian, so QAOA (built in
Module 3) can solve it. Compares against a classical brute-force
optimum, which is exact/guaranteed-correct for the small asset counts
used here - giving an honest, verifiable classical-vs-quantum comparison
rather than a claim that can't be checked.

Business relevance (for the viva): this is the standard way portfolio
selection is mapped onto quantum hardware in the literature (e.g. IBM's
and D-Wave's finance use-cases) - minimize risk, maximize return, subject
to a cardinality constraint (pick exactly k of N assets), formulated as
a QUBO and solved variationally.
"""

import itertools
from typing import List, Tuple, Dict
import numpy as np


def generate_simulated_market_data(num_assets: int, seed: int = 42) -> Tuple[List[str], np.ndarray, np.ndarray]:
    """
    Generate a small, reproducible simulated market dataset:
    - asset names
    - expected_returns: 1D array, annualized expected return per asset
    - covariance: 2D array, asset return covariance matrix (risk)

    Reproducible (fixed seed) so results are consistent between runs -
    the spec requires "simulated financial datasets," not live market data.
    """
    rng = np.random.default_rng(seed)

    asset_names = [f"ASSET_{chr(65 + i)}" for i in range(num_assets)]  # ASSET_A, ASSET_B, ...

    expected_returns = rng.uniform(0.04, 0.18, size=num_assets)  # 4%-18% annual return

    # Build a valid covariance matrix: random correlations, positive-definite
    volatilities = rng.uniform(0.10, 0.35, size=num_assets)  # 10%-35% annual volatility
    correlation = rng.uniform(-0.3, 0.7, size=(num_assets, num_assets))
    correlation = (correlation + correlation.T) / 2  # symmetric
    np.fill_diagonal(correlation, 1.0)

    # Ensure positive semi-definite by nudging eigenvalues up if needed
    eigvals = np.linalg.eigvalsh(correlation)
    if eigvals.min() < 0:
        correlation += np.eye(num_assets) * (abs(eigvals.min()) + 0.01)

    covariance = np.outer(volatilities, volatilities) * correlation

    return asset_names, expected_returns, covariance


def build_qubo(expected_returns: np.ndarray, covariance: np.ndarray,
               budget: int, risk_aversion: float = 0.5, penalty_weight: float = 2.0) -> np.ndarray:
    """
    Build the QUBO matrix Q such that x^T Q x is the objective to MINIMIZE,
    for binary decision variables x_i in {0, 1} (1 = include asset i).

    Objective = risk_aversion * (portfolio variance) - (expected return)
                + penalty_weight * (cardinality constraint violation)^2

    The cardinality penalty (sum(x_i) - budget)^2 pushes the optimizer
    toward selecting exactly `budget` assets, since unconstrained QUBO/QAOA
    has no native way to enforce "pick exactly k" otherwise.
    """
    n = len(expected_returns)
    Q = np.zeros((n, n))

    # Risk term: risk_aversion * x^T Covariance x
    Q += risk_aversion * covariance

    # Return term: -expected_returns on the diagonal (since x_i^2 = x_i for binary)
    for i in range(n):
        Q[i, i] -= expected_returns[i]

    # Cardinality penalty: penalty_weight * (sum(x_i) - budget)^2
    # Expand: sum(x_i^2) + 2*sum_{i<j} x_i*x_j - 2*budget*sum(x_i) + budget^2
    # x_i^2 = x_i for binary variables, so it folds into the diagonal.
    for i in range(n):
        Q[i, i] += penalty_weight * (1 - 2 * budget)
        for j in range(n):
            if i != j:
                Q[i, j] += penalty_weight  # will be halved below since Q is symmetric-counted twice

    # Q[i,j] and Q[j,i] both got the off-diagonal penalty added -> that's
    # correct since x^T Q x sums both Q[i,j]*x_i*x_j and Q[j,i]*x_j*x_i,
    # and we want the total cross term to be 2*penalty_weight per pair.

    return Q


def qubo_to_ising(Q: np.ndarray) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Convert QUBO (binary x_i in {0,1}) to Ising form (spin z_i in {-1,+1})
    via x_i = (1 - z_i) / 2.

    Assumes Q is symmetric (true for how build_qubo constructs it, since
    covariance matrices and the cardinality penalty are both symmetric
    by construction).

    Derivation: x^T Q x = sum_i Q_ii*x_i + 2*sum_{i<j} Q_ij*x_i*x_j (Q symmetric)
    Substituting x_i = (1-z_i)/2 and collecting terms gives:
        offset = sum_i(Q_ii)/2 + sum_{i<j}(Q_ij)/2
        h_k    = -Q_kk/2 - (1/2) * sum_{j != k} Q_kj
        J_ij   = Q_ij / 2   (for i < j)

    Returns:
        h: linear (single-qubit Z) coefficients, shape (n,)
        J: quadratic (ZZ) coefficients, shape (n,n), only upper triangle (i<j) used
        offset: constant term (doesn't affect optimization, just for completeness)
    """
    n = Q.shape[0]
    h = np.zeros(n)
    J = np.zeros((n, n))

    diag_sum = float(np.trace(Q))
    offdiag_sum = float((np.sum(Q) - diag_sum) / 2)  # sum over i<j of Q_ij (Q symmetric)
    offset = diag_sum / 2 + offdiag_sum / 2

    for k in range(n):
        row_sum_excl_diag = float(np.sum(Q[k, :]) - Q[k, k])
        h[k] = -Q[k, k] / 2 - row_sum_excl_diag / 2

    for i in range(n):
        for j in range(i + 1, n):
            J[i, j] = Q[i, j] / 2

    return h, J, offset


def qubo_cost(bitstring: str, Q: np.ndarray) -> float:
    """Evaluate x^T Q x for a given bitstring (rightmost char = asset 0)."""
    x = np.array([int(b) for b in reversed(bitstring)])
    return float(x @ Q @ x)


def brute_force_optimum(Q: np.ndarray) -> Tuple[str, float]:
    """
    Exact classical solution via brute force - guaranteed correct for
    small n. Used as the ground truth to evaluate QAOA's result against.
    Only feasible for small num_assets (this project caps at 8).
    """
    n = Q.shape[0]
    best_bitstring = None
    best_cost = float("inf")

    for combo in itertools.product([0, 1], repeat=n):
        x = np.array(combo)
        cost = float(x @ Q @ x)
        if cost < best_cost:
            best_cost = cost
            # bitstring convention: rightmost char = asset 0
            best_bitstring = "".join(str(b) for b in reversed(combo))

    return best_bitstring, best_cost


def portfolio_metrics(bitstring: str, expected_returns: np.ndarray, covariance: np.ndarray, asset_names: List[str]) -> Dict:
    """Compute expected return, risk (std dev), and a Sharpe-like ratio for a selected portfolio."""
    x = np.array([int(b) for b in reversed(bitstring)])
    selected_indices = [i for i, bit in enumerate(x) if bit == 1]

    if not selected_indices:
        return {
            "selected_assets": [],
            "num_selected": 0,
            "expected_return": 0.0,
            "risk_std_dev": 0.0,
            "sharpe_like_ratio": None,
        }

    n_selected = len(selected_indices)
    weights = np.zeros(len(expected_returns))
    for i in selected_indices:
        weights[i] = 1.0 / n_selected  # equal-weight among selected assets

    port_return = float(weights @ expected_returns)
    port_variance = float(weights @ covariance @ weights)
    port_std = float(np.sqrt(port_variance)) if port_variance > 0 else 0.0

    return {
        "selected_assets": [asset_names[i] for i in selected_indices],
        "num_selected": n_selected,
        "expected_return": round(port_return, 4),
        "risk_std_dev": round(port_std, 4),
        "sharpe_like_ratio": round(port_return / port_std, 4) if port_std > 0 else None,
    }
