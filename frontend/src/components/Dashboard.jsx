import { useState, useEffect } from "react";
import { api } from "../api";

// Module 4 - Executive Quantum Operations Dashboard.
// Read-only aggregation of everything run across Modules 1-3 (and PQC).
// Auto-loads on mount; a Refresh button re-pulls the latest numbers.

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [kpis, setKpis] = useState(null);
  const [history, setHistory] = useState([]);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [ov, kp, hist] = await Promise.all([
        api.dashboardOverview(),
        api.dashboardKpis(),
        api.dashboardHistory(),
      ]);
      setOverview(ov);
      setKpis(kp);
      setHistory(hist);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // Load once when the screen first opens
  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h2>Executive Quantum Operations Dashboard</h2>
      <p className="subtitle">
        Real-time overview of quantum experiments, success rates, and activity across the platform.
      </p>

      <button className="btn-secondary" onClick={load} disabled={loading}>
        {loading ? "Refreshing..." : "↻ Refresh"}
      </button>

      {error && <div className="error-box">Error: {error}</div>}

      {kpis && (
        <div className="kpi-grid">
          <KpiCard
            label="Total Experiments Run"
            value={kpis.total_quantum_experiments_run}
          />
          <KpiCard
            label="Overall Success Rate"
            value={
              kpis.overall_success_rate !== null
                ? `${(kpis.overall_success_rate * 100).toFixed(1)}%`
                : "—"
            }
          />
          <KpiCard
            label="Portfolio Runs"
            value={kpis.portfolio_optimizations_run}
          />
          <KpiCard
            label="Quantum/Classical Agreement"
            value={
              kpis.portfolio_quantum_classical_agreement_rate !== null
                ? `${(
                    kpis.portfolio_quantum_classical_agreement_rate * 100
                  ).toFixed(0)}%`
                : "—"
            }
          />
        </div>
      )}

      {overview && (
        <div className="card">
          <h3>Success Rates by Module</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Module</th>
                <th>Attempts</th>
                <th>Successes</th>
                <th>Failures</th>
                <th>Success Rate</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(overview.success_rates_by_module).map(
                ([mod, s]) => (
                  <tr key={mod}>
                    <td>{mod}</td>
                    <td>{s.attempts}</td>
                    <td>{s.successes}</td>
                    <td>{s.failures}</td>
                    <td>
                      {s.success_rate !== null
                        ? `${(s.success_rate * 100).toFixed(0)}%`
                        : "—"}
                    </td>
                  </tr>
                )
              )}
            </tbody>
          </table>
        </div>
      )}

      {overview && (
        <div className="card">
          <h3>Experiments by Module</h3>
          <div className="module-counts">
            {Object.entries(overview.experiments_by_module).map(([mod, n]) => (
              <div key={mod} className="module-count-item">
                <span className="module-count-value">{n}</span>
                <span className="module-count-label">
                  {mod.replace(/_/g, " ")}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <h3>Recent Activity</h3>
        {history.length === 0 ? (
          <p className="muted">
            No experiments recorded yet. Run something in another module, then
            refresh.
          </p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Module</th>
                <th>Summary</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {history.slice(0, 15).map((h) => (
                <tr key={h.execution_id}>
                  <td>{h.module.replace(/_/g, " ")}</td>
                  <td>{h.summary}</td>
                  <td className="muted">
                    {new Date(h.timestamp).toLocaleTimeString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

function KpiCard({ label, value }) {
  return (
    <div className="kpi-card">
      <div className="kpi-value">{value}</div>
      <div className="kpi-label">{label}</div>
    </div>
  );
}
