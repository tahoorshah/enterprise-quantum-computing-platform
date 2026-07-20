import { useState } from "react";
import { api } from "../api";

// Multi-Framework Demonstration - runs the same Bell-state circuit across
// Qiskit, PennyLane, and Cirq and shows their results side by side.

export default function Frameworks() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.compareFrameworks(1024);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Multi-Framework Comparison</h2>
      <p className="subtitle">
        Run the same quantum circuit across Qiskit, PennyLane, and Cirq to
        confirm framework-independent results.
      </p>

      <div className="card">
        <p style={{ marginBottom: "1rem", color: "var(--text-dim)", fontSize: "0.9rem" }}>
          This runs a Bell state (Hadamard + CNOT) on all three quantum
          frameworks. Correct entanglement means only |00⟩ and |11⟩ appear —
          never |01⟩ or |10⟩ — in every framework.
        </p>
        <button className="btn-primary" onClick={run} disabled={loading}>
          {loading ? "Running on all frameworks..." : "Run Comparison"}
        </button>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && (
        <>
          <div
            className={`verdict ${
              result.all_frameworks_show_entanglement ? "match" : "nomatch"
            }`}
          >
            {result.all_frameworks_show_entanglement
              ? "✓ All three frameworks produced the correct entangled result (only |00⟩ and |11⟩)."
              : "✗ Frameworks disagreed — unexpected outcome."}
          </div>

          <div className="framework-grid">
            {Object.values(result.results).map((fw) => (
              <div key={fw.framework} className="card framework-card">
                <h3>{fw.framework}</h3>
                <h4>Measurement Counts</h4>
                <div className="counts-grid">
                  {Object.entries(fw.counts).map(([state, count]) => (
                    <div key={state} className="count-item">
                      <span className="count-state">|{state}⟩</span>
                      <span className="count-value">{count}</span>
                      <div
                        className="count-bar"
                        style={{
                          width: `${(count / result.shots) * 100}%`,
                        }}
                      />
                    </div>
                  ))}
                </div>
                <h4>Circuit</h4>
                <pre className="diagram framework-diagram">{fw.diagram}</pre>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
