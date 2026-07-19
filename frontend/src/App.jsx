import { useState, useEffect } from "react";
import { api } from "./api";
import CircuitDesigner from "./components/CircuitDesigner";
import Algorithms from "./components/Algorithms";
import Portfolio from "./components/Portfolio";
import "./App.css";

// The five module screens. For now only Circuit Designer is built;
// the others show a placeholder until we add them one at a time.
const MODULES = [
  { id: "circuit", label: "Circuit Designer", subtitle: "Module 1" },
  { id: "algorithms", label: "Quantum Algorithms", subtitle: "Module 3" },
  { id: "portfolio", label: "Portfolio Optimization", subtitle: "Module 2" },
  { id: "dashboard", label: "Executive Dashboard", subtitle: "Module 4" },
  { id: "pqc", label: "PQC Readiness", subtitle: "Module 5" },
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
        return <Placeholder name="Executive Dashboard" />;
      case "pqc":
        return <Placeholder name="PQC Readiness" />;
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
