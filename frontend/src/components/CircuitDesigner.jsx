import { useState } from "react";
import { api } from "../api";

// Module 1 - Quantum Circuit Design Platform.
// Lets the user build a small circuit by adding gates, then runs it on the
// backend (AerSimulator) and shows the circuit diagram + measurement results.

export default function CircuitDesigner() {
  const [numQubits, setNumQubits] = useState(2);
  const [shots, setShots] = useState(1024);
  const [gates, setGates] = useState([
    { gate: "h", qubits: [0] },
    { gate: "cx", qubits: [0, 1] },
  ]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Add a new blank gate row
  const addGate = () => {
    setGates([...gates, { gate: "h", qubits: [0] }]);
  };

  // Remove a gate row by index
  const removeGate = (index) => {
    setGates(gates.filter((_, i) => i !== index));
  };

  // Update a gate's name
  const updateGateName = (index, name) => {
    const next = [...gates];
    next[index] = { ...next[index], gate: name };
    setGates(next);
  };

  // Update a gate's qubit list (comma-separated string -> array of ints)
  const updateGateQubits = (index, value) => {
    const qubits = value
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s !== "")
      .map((s) => parseInt(s, 10))
      .filter((n) => !isNaN(n));
    const next = [...gates];
    next[index] = { ...next[index], qubits };
    setGates(next);
  };

  const runCircuit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        num_qubits: Number(numQubits),
        gates: gates,
        shots: Number(shots),
      };
      const data = await api.executeCircuit(payload);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Quantum Circuit Designer</h2>
      <p className="subtitle">
        Build a circuit gate-by-gate and execute it on the quantum simulator.
      </p>

      <div className="card">
        <div className="field-row">
          <label>
            Number of qubits:
            <input
              type="number"
              min="1"
              max="20"
              value={numQubits}
              onChange={(e) => setNumQubits(e.target.value)}
            />
          </label>
          <label>
            Shots:
            <input
              type="number"
              min="1"
              max="10000"
              value={shots}
              onChange={(e) => setShots(e.target.value)}
            />
          </label>
        </div>

        <h3>Gates</h3>
        <table className="gate-table">
          <thead>
            <tr>
              <th>Gate</th>
              <th>Qubits (comma-separated)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {gates.map((g, i) => (
              <tr key={i}>
                <td>
                  <select
                    value={g.gate}
                    onChange={(e) => updateGateName(i, e.target.value)}
                  >
                    <option value="h">H (Hadamard)</option>
                    <option value="x">X</option>
                    <option value="y">Y</option>
                    <option value="z">Z</option>
                    <option value="s">S</option>
                    <option value="t">T</option>
                    <option value="rx">RX</option>
                    <option value="ry">RY</option>
                    <option value="rz">RZ</option>
                    <option value="cx">CX (CNOT)</option>
                    <option value="cz">CZ</option>
                    <option value="swap">SWAP</option>
                    <option value="ccx">CCX (Toffoli)</option>
                  </select>
                </td>
                <td>
                  <input
                    type="text"
                    value={g.qubits.join(", ")}
                    onChange={(e) => updateGateQubits(i, e.target.value)}
                    placeholder="e.g. 0, 1"
                  />
                </td>
                <td>
                  <button className="btn-small" onClick={() => removeGate(i)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <button className="btn-secondary" onClick={addGate}>
          + Add Gate
        </button>

        <div style={{ marginTop: "1rem" }}>
          <button className="btn-primary" onClick={runCircuit} disabled={loading}>
            {loading ? "Running..." : "Run Circuit"}
          </button>
        </div>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && (
        <div className="card result-card">
          <h3>Results</h3>
          <p>
            <strong>Execution ID:</strong> {result.execution_id}
          </p>
          <p>
            <strong>Execution time:</strong> {result.execution_time_ms} ms
          </p>

          <h4>Circuit Diagram</h4>
          <pre className="diagram">{result.circuit_diagram_text}</pre>

          <h4>Measurement Counts</h4>
          <div className="counts-grid">
            {Object.entries(result.counts).map(([state, count]) => (
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
        </div>
      )}
    </div>
  );
}
