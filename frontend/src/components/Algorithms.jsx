import { useState } from "react";
import { api } from "../api";

// Module 3 - Quantum Algorithm Demonstration Platform.
// Four algorithms, each with its own inputs. A tab picker switches between
// them; results (including convergence for QAOA/VQE) render below.

const ALGOS = [
  { id: "grover", label: "Grover's Search" },
  { id: "qft", label: "Quantum Fourier Transform" },
  { id: "qaoa", label: "QAOA (Max-Cut)" },
  { id: "vqe", label: "VQE" },
];

export default function Algorithms() {
  const [algo, setAlgo] = useState("grover");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  // Inputs for each algorithm
  const [groverQubits, setGroverQubits] = useState(3);
  const [groverMarked, setGroverMarked] = useState("101");
  const [qftQubits, setQftQubits] = useState(3);
  const [qftInput, setQftInput] = useState("110");
  const [qaoaEdges, setQaoaEdges] = useState("0,1; 1,2; 0,2");
  const [qaoaNodes, setQaoaNodes] = useState(3);
  const [vqeQubits, setVqeQubits] = useState(3);

  const switchAlgo = (id) => {
    setAlgo(id);
    setResult(null);
    setError(null);
  };

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      let data;
      if (algo === "grover") {
        data = await api.runGrover({
          num_qubits: Number(groverQubits),
          marked_state: groverMarked,
          shots: 1024,
        });
      } else if (algo === "qft") {
        data = await api.runQFT({
          num_qubits: Number(qftQubits),
          input_state: qftInput,
          shots: 1024,
        });
      } else if (algo === "qaoa") {
        // Parse "0,1; 1,2; 0,2" into [[0,1],[1,2],[0,2]]
        const edges = qaoaEdges
          .split(";")
          .map((pair) => pair.trim())
          .filter((pair) => pair !== "")
          .map((pair) => pair.split(",").map((n) => parseInt(n.trim(), 10)));
        data = await api.runQAOA({
          edges: edges,
          num_nodes: Number(qaoaNodes),
          p_layers: 1,
          shots: 512,
          max_iterations: 20,
        });
      } else if (algo === "vqe") {
        data = await api.runVQE({
          num_qubits: Number(vqeQubits),
          max_iterations: 40,
        });
      }
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2>Quantum Algorithms</h2>
      <p className="subtitle">
        Demonstrate Grover's search, QFT, QAOA, and VQE on the simulator.
      </p>

      <div className="tab-row">
        {ALGOS.map((a) => (
          <button
            key={a.id}
            className={`tab ${algo === a.id ? "active" : ""}`}
            onClick={() => switchAlgo(a.id)}
          >
            {a.label}
          </button>
        ))}
      </div>

      <div className="card">
        {algo === "grover" && (
          <div className="field-row">
            <label>
              Number of qubits:
              <input
                type="number"
                min="1"
                max="6"
                value={groverQubits}
                onChange={(e) => setGroverQubits(e.target.value)}
              />
            </label>
            <label>
              Marked state (bitstring):
              <input
                type="text"
                value={groverMarked}
                onChange={(e) => setGroverMarked(e.target.value)}
                placeholder="e.g. 101"
              />
            </label>
          </div>
        )}

        {algo === "qft" && (
          <div className="field-row">
            <label>
              Number of qubits:
              <input
                type="number"
                min="1"
                max="6"
                value={qftQubits}
                onChange={(e) => setQftQubits(e.target.value)}
              />
            </label>
            <label>
              Input state (bitstring):
              <input
                type="text"
                value={qftInput}
                onChange={(e) => setQftInput(e.target.value)}
                placeholder="e.g. 110"
              />
            </label>
          </div>
        )}

        {algo === "qaoa" && (
          <div className="field-row">
            <label>
              Number of nodes:
              <input
                type="number"
                min="2"
                max="6"
                value={qaoaNodes}
                onChange={(e) => setQaoaNodes(e.target.value)}
              />
            </label>
            <label>
              Edges (pairs, e.g. "0,1; 1,2; 0,2"):
              <input
                type="text"
                value={qaoaEdges}
                onChange={(e) => setQaoaEdges(e.target.value)}
                style={{ minWidth: "220px" }}
              />
            </label>
          </div>
        )}

        {algo === "vqe" && (
          <div className="field-row">
            <label>
              Number of qubits:
              <input
                type="number"
                min="1"
                max="6"
                value={vqeQubits}
                onChange={(e) => setVqeQubits(e.target.value)}
              />
            </label>
          </div>
        )}

        <div style={{ marginTop: "1rem" }}>
          <button className="btn-primary" onClick={run} disabled={loading}>
            {loading ? "Running..." : "Run Algorithm"}
          </button>
        </div>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && <AlgorithmResult algo={algo} data={result} />}
    </div>
  );
}

// Renders the result, adapting to which algorithm produced it.
function AlgorithmResult({ algo, data }) {
  const r = data.result;

  return (
    <div className="card result-card">
      <h3>Results — {data.algorithm.toUpperCase()}</h3>

      {algo === "grover" && (
        <>
          <p>
            <strong>Marked state:</strong> {r.marked_state} &nbsp;|&nbsp;
            <strong> Success probability:</strong>{" "}
            {(r.success_probability * 100).toFixed(1)}%
          </p>
          <p>
            <strong>Iterations used:</strong> {r.iterations_used} &nbsp;|&nbsp;
            <strong> Classical avg lookups:</strong>{" "}
            {r.classical_comparison.classical_avg_lookups_needed} vs{" "}
            <strong>quantum:</strong>{" "}
            {r.classical_comparison.quantum_oracle_calls_needed}
          </p>
        </>
      )}

      {algo === "qft" && (
        <p>
          <strong>Input state:</strong> {r.input_state} &nbsp;|&nbsp;
          <strong> Recovered correctly:</strong>{" "}
          {(r.recovered_correctly_probability * 100).toFixed(1)}%
        </p>
      )}

      {algo === "qaoa" && (
        <>
          <p>
            <strong>Best cut found:</strong> {r.best_bitstring_found} &nbsp;|&nbsp;
            <strong> Cut value:</strong> {r.best_cut_value} /{" "}
            {r.max_possible_cut_value}
          </p>
          <p>
            <strong>Optimal γ:</strong> {r.optimal_gamma} &nbsp;|&nbsp;
            <strong> Optimal β:</strong> {r.optimal_beta} &nbsp;|&nbsp;
            <strong> Iterations:</strong> {r.iterations_run}
          </p>
          <ConvergenceChart
            history={r.convergence_history}
            valueKey="expected_cut_value"
            label="Expected Cut Value"
          />
        </>
      )}

      {algo === "vqe" && (
        <>
          <p>
            <strong>Final energy:</strong> {r.final_energy} &nbsp;|&nbsp;
            <strong> Theoretical minimum:</strong> {r.theoretical_minimum_energy}{" "}
            &nbsp;|&nbsp;
            <strong> Converged within:</strong> {r.converged_within}
          </p>
          <ConvergenceChart
            history={r.convergence_history}
            valueKey="energy"
            label="Energy"
          />
        </>
      )}

      {r.circuit_diagram_text && (
        <>
          <h4>Circuit Diagram</h4>
          <pre className="diagram">{r.circuit_diagram_text}</pre>
        </>
      )}
    </div>
  );
}

// A simple SVG line chart of the convergence history (no chart library needed).
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
    const y =
      height - pad - ((h[valueKey] - min) / range) * (height - 2 * pad);
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
        <text x={pad} y={height - 8} className="chart-axis">
          iter 1
        </text>
        <text x={width - pad - 30} y={height - 8} className="chart-axis">
          iter {history.length}
        </text>
      </svg>
    </>
  );
}
