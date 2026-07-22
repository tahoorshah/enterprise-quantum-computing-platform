// Single source of truth for talking to the backend API.
//
// BASE_URL is environment-aware:
//  - Local Vite dev:      VITE_API_BASE is unset, so we default to
//                         "http://localhost:8000" (talks to uvicorn directly).
//  - Kubernetes / nginx:  the production build sets VITE_API_BASE="" (empty),
//                         so all calls use relative paths like "/api/quantum/..."
//                         which nginx reverse-proxies to the backend service.
//
// This keeps ONE codebase working in both environments - only the build-time
// env var changes.
const BASE_URL = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

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
  health: () => getJSON("/health"),

  executeCircuit: (payload) => postJSON("/api/quantum/execute", payload),
  listGates: () => getJSON("/api/quantum/gates"),
  circuitHistory: () => getJSON("/api/quantum/history"),

  runGrover: (payload) => postJSON("/api/algorithms/grover", payload),
  runQFT: (payload) => postJSON("/api/algorithms/qft", payload),
  runQAOA: (payload) => postJSON("/api/algorithms/qaoa", payload),
  runVQE: (payload) => postJSON("/api/algorithms/vqe", payload),

  optimizePortfolio: (payload) => postJSON("/api/optimization/portfolio", payload),

  dashboardOverview: () => getJSON("/api/dashboard/overview"),
  dashboardKpis: () => getJSON("/api/dashboard/kpis"),
  dashboardHistory: () => getJSON("/api/dashboard/history"),

  pqcClassical: () => getJSON("/api/pqc/algorithms/classical"),
  pqcNist: () => getJSON("/api/pqc/algorithms/nist-pqc"),
  pqcThreatDemo: (payload) => postJSON("/api/pqc/threat-demo", payload),
  pqcInventoryScan: (payload) => postJSON("/api/pqc/inventory/scan", payload),
  pqcRiskAssessment: () => getJSON("/api/pqc/risk-assessment"),
  compareFrameworks: (shots) => getJSON(`/api/frameworks/compare?shots=${shots}`),

  mlCompare: (payload) => postJSON("/api/ml/compare", payload),
  mlHistory: () => getJSON("/api/ml/history"),	
};
