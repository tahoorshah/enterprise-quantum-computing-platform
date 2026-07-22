import { useState } from "react";
import { api } from "../api";

// Module 7 - Classical Machine Learning vs Quantum Optimization.
// Trains a scikit-learn RandomForest on many simulated markets (labelled by the
// exact brute-force optimum), then compares its prediction against the exact
// optimum on a fresh market. Highlights the key difference: the ML model is
// constraint-UNAWARE, while the quantum optimizer enforces the budget.

export default function MLComparison() {
  const [numAssets, setNumAssets] = useState(5);
  const [budget, setBudget] = useState(2);
  const [numScenarios, setNumScenarios] = useState(60);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.mlCompare({
        num_assets: Number(numAssets),
        budget: Number(budget),
        num_scenarios: Number(numScenarios),
        eval_seed: 42,
      });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Classical ML vs Quantum Optimization</h2>
      <p className="subtitle">
        A classical machine-learning model (scikit-learn RandomForest) learns to
        pick portfolios from simulated markets, then is compared against the exact
        optimum — showing where a learned heuristic and a constrained optimizer differ.
      </p>

      <div className="card">
        <div className="field-row">
          <label>
            Number of assets:
            <input
              type="number"
              min="3"
              max="8"
              value={numAssets}
              onChange={(e) => setNumAssets(e.target.value)}
            />
          </label>
          <label>
            Assets to select (budget):
            <input
              type="number"
              min="1"
              max={Number(numAssets) - 1}
              value={budget}
              onChange={(e) => setBudget(e.target.value)}
            />
          </label>
          <label>
            Training scenarios (markets):
            <input
              type="number"
              min="20"
              max="200"
              value={numScenarios}
              onChange={(e) => setNumScenarios(e.target.value)}
            />
          </label>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <button className="btn-primary" onClick={run} disabled={loading}>
            {loading ? "Training model..." : "Train & Compare"}
          </button>
        </div>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && <MLResult data={result.result} />}
    </div>
  );
}

function MLResult({ data }) {
  const training = data.training;
  const mlPred = data.ml_prediction;
  const optimum = data.exact_optimum;
  const comparison = data.comparison;

  return (
    <>
      {/* Training summary */}
      <div className="card">
        <h3>Model Training</h3>
        <p className="method-note">
          Trained on {training.num_scenarios} simulated markets
          ({training.training_rows} labelled asset rows). Labels come from the exact
          brute-force optimum.
        </p>
        <div className="comparison-grid">
          <div>
            <p>
              <strong>Train accuracy:</strong>{" "}
              {(training.train_accuracy * 100).toFixed(1)}%
            </p>
            <p>
              <strong>Test accuracy:</strong>{" "}
              {(training.test_accuracy * 100).toFixed(1)}%
            </p>
            <p className="muted">
              Per-asset selection accuracy on a held-out 25% test split.
            </p>
          </div>
          <div>
            <FeatureImportance fi={training.feature_importance} />
          </div>
        </div>
      </div>

      {/* Side by side: ML prediction vs exact optimum */}
      <div className="comparison-grid">
        <div className="card">
          <h3>Classical ML Prediction</h3>
          <p className="method-note">RandomForest (constraint-unaware)</p>
          <p>
            <strong>Selected assets:</strong>{" "}
            {mlPred.selected_assets.join(", ") || "(none)"}
          </p>
          <p>
            <strong>Expected return:</strong>{" "}
            {(mlPred.portfolio_metrics.expected_return * 100).toFixed(2)}%
          </p>
          <p>
            <strong>Risk (std dev):</strong>{" "}
            {(mlPred.portfolio_metrics.risk_std_dev * 100).toFixed(2)}%
          </p>
          <p className="muted">
            Raw model picked {mlPred.raw_selected_count} asset(s); budget required{" "}
            {mlPred.budget_required}. Budget enforced by taking top-probability assets.
          </p>
        </div>
        <div className="card result-card">
          <h3>Exact Optimum</h3>
          <p className="method-note">{optimum.method}</p>
          <p>
            <strong>Selected assets:</strong>{" "}
            {optimum.selected_assets.join(", ") || "(none)"}
          </p>
          <p>
            <strong>Expected return:</strong>{" "}
            {(optimum.portfolio_metrics.expected_return * 100).toFixed(2)}%
          </p>
          <p>
            <strong>Risk (std dev):</strong>{" "}
            {(optimum.portfolio_metrics.risk_std_dev * 100).toFixed(2)}%
          </p>
          <p className="muted">QUBO cost: {optimum.qubo_cost}</p>
        </div>
      </div>

      {/* Verdict */}
      <div
        className={`verdict ${
          comparison.ml_matched_exact_optimum ? "match" : "nomatch"
        }`}
      >
        {comparison.ml_matched_exact_optimum
          ? "✓ The ML model's selection matched the exact optimum this run."
          : "✗ The ML model's selection differed from the exact optimum — the learned heuristic diverged from the true optimizer."}
      </div>

      {/* The key insight */}
      <div className="card">
        <h4>Why this matters</h4>
        <p>
          The classical ML model predicts each asset independently and has no model
          of the cardinality constraint (&quot;pick exactly {mlPred.budget_required}&quot;),
          so its raw output can select the wrong number of assets. The quantum
          optimizer (QAOA in Module 2) enforces that constraint directly through a
          penalty term in the QUBO. This is the core difference between a fast learned
          heuristic and a constrained optimizer.
        </p>
      </div>
    </>
  );
}

function FeatureImportance({ fi }) {
  const rows = [
    ["Expected return", fi.expected_return],
    ["Volatility", fi.volatility],
    ["Mean correlation", fi.mean_correlation],
  ];
  const max = Math.max(...rows.map((r) => r[1])) || 1;

  return (
    <div>
      <h4>Feature Importance</h4>
      {rows.map(([label, val]) => (
        <div key={label} style={{ marginBottom: "0.4rem" }}>
          <div style={{ fontSize: "0.85rem", marginBottom: "0.15rem" }}>
            {label}: {(val * 100).toFixed(1)}%
          </div>
          <div
            style={{
              background: "#2a2f3a",
              borderRadius: "3px",
              height: "8px",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                width: `${(val / max) * 100}%`,
                background: "#4f8cff",
                height: "100%",
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
