# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

QFT Bank — a proof-of-concept enterprise quantum computing platform for a fictional bank, built as
an EduQual Level 6 capstone. FastAPI backend + React (Vite) frontend, quantum work runs on the
Qiskit Aer simulator (PennyLane and Cirq used for framework-independence demos), PostgreSQL for
persistence with an automatic in-memory fallback. See `README.md` for the full writeup (objectives,
standards alignment, design-decision rationale) — it is unusually detailed and worth reading before
making architectural changes.

## Commands

### Backend (from `backend/`)

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload          # run locally, http://localhost:8000, docs at /docs
python3 -m pytest -q                   # run full suite (76 tests)
python3 -m pytest tests/test_algorithms.py -q          # single file
python3 -m pytest tests/test_algorithms.py::TestGrover::test_x -q   # single test
python app/quantum/sanity_check.py     # standalone check that the simulator gives correct quantum behavior (e.g. Bell state ~50/50)
```

Test config is in `pytest.ini` (`testpaths = tests`, verbose + short tracebacks by default). Tests
run against an in-memory SQLite DB (see `tests/conftest.py`) and bypass JWT auth for every module
except `test_auth.py`, via a `get_current_user` dependency override.

### Frontend (from `frontend/`)

```bash
npm install
npm run dev        # Vite dev server
npm run build
npm run lint        # ESLint
npm run preview
```

### Full stack (Docker Compose, from repo root)

```bash
cp .env.example .env
docker compose up -d
curl http://localhost:8000/health   # check storage_backend: postgres vs in-memory
```

## Architecture

**Module = vertical slice.** Each of the six functional modules is its own package under
`backend/app/<module>/`, each with the same internal shape: `router.py` (FastAPI endpoints),
`schemas.py` (Pydantic models), a domain file (e.g. `circuit_builder.py`, `qaoa_portfolio.py`), and
usually `history.py`. All routers are wired into `app/main.py` under `/api/<module>` and every one
(except `/api/auth`) is protected by `Depends(get_current_user)` at the `include_router` level, not
per-endpoint.

- `app/quantum/` — Module 1: circuit design, 13 gates, runs on Aer.
- `app/optimization/` — Module 2: portfolio optimization (QUBO → Ising → QAOA vs. exact brute-force classical baseline, capped at 8 assets so brute force stays feasible).
- `app/algorithms/` — Module 3: Grover, QFT, QAOA (Max-Cut), VQE, built gate-by-gate (not high-level library routines) so every gate is explainable.
- `app/dashboard/` — Module 4: read-only aggregation of Modules 1–3 into KPIs; runs no new quantum computation itself.
- `app/pqc/` — Module 5: PQC readiness (crypto vulnerability reference, NIST PQC catalogue, simulated crypto inventory scan, migration plan); its quantum-threat demo reuses Module 3's QFT.
- `app/frameworks/` — Module 6: same Bell state built in Qiskit, PennyLane, and Cirq to prove framework-independent correctness.
- `app/governance/` — accountability model + 16-entry risk register; explicitly documents that role separation is a model, not an enforced control, since this POC is operated by one person.
- `app/ml/`, `app/analytics/` — later additions: scikit-learn asset-selection comparison and Plotly-based market analytics, following the same router/schemas/history shape.
- `app/auth/` — JWT auth (`security.py`), real `users` table seeded with two demo accounts (`analyst`/`admin`). `context.py` stashes the current username per-request so the persistence layer can attribute saved executions.
- `app/database/` — the persistence layer all modules route through.

**Persistence: graceful degradation, not a hard dependency.** `database/connection.py::init_db()`
tries PostgreSQL at startup and never raises; if the DB is unreachable it falls back to in-memory
storage and the app keeps running. `DATABASE_AVAILABLE` is the global flag every layer checks —
`auth/security.py` mirrors the same fallback (seed users work even without a DB), and `/health`
reports `status: degraded` + the active `storage_backend` rather than silently swallowing it. This
is deliberate: in Kubernetes, pods start in parallel and the backend may come up before Postgres is
ready.

**Execution history is unified, not per-module.** All history writers (`quantum/history.py`,
`algorithms/history.py`, `optimization/history.py`, `ml/history.py`) delegate to
`database/persistence.py`, which stores everything in one `executions` table keyed by a `module`
discriminator with a JSON result payload — this is what lets the dashboard do cross-module queries
without four separate schemas. When adding a new module with history, follow this same
delegate-to-`persistence`-with-a-`_MODULE`-constant pattern rather than inventing a new storage
path.

**Frontend mirrors the backend module boundary.** Each `frontend/src/components/*.jsx` corresponds
1:1 to a backend module (`CircuitDesigner.jsx` ↔ `app/quantum`, `Portfolio.jsx` ↔
`app/optimization`, etc.). All API calls go through `frontend/src/api.js`, which reads
`VITE_API_BASE` (falls back to `http://localhost:8000`) so the same build works unmodified across
local dev, Docker Compose, and Kubernetes. It stores the JWT in `sessionStorage` and dispatches a
`qft-unauthorized` window event on any 401 so `App.jsx` can react without prop-drilling auth state
through every component.

**Network boundary.** Only the frontend is ever exposed externally (Nginx, NodePort in k8s); it
reverse-proxies `/api` to the backend. Backend, Postgres, and Redis are `ClusterIP`-only in
`infra/k8s/`. `CORS_ORIGINS` (comma-separated) controls allowed origins — no wildcard, since
`allow_credentials=True` requires explicit origins.

**Quantum correctness is enforced by tests, not assumed.** There's a regression test
(`test_qubo_to_ising_conversion_is_consistent`) guarding a real QUBO→Ising bug found during
development by exhaustively checking bitstrings against the classical optimum — if you touch
`app/optimization/qaoa_portfolio.py`, that test is the tripwire. More generally: all quantum results
must come from real Aer/PennyLane/Cirq execution, never hard-coded or synthetic output — this is a
stated project invariant, not just a style preference.

## Other places to look

- `infra/k8s/` — Kubernetes manifests (Minikube); `infra/terraform/` provisions the same stack via
  the Kubernetes provider into a separate `qft-terraform` namespace so it doesn't collide with
  `kubectl`-managed resources.
- `infra/policy/kubernetes.rego` — OPA/Conftest policy gate that validates every manifest as a CI
  build gate (not advisory) before the Docker build stage.
- `Jenkinsfile` — 8-stage pipeline: checkout → backend build/test → Bandit (SAST) → pip-audit → frontend build → OPA policy check → Docker build → Trivy (container scan).
- `docs/SCOPE_DECISIONS.md` — what was deliberately not built (Keycloak, OpenTelemetry, Wazuh,
  GitLab CE) and why, plus the known Promtail log-discovery issue in the Minikube environment.
- `docs/TESTING_COVERAGE.md` — maps test files to mandatory coverage areas and states explicitly
  what is NOT covered by automated tests.
