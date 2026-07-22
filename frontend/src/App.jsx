import { useState, useEffect } from "react";
import { api } from "./api";
import CircuitDesigner from "./components/CircuitDesigner";
import Algorithms from "./components/Algorithms";
import Portfolio from "./components/Portfolio";
import Dashboard from "./components/Dashboard";
import PQCReadiness from "./components/PQCReadiness";
import "./App.css";
import Frameworks from "./components/Frameworks";
import MLComparison from "./components/MLComparison";

// The module screens for the platform's seven modules.
const MODULES = [
  { id: "circuit", label: "Circuit Designer", subtitle: "Build & run circuits" },
  { id: "algorithms", label: "Quantum Algorithms", subtitle: "Grover, QFT, QAOA, VQE" },
  { id: "portfolio", label: "Portfolio Optimization", subtitle: "Quantum finance" },
  { id: "dashboard", label: "Executive Dashboard", subtitle: "KPIs & activity" },
  { id: "pqc", label: "PQC Readiness", subtitle: "Crypto migration" },
  { id: "frameworks", label: "Framework Comparison", subtitle: "Qiskit / PennyLane / Cirq" },	
  { id: "ml", label: "ML vs Quantum", subtitle: "Classical ML comparison" },
];

function Placeholder({ name }) {
  return (
    <div>
      <h2>{name}</h2>
      <p className="subtitle">This module's UI is coming next.</p>
    </div>
  );
}

export default function App() {
  const [active, setActive] = useState("circuit");
  const [backend, setBackend] = useState(null);

  // On load, ping the backend health endpoint so we can show a status light
  useEffect(() => {
    api
      .health()
      .then((d) => setBackend(d))
      .catch(() => setBackend({ status: "unreachable" }));
  }, []);

  const renderModule = () => {
    switch (active) {
      case "circuit":
        return <CircuitDesigner />;
      case "algorithms":
        return <Algorithms />;
      case "portfolio":
        return <Portfolio />;
      case "dashboard":
        return <Dashboard />;
      case "pqc":
        return <PQCReadiness />;
      case "frameworks":
        return <Frameworks />;	
      case "ml":
        return <MLComparison />;
      default:
        return null;
    }
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-title">QFT Bank</div>
          <div className="brand-sub">Quantum Computing Platform</div>
        </div>

        <nav>
          {MODULES.map((m) => (
            <button
              key={m.id}
              className={`nav-item ${active === m.id ? "active" : ""}`}
              onClick={() => setActive(m.id)}
            >
              <span className="nav-label">{m.label}</span>
              <span className="nav-sub">{m.subtitle}</span>
            </button>
          ))}
        </nav>

        <div className="backend-status">
          <span
            className={`status-dot ${
              backend?.status === "healthy" ? "ok" : "bad"
            }`}
          />
          {backend
            ? backend.status === "healthy"
              ? `Backend: ${backend.storage_backend}`
              : "Backend unreachable"
            : "Checking backend..."}
        </div>
      </aside>

      <main className="content">{renderModule()}</main>
    </div>
  );
}
