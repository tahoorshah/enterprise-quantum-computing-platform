import { useState } from "react";
import { api } from "../api";

// Multi-Framework Demonstration - runs Bell state AND superposition across
// Qiskit, PennyLane, and Cirq, statistically validating agreement rather
// than just checking that no forbidden outcome appeared.

function FrameworkGrid({ results, shots }) {
  return (
    <div className="framework-grid">
      {Object.values(results).map((fw) => (
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
                  style={{ width: `${(count / shots) * 100}%` }}
                />
              </div>
            ))}
          </div>
          <h4>Circuit</h4>
          <pre className="diagram framework-diagram">{fw.diagram}</pre>
        </div>
      ))}
    </div>
  );
}

function DemonstrationSection({ demo }) {
  const v = demo.validation;
  const agree = v.all_agree_with_theory && v.all_agree_with_each_other;

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3>{demo.demonstration}</h3>
      <p style={{ color: "var(--text-dim)", fontSize: "0.9rem" }}>
        Circuit: {demo.circuit} &nbsp;|&nbsp; Shots: {demo.shots}
      </p>

      <div className={`verdict ${agree ? "match" : "nomatch"}`}>
        {agree
          ? "✓ All three frameworks statistically agree with theory and each other."
          : "✗ Statistical disagreement detected — see distances below."}
      </div>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <p style={{ fontSize: "0.85rem", color: "var(--text-dim)" }}>
          Method: {v.method}. Tolerance: {v.tolerance} ({v.tolerance_basis})
        </p>
        <p style={{ fontSize: "0.85rem" }}>
          Max deviation from theory: {v.max_deviation_from_theory} &nbsp;|&nbsp;
          Max deviation between frameworks: {v.max_deviation_between_frameworks}
        </p>
      </div>

      {demo.no_forbidden_outcomes !== undefined && (
        <div className={`verdict ${demo.no_forbidden_outcomes ? "match" : "nomatch"}`}>
          {demo.no_forbidden_outcomes
            ? "✓ No forbidden outcomes (|01⟩ or |10⟩) observed in any framework."
            : "✗ A forbidden outcome was observed."}
        </div>
      )}

      <FrameworkGrid results={demo.results} shots={demo.shots} />
    </div>
  );
}

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
        Run a Bell state and a single-qubit superposition across Qiskit,
        PennyLane, and Cirq, and statistically validate that all three agree.
      </p>

      <div className="card">
        <p style={{ marginBottom: "1rem", color: "var(--text-dim)", fontSize: "0.9rem" }}>
          Each framework's measured shot distribution is compared against
          theory and against the other frameworks using total variation
          distance, with a tolerance derived from finite-shot sampling error.
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
              result.cross_framework_validation_passed ? "match" : "nomatch"
            }`}
            style={{ marginTop: "1rem" }}
          >
            {result.cross_framework_validation_passed
              ? "✓ Cross-framework validation passed for both demonstrations."
              : "✗ Cross-framework validation failed — see details below."}
          </div>

          <p style={{ color: "var(--text-dim)", fontSize: "0.85rem", margin: "0.5rem 0 1.5rem" }}>
            {result.explanation}
          </p>

          <DemonstrationSection demo={result.demonstrations.bell_state} />
          <DemonstrationSection demo={result.demonstrations.superposition} />
        </>
      )}
    </div>
  );
}
