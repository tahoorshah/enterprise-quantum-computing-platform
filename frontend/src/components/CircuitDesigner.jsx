import { useState } from "react";
import { api } from "../api";

// Module 1 - Quantum Circuit Design Platform.
// Lets the user build a small circuit by adding gates, then runs it on the
// backend (AerSimulator) and shows the circuit diagram + measurement results.

// Gates that need an angle parameter (radians). Used only to hint the UI.
const PARAM_GATES = new Set(["rx", "ry", "rz"]);

export default function CircuitDesigner() {
  const [numQubits, setNumQubits] = useState(2);
  const [shots, setShots] = useState(1024);
  // Gate rows keep the user's RAW text while typing. We only parse into
  // numbers when the circuit is actually run - that way commas and decimal
  // points are never eaten mid-typing.
  const [gates, setGates] = useState([
    { gate: "h", qubitsText: "0", paramsText: "" },
    { gate: "cx", qubitsText: "0, 1", paramsText: "" },
  ]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Add a new blank gate row
  const addGate = () => {
    setGates([...gates, { gate: "h", qubitsText: "0", paramsText: "" }]);
  };

  // Remove a gate row by index
  const removeGate = (index) => {
    setGates(gates.filter((_, i) => i !== index));
  };

  // Update any field on a gate row. For text fields we store the raw string
  // exactly as typed (no parsing here), so "0, 1" and "1.57" survive.
  const updateGateField = (index, field, value) => {
    const next = [...gates];
    next[index] = { ...next[index], [field]: value };
    setGates(next);
  };

  // Parse a comma-separated string into numbers, at run time only.
  const parseInts = (text) =>
    text
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s !== "")
      .map((s) => parseInt(s, 10))
      .filter((n) => !isNaN(n));

  const parseFloats = (text) =>
    text
      .split(",")
      .map((s) => s.trim())
      .filter((s) => s !== "")
      .map((s) => parseFloat(s))
      .filter((n) => !isNaN(n));

  const runCircuit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      // Build the backend payload from the raw text, parsing here (once).
      const parsedGates = gates.map((g) => {
        const qubits = parseInts(g.qubitsText);
        const params = parseFloats(g.paramsText);
        const gateObj = { gate: g.gate, qubits };
        if (params.length > 0) gateObj.params = params;
        return gateObj;
      });

      const payload = {
        num_qubits: Number(numQubits),
        gates: parsedGates,
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
        Design a quantum circuit gate-by-gate and execute it on the simulator.
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
              <th>Parameters (angle in radians)</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {gates.map((g, i) => (
              <tr key={i}>
                <td>
                  <select
                    value={g.gate}
                    onChange={(e) => updateGateField(i, "gate", e.target.value)}
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
                    inputMode="text"
                    value={g.qubitsText}
                    onChange={(e) =>
                      updateGateField(i, "qubitsText", e.target.value)
                    }
                    placeholder="e.g. 0, 1"
                  />
                </td>
                <td>
                  <input
                    type="text"
                    inputMode="text"
                    value={g.paramsText}
                    onChange={(e) =>
                      updateGateField(i, "paramsText", e.target.value)
                    }
                    placeholder={
                      PARAM_GATES.has(g.gate) ? "e.g. 1.57" : "(not needed)"
                    }
                    disabled={!PARAM_GATES.has(g.gate)}
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
