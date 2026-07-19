import { useState } from "react";
import { api } from "../api";

// Module 2 - Financial Portfolio Optimization Platform.
// Sets up a portfolio problem, runs both classical (brute-force) and quantum
// (QAOA) solvers on the backend, and shows them side by side.

export default function Portfolio() {
  const [numAssets, setNumAssets] = useState(4);
  const [budget, setBudget] = useState(2);
  const [riskAversion, setRiskAversion] = useState(0.5);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.optimizePortfolio({
        num_assets: Number(numAssets),
        budget: Number(budget),
        risk_aversion: Number(riskAversion),
        shots: 512,
        max_iterations: 25,
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
      <h2>Financial Portfolio Optimization</h2>
      <p className="subtitle">
        Select the best assets using classical brute-force vs quantum QAOA,
        on simulated market data.
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
            Risk aversion (0 = ignore risk, higher = avoid risk):
            <input
              type="number"
              min="0"
              max="5"
              step="0.1"
              value={riskAversion}
              onChange={(e) => setRiskAversion(e.target.value)}
            />
          </label>
        </div>

        <div style={{ marginTop: "1rem" }}>
          <button className="btn-primary" onClick={run} disabled={loading}>
            {loading ? "Optimizing..." : "Optimize Portfolio"}
          </button>
        </div>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && <PortfolioResult data={result.result} />}
    </div>
  );
}

function PortfolioResult({ data }) {
  const md = data.market_data;
  const classical = data.classical_solution;
  const quantum = data.quantum_solution;
  const comparison = data.comparison;

  return (
    <>
      {/* Market data */}
      <div className="card">
        <h3>Simulated Market Data</h3>
        <table className="data-table">
          <thead>
            <tr>
              <th>Asset</th>
              <th>Expected Return</th>
              <th>Volatility</th>
            </tr>
          </thead>
          <tbody>
            {md.asset_names.map((name, i) => (
              <tr key={name}>
                <td>{name}</td>
                <td>{(md.expected_returns[i] * 100).toFixed(2)}%</td>
                <td>{(md.volatilities[i] * 100).toFixed(2)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Side by side comparison */}
      <div className="comparison-grid">
        <div className="card">
          <h3>Classical (Brute Force)</h3>
          <p className="method-note">{classical.method}</p>
          <SolutionMetrics sol={classical} />
        </div>
        <div className="card result-card">
          <h3>Quantum (QAOA)</h3>
          <p className="method-note">{quantum.method}</p>
          <SolutionMetrics sol={quantum} />
        </div>
      </div>

      {/* Verdict */}
      <div
        className={`verdict ${
          comparison.quantum_matched_classical_optimum ? "match" : "nomatch"
        }`}
      >
        {comparison.quantum_matched_classical_optimum
          ? "✓ QAOA found the exact same optimal portfolio as brute force."
          : "✗ QAOA found a different (sub-optimal) portfolio this run."}
      </div>

      {/* Convergence */}
      {quantum.convergence_history && (
        <div className="card">
          <ConvergenceChart
            history={quantum.convergence_history}
            valueKey="expected_qubo_cost"
            label="Expected QUBO Cost (lower = better)"
          />
        </div>
      )}
    </>
  );
}

function SolutionMetrics({ sol }) {
  const m = sol.portfolio_metrics;
  return (
    <div>
      <p>
        <strong>Selected assets:</strong>{" "}
        {m.selected_assets.join(", ") || "(none)"}
      </p>
      <p>
        <strong>Expected return:</strong> {(m.expected_return * 100).toFixed(2)}%
      </p>
      <p>
        <strong>Risk (std dev):</strong> {(m.risk_std_dev * 100).toFixed(2)}%
      </p>
      <p>
        <strong>Sharpe-like ratio:</strong>{" "}
        {m.sharpe_like_ratio !== null ? m.sharpe_like_ratio : "n/a"}
      </p>
      <p className="muted">
        Time: {sol.execution_time_ms} ms
      </p>
    </div>
  );
}

// Same SVG convergence chart pattern as Module 3.
function ConvergenceChart({ history, valueKey, label }) {
  if (!history || history.length === 0) return null;

  const values = history.map((h) => h[valueKey]);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  const width = 500;
  const height = 160;
  const pad = 30;

  const points = history.map((h, i) => {
    const x = pad + (i / (history.length - 1 || 1)) * (width - 2 * pad);
    const y = height - pad - ((h[valueKey] - min) / range) * (height - 2 * pad);
    return `${x},${y}`;
  });

  return (
    <>
      <h4>Convergence — {label}</h4>
      <svg width={width} height={height} className="convergence-chart">
        <polyline
          points={points.join(" ")}
          fill="none"
          stroke="#4f8cff"
          strokeWidth="2"
        />
        {history.map((h, i) => {
          const x = pad + (i / (history.length - 1 || 1)) * (width - 2 * pad);
          const y =
            height - pad - ((h[valueKey] - min) / range) * (height - 2 * pad);
          return <circle key={i} cx={x} cy={y} r="2.5" fill="#4f8cff" />;
        })}
      </svg>
    </>
  );
}
