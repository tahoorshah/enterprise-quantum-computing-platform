import { useState } from "react";
import { api } from "../api";

// Module 5 - Post-Quantum Cryptography Readiness Platform.
// Tabbed: (1) crypto threat reference, (2) NIST PQC standards,
// (3) live QPE threat demo, (4) simulated inventory scan + risk.

const TABS = [
  { id: "threat", label: "Crypto Threats" },
  { id: "nist", label: "NIST PQC Standards" },
  { id: "qpe", label: "Quantum Threat Demo" },
  { id: "inventory", label: "Inventory & Risk" },
];

export default function PQCReadiness() {
  const [tab, setTab] = useState("threat");

  return (
    <div>
      <h2>Post-Quantum Cryptography Readiness</h2>
      <p className="subtitle">
        Assess quantum threats to current cryptography and plan migration to
        NIST post-quantum standards.
      </p>

      <div className="tab-row">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "threat" && <ThreatReference />}
      {tab === "nist" && <NistStandards />}
      {tab === "qpe" && <QpeDemo />}
      {tab === "inventory" && <InventoryScan />}
    </div>
  );
}

// --- Tab 1: classical algorithms and their quantum vulnerability ---
function ThreatReference() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = async () => {
    setError(null);
    try {
      setData(await api.pqcClassical());
    } catch (e) {
      setError(e.message);
    }
  };

  // Load immediately
  useState(() => {
    load();
  });

  return (
    <div className="card">
      <h3>Current Cryptography — Quantum Vulnerability</h3>
      {error && <div className="error-box">Error: {error}</div>}
      {!data && (
        <button className="btn-secondary" onClick={load}>
          Load
        </button>
      )}
      {data &&
        Object.entries(data).map(([name, info]) => (
          <div key={name} className="crypto-item">
            <div className="crypto-header">
              <strong>{name}</strong>
              <span
                className={`risk-badge ${
                  (info.risk_level || "").includes("CRITICAL")
                    ? "critical"
                    : (info.risk_level || "").includes("MODERATE")
                    ? "moderate"
                    : "low"
                }`}
              >
                {info.risk_level}
              </span>
            </div>
            <p className="muted">{info.type}</p>
            <p>{info.quantum_threat}</p>
          </div>
        ))}
    </div>
  );
}

// --- Tab 2: NIST PQC replacement standards ---
function NistStandards() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  const load = async () => {
    setError(null);
    try {
      setData(await api.pqcNist());
    } catch (e) {
      setError(e.message);
    }
  };
  useState(() => {
    load();
  });

  return (
    <div className="card">
      <h3>NIST Post-Quantum Cryptography Standards</h3>
      {error && <div className="error-box">Error: {error}</div>}
      {!data && (
        <button className="btn-secondary" onClick={load}>
          Load
        </button>
      )}
      {data &&
        Object.entries(data).map(([name, info]) => (
          <div key={name} className="crypto-item">
            <div className="crypto-header">
              <strong>{name}</strong>
              {info.fips_standard && (
                <span className="fips-badge">{info.fips_standard}</span>
              )}
            </div>
            <p>{info.purpose}</p>
            <p className="muted">
              {info.hardness_assumption}
              {info.based_on ? ` — based on ${info.based_on}` : ""}
            </p>
          </div>
        ))}
    </div>
  );
}

// --- Tab 3: live Quantum Phase Estimation threat demo ---
function QpeDemo() {
  const [theta, setTheta] = useState(0.375);
  const [qubits, setQubits] = useState(3);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const data = await api.pqcThreatDemo({
        theta: Number(theta),
        num_counting_qubits: Number(qubits),
        shots: 1024,
      });
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h3>Quantum Phase Estimation — The Threat Behind Shor's Algorithm</h3>
      <p className="muted" style={{ marginBottom: "1rem" }}>
        QPE is the subroutine Shor's algorithm uses to break RSA/ECC. This runs
        genuine QPE (reusing the platform's own QFT) to recover a known phase.
      </p>
      <div className="field-row">
        <label>
          Phase to estimate (0 to 1):
          <input
            type="number"
            min="0"
            max="0.99"
            step="0.001"
            value={theta}
            onChange={(e) => setTheta(e.target.value)}
          />
        </label>
        <label>
          Counting qubits (precision):
          <input
            type="number"
            min="1"
            max="8"
            value={qubits}
            onChange={(e) => setQubits(e.target.value)}
          />
        </label>
      </div>
      <div style={{ marginTop: "1rem" }}>
        <button className="btn-primary" onClick={run} disabled={loading}>
          {loading ? "Running..." : "Run QPE Demo"}
        </button>
      </div>

      {error && <div className="error-box">Error: {error}</div>}

      {result && (
        <div style={{ marginTop: "1.2rem" }}>
          <p>
            <strong>True phase:</strong> {result.true_theta} &nbsp;|&nbsp;
            <strong> Estimated:</strong> {result.most_likely_estimate}{" "}
            &nbsp;|&nbsp;
            <strong> Error:</strong> {result.estimation_error}
          </p>
          <p className="muted">Precision: {result.precision}</p>
          <h4>Circuit Diagram</h4>
          <pre className="diagram">{result.circuit_diagram_text}</pre>
        </div>
      )}
    </div>
  );
}

// --- Tab 4: simulated cryptographic inventory scan + org risk ---
function InventoryScan() {
  const [inventory, setInventory] = useState(null);
  const [risk, setRisk] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const scan = async () => {
    setLoading(true);
    setError(null);
    try {
      const inv = await api.pqcInventoryScan({ seed: 42 });
      setInventory(inv.inventory);
      const r = await api.pqcRiskAssessment();
      setRisk(r);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="card">
        <h3>Simulated Cryptographic Inventory Scan</h3>
        <p className="muted" style={{ marginBottom: "1rem" }}>
          Scans QFT Bank's (fictional) systems and scores each for
          post-quantum migration urgency.
        </p>
        <button className="btn-primary" onClick={scan} disabled={loading}>
          {loading ? "Scanning..." : "Run Inventory Scan"}
        </button>
        {error && <div className="error-box">Error: {error}</div>}
      </div>

      {risk && (
        <div className="card">
          <h3>Organizational Risk Assessment</h3>
          <div className="kpi-grid">
            <div className="kpi-card">
              <div className="kpi-value">{risk.total_systems_scanned}</div>
              <div className="kpi-label">Systems Scanned</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">{risk.average_quantum_risk_score}</div>
              <div className="kpi-label">Avg Risk Score</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">
                {risk.overall_organizational_risk_rating}
              </div>
              <div className="kpi-label">Overall Rating</div>
            </div>
            <div className="kpi-card">
              <div className="kpi-value">
                {risk.systems_requiring_immediate_action?.length ?? 0}
              </div>
              <div className="kpi-label">Immediate Action</div>
            </div>
          </div>
        </div>
      )}

      {inventory && (
        <div className="card">
          <h3>System Inventory</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>System</th>
                <th>Current Algorithm</th>
                <th>Risk</th>
                <th>Urgency</th>
                <th>Recommended Replacement</th>
              </tr>
            </thead>
            <tbody>
              {inventory.map((s) => (
                <tr key={s.system_id}>
                  <td>{s.system_name}</td>
                  <td>{s.current_algorithm}</td>
                  <td>{s.quantum_risk_score}</td>
                  <td>
                    <span
                      className={`risk-badge ${
                        s.migration_urgency === "IMMEDIATE"
                          ? "critical"
                          : s.migration_urgency === "HIGH"
                          ? "moderate"
                          : "low"
                      }`}
                    >
                      {s.migration_urgency}
                    </span>
                  </td>
                  <td className="muted">{s.recommended_replacement}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
