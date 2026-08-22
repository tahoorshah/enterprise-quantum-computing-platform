const BASE_URL = import.meta.env.VITE_API_BASE ?? "http://localhost:8000";

let authToken = sessionStorage.getItem("qft_token") || null;

function setToken(token) {
  authToken = token;
  if (token) sessionStorage.setItem("qft_token", token);
  else sessionStorage.removeItem("qft_token");
}

function getToken() {
  return authToken;
}

function authHeaders() {
  return authToken ? { Authorization: `Bearer ${authToken}` } : {};
}

function handleUnauthorized() {
  setToken(null);
  window.dispatchEvent(new Event("qft-unauthorized"));
}

async function postJSON(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...authHeaders() },
    body: JSON.stringify(body),
  });
  if (res.status === 401) handleUnauthorized();
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

async function getJSON(path) {
  const res = await fetch(`${BASE_URL}${path}`, { headers: { ...authHeaders() } });
  if (res.status === 401) handleUnauthorized();
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  return data;
}

async function login(username, password) {
  const body = new URLSearchParams({ username, password });
  const res = await fetch(`${BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = data.detail || `Login failed (${res.status})`;
    throw new Error(typeof message === "string" ? message : JSON.stringify(message));
  }
  setToken(data.access_token);
  return data;
}

function logout() {
  setToken(null);
}

export const api = {
  health: () => getJSON("/health"),
  login,
  logout,
  getToken,
  isAuthenticated: () => Boolean(authToken),

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

  marketAnalytics: (numAssets, seed = 42) =>
    getJSON(`/api/analytics/market/${numAssets}?seed=${seed}`),
  marketChartPng: (numAssets, seed = 42) =>
    getJSON(`/api/analytics/market/${numAssets}/chart?seed=${seed}`),
  marketChartInteractive: (numAssets, seed = 42) =>
    getJSON(`/api/analytics/market/${numAssets}/interactive?seed=${seed}`),

  mlCompare: (payload) => postJSON("/api/ml/compare", payload),
  mlHistory: () => getJSON("/api/ml/history"),
};
