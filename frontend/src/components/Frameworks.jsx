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

// Runs the Qiskit and native-framework implementations of the same
// algorithm side by side, so a single "did it converge to the same place?"
// comparison stands next to the multi-framework Bell state demo above.
function AlgorithmComparisonSection({
  title,
  description,
  runBoth,
  renderCard,
  renderVerdict,
}) {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const [qiskit, other] = await Promise.all(runBoth());
      setResult({ qiskit: qiskit.result, other: other.result });
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ marginBottom: "2rem" }}>
      <h3>{title}</h3>
      <p style={{ color: "var(--text-dim)", fontSize: "0.9rem" }}>{description}</p>

      <div className="card" style={{ marginBottom: "1rem" }}>
        <button className="btn-primary" onClick={run} disabled={loading}>
          {loading ? "Running on both frameworks..." : "Run Comparison"}
        </button>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && (
        <>
          {renderVerdict(result)}
          <div className="comparison-grid">
            {renderCard("Qiskit", result.qiskit)}
            {renderCard(result.other.framework, result.other)}
          </div>
        </>
      )}
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

      <AlgorithmComparisonSection
        title="Grover's Search — Qiskit vs. Cirq"
        description={
          'Runs the same oracle/diffuser construction, searching for the same ' +
          'marked state "101" over 3 qubits, on both frameworks and compares ' +
          "the resulting success probabilities."
        }
        runBoth={() => [
          api.runGrover({ num_qubits: 3, marked_state: "101", shots: 1024 }),
          api.runGroverCirq({ num_qubits: 3, marked_state: "101", shots: 1024 }),
        ]}
        renderVerdict={({ qiskit, other }) => {
          const diff = Math.abs(
            qiskit.success_probability - other.success_probability
          );
          const agree = diff <= 0.1;
          return (
            <div className={`verdict ${agree ? "match" : "nomatch"}`}>
              {agree
                ? `✓ Success probabilities agree within sampling tolerance (Δ = ${diff.toFixed(3)}).`
                : `✗ Success probabilities diverge more than expected (Δ = ${diff.toFixed(3)}).`}
            </div>
          );
        }}
        renderCard={(label, r) => (
          <div className="card">
            <h3>{label}</h3>
            <p>
              <strong>Success probability:</strong>{" "}
              {(r.success_probability * 100).toFixed(1)}%
            </p>
            <p>
              <strong>Iterations used:</strong> {r.iterations_used} &nbsp;|&nbsp;
              <strong> Oracle calls:</strong>{" "}
              {r.query_complexity_comparison.quantum_oracle_calls_needed}
            </p>
            {r.bit_order_note && (
              <p style={{ color: "var(--text-dim)", fontSize: "0.8rem" }}>
                {r.bit_order_note}
              </p>
            )}
          </div>
        )}
      />

      <AlgorithmComparisonSection
        title="VQE — Qiskit vs. PennyLane"
        description={
          "Runs the same hardware-efficient ansatz against the same demo " +
          "Hamiltonian (sum of Pauli-Z on 3 qubits, theoretical minimum energy " +
          "-3) on both frameworks and compares how close each converges."
        }
        runBoth={() => [
          api.runVQE({ num_qubits: 3, max_iterations: 40 }),
          api.runVQEPennylane({ num_qubits: 3, max_iterations: 40 }),
        ]}
        renderVerdict={({ qiskit, other }) => {
          const agree = qiskit.converged_within <= 0.2 && other.converged_within <= 0.2;
          return (
            <div className={`verdict ${agree ? "match" : "nomatch"}`}>
              {agree
                ? "✓ Both frameworks converged close to the theoretical minimum energy."
                : "✗ At least one framework did not converge close to the theoretical minimum."}
            </div>
          );
        }}
        renderCard={(label, r) => (
          <div className="card">
            <h3>{label}</h3>
            <p>
              <strong>Final energy:</strong> {r.final_energy} &nbsp;|&nbsp;
              <strong> Theoretical minimum:</strong> {r.theoretical_minimum_energy}
            </p>
            <p>
              <strong>Converged within:</strong> {r.converged_within} &nbsp;|&nbsp;
              <strong> Iterations run:</strong> {r.iterations_run}
            </p>
          </div>
        )}
      />
    </div>
  );
}
