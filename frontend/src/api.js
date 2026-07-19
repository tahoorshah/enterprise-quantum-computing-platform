// Single source of truth for talking to the backend API.
// If the backend URL ever changes (e.g. in production), it changes here only.

const BASE_URL = "http://localhost:8000";

// Generic POST helper. Returns parsed JSON, or throws an Error with a
// useful message that the UI can display.
async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    // FastAPI puts error messages in a "detail" field
    const message = data.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

// Generic GET helper.
async function getJSON(path) {
  const res = await fetch(`${BASE_URL}${path}`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

export const api = {
  // Health
  health: () => getJSON("/health"),

  // Module 1 - Quantum Circuits
  executeCircuit: (payload) => postJSON("/api/quantum/execute", payload),
  listGates: () => getJSON("/api/quantum/gates"),
  circuitHistory: () => getJSON("/api/quantum/history"),

  // Module 3 - Algorithms
  runGrover: (payload) => postJSON("/api/algorithms/grover", payload),
  runQFT: (payload) => postJSON("/api/algorithms/qft", payload),
  runQAOA: (payload) => postJSON("/api/algorithms/qaoa", payload),
  runVQE: (payload) => postJSON("/api/algorithms/vqe", payload),

  // Module 2 - Portfolio
  optimizePortfolio: (payload) => postJSON("/api/optimization/portfolio", payload),

  // Module 4 - Dashboard
  dashboardOverview: () => getJSON("/api/dashboard/overview"),
  dashboardKpis: () => getJSON("/api/dashboard/kpis"),
  dashboardHistory: () => getJSON("/api/dashboard/history"),

  // Module 5 - PQC
  pqcClassical: () => getJSON("/api/pqc/algorithms/classical"),
  pqcNist: () => getJSON("/api/pqc/algorithms/nist-pqc"),
  pqcThreatDemo: (payload) => postJSON("/api/pqc/threat-demo", payload),
  pqcInventoryScan: (payload) => postJSON("/api/pqc/inventory/scan", payload),
  pqcRiskAssessment: () => getJSON("/api/pqc/risk-assessment"),
};
