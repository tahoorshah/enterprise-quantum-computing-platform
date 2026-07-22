# QFT Bank — Enterprise Quantum Computing Platform

**EduQual Level 6 Enterprise Capstone Project** (Code: ANPP-OP)
Diploma in AIOPS — Al Nafi International College

A proof-of-concept enterprise quantum computing platform for a fictional multinational bank
("Quantum Financial Technologies", QFT Bank). It demonstrates quantum circuit design, quantum
financial portfolio optimization, a suite of quantum algorithms, an executive operations
dashboard, and post-quantum cryptography (PQC) readiness — all running on open-source quantum
simulators on classical hardware (no physical quantum computer required).

> **Assessment context:** QFT Bank is a fictional organisation for assessment purposes. All
> financial datasets are simulated and reproducible. No real banking systems, market feeds, or
> financial transactions are involved.

---

## Table of Contents

1. [Project Objectives](#1-project-objectives)
2. [Architecture Overview](#2-architecture-overview)
3. [Functional Modules](#3-functional-modules)
4. [Technology Stack](#4-technology-stack)
5. [Repository Structure](#5-repository-structure)
6. [Quick Start (Docker Compose)](#6-quick-start-docker-compose)
7. [Alternative Run Paths (Kubernetes, Terraform, Local Dev)](#7-alternative-run-paths)
8. [Persistence Model](#8-persistence-model)
9. [CI/CD and DevSecOps](#9-cicd-and-devsecops)
10. [Monitoring and Observability](#10-monitoring-and-observability)
11. [Testing](#11-testing)
12. [Key Quantum-Computing Design Decisions](#12-key-quantum-computing-design-decisions)
13. [Assumptions and Limitations](#13-assumptions-and-limitations)
14. [Standards and Frameworks Considered](#14-standards-and-frameworks-considered)
15. [Recommendations for Future Improvements](#15-recommendations-for-future-improvements)
16. [Documentation Index](#16-documentation-index)

---

## 1. Project Objectives

The platform was built to design, develop, deploy, and demonstrate an enterprise quantum computing
solution addressing four business needs QFT Bank's Quantum Innovation Programme identified:

- **Portfolio optimization** — map asset selection onto a quantum-solvable problem (QAOA) and
  benchmark it honestly against an exact classical baseline.
- **Quantum algorithm capability** — demonstrate the enterprise-relevant algorithms (Grover's
  search, Quantum Fourier Transform, QAOA, VQE) with genuine simulation, not fabricated output.
- **Executive decision support** — aggregate quantum experiment activity into KPIs and a research
  progress report for non-technical leadership.
- **Post-quantum cryptography readiness** — assess the future quantum threat to current
  public-key cryptography and present a NIST-aligned migration path.

The solution is delivered as a containerised, orchestrated, monitored, and CI/CD-driven platform
to reflect how such a capability would sit inside a real enterprise environment.

## 2. Architecture Overview

The platform is a three-tier web application wrapped in enterprise operations tooling:

- **Presentation tier** — a React single-page application (six module UIs), served in production
  by Nginx.
- **Application tier** — a FastAPI backend exposing the six modules; quantum work runs on the
  Qiskit Aer simulator (with PennyLane and Cirq demonstrated for framework independence).
- **Data tier** — PostgreSQL for execution-history persistence, with Redis provisioned for caching.

Around these tiers: Docker containers, Kubernetes orchestration (Minikube), Terraform
infrastructure-as-code, a Jenkins DevSecOps pipeline, and Prometheus + Grafana monitoring.

A defining property of the network design is a **single external entry point**: only the frontend
service is exposed (NodePort). Nginx serves the React app and reverse-proxies `/api` calls to the
backend over the in-cluster network. The backend, PostgreSQL, and Redis are `ClusterIP`-only and
are never reachable directly from outside the cluster.

The 15 mandatory architecture diagrams (enterprise architecture, network flow, data-flow levels 0
and 1, sequence, ERD, and more) are in [`diagrams/`](diagrams/) as Mermaid source and exported PNGs.

## 3. Functional Modules

| # | Module | Package | What it does |
|---|--------|---------|--------------|
| 1 | Quantum Circuit Design | `app/quantum/` | Build circuits from 13 supported gates, validate before execution, run on Aer, return counts + circuit diagram + probability distribution, persist history. |
| 2 | Financial Portfolio Optimization | `app/optimization/` | Simulated market data → QUBO → Ising Hamiltonian → QAOA (real COBYLA optimization) vs an exact classical brute-force optimum, with portfolio risk/return metrics. |
| 3 | Quantum Algorithm Demonstration | `app/algorithms/` | Grover's search, Quantum Fourier Transform, QAOA (Max-Cut), and VQE — constructed at gate level, executed on Aer, compared against classical approaches. |
| 4 | Executive Operations Dashboard | `app/dashboard/` | Aggregates Modules 1–3 into KPIs, success rates, resource utilization, merged history, and a research progress report. Runs no new quantum computation. |
| 5 | Post-Quantum Cryptography Readiness | `app/pqc/` | Classical-crypto vulnerability reference, a conceptual quantum-threat demo (reuses Module 3's QFT for phase estimation), the NIST PQC standards catalogue (ML-KEM, ML-DSA, SLH-DSA, HQC), a simulated cryptographic inventory scan with risk scoring, and a 5-phase migration plan. |
| 6 | Multi-Framework Demonstration | `app/frameworks/` | Constructs the same Bell state in Qiskit, PennyLane, and Cirq to show framework-independent correctness; satisfies the spec's PennyLane and Cirq requirements. |

## 4. Technology Stack

**Language & core:** Python, FastAPI, React (Vite), PostgreSQL, Redis.
**Quantum:** Qiskit (primary, with Aer simulator), PennyLane, Cirq.
**Scientific:** NumPy, SciPy (COBYLA optimizer).
**Infrastructure:** Docker, Kubernetes (Minikube), Terraform (Kubernetes provider).
**CI/CD & security:** Jenkins (7-stage DevSecOps pipeline), Bandit (SAST), pip-audit (dependency
scan), Trivy (container scan).
**Monitoring:** Prometheus, Grafana (via `prometheus-fastapi-instrumentator`).
**Diagrams:** Mermaid (diagram-as-code, exported to PNG).

Verified working versions on the development machine (Kali Linux, Python 3.13): `qiskit==2.5.0`,
`qiskit-aer==0.17.2`, `pennylane==0.45.1`, `cirq==1.7.0`, `numpy==2.5.1`,
`psycopg2-binary==2.9.10`, `prometheus-fastapi-instrumentator==8.0.2`.

## 5. Repository Structure

```
enterprise-quantum-computing-platform/
├── backend/
│   ├── app/
│   │   ├── quantum/        # Module 1 — circuit design
│   │   ├── optimization/   # Module 2 — portfolio optimization
│   │   ├── algorithms/     # Module 3 — Grover / QFT / QAOA / VQE
│   │   ├── dashboard/      # Module 4 — executive dashboard + shared metrics
│   │   ├── pqc/            # Module 5 — post-quantum cryptography readiness
│   │   ├── frameworks/     # Module 6 — Qiskit / PennyLane / Cirq comparison
│   │   └── database/       # persistence layer (PostgreSQL + in-memory fallback)
│   ├── tests/              # pytest suite (30 tests)
│   └── pytest.ini
├── frontend/               # React SPA (6 module UIs) + Nginx production config
├── infra/
│   ├── k8s/                # Kubernetes manifests (Minikube)
│   └── terraform/          # Terraform IaC (Kubernetes provider)
├── diagrams/               # 15 mandatory architecture diagrams (Mermaid + PNG)
├── docs/                   # Installation / Deployment / User / Admin guides, reports
├── Jenkinsfile             # 7-stage DevSecOps pipeline
└── docker-compose.yml      # local full-stack quick start
```

## 6. Quick Start (Docker Compose)

The fastest way to run the full stack locally:

```bash
cp .env.example .env        # adjust values if needed
docker compose up -d
docker compose logs -f backend
```

Check the backend is healthy:

```bash
curl http://localhost:8000/health
```

The `/health` response includes a `storage_backend` field reporting whether persistence is running
on PostgreSQL or the in-memory fallback (see [Persistence Model](#8-persistence-model)).

Interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs`.

### Quantum sanity check

Before trusting any API results, a standalone sanity check verifies the simulator produces correct
quantum behaviour (e.g. a Bell state yields a genuine ~50/50 distribution):

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/quantum/sanity_check.py
```

## 7. Alternative Run Paths

**Kubernetes (Minikube).** Manifests in `infra/k8s/` deploy PostgreSQL (with a PVC), Redis, the
backend, the Nginx-served frontend (NodePort 30080), Prometheus, and Grafana. All services except
the frontend and monitoring UIs are `ClusterIP`-only. See the Deployment Guide for the image
build/load procedure (Minikube requires images loaded into its own Docker daemon).

**Terraform (IaC).** `infra/terraform/` provisions the full platform declaratively via the
Kubernetes provider into a dedicated `qft-terraform` namespace (NodePort 30081), deliberately
parallel to the `kubectl`-managed `default` namespace so the two deployments don't interfere.
`terraform state` files are git-ignored (they can contain sensitive values).

**Local development (no containers).** Run the backend with Uvicorn (`uvicorn app.main:app
--reload` from `backend/`) and the frontend with Vite (`npm run dev` from `frontend/`). The
frontend's API base is environment-aware (`VITE_API_BASE`), so the same codebase works in local
dev and in Kubernetes.

## 8. Persistence Model

Execution history uses a **single unified `executions` table** with a `module` discriminator column
and a JSON result payload, rather than four near-identical per-module tables. This simplifies the
dashboard's cross-module queries and accommodates result shapes that differ between algorithms.

Persistence is designed for **graceful degradation**. At startup the platform tests the database
connection: if PostgreSQL is reachable, history is persisted there; if not, it transparently falls
back to in-memory storage rather than crashing. All three history-recording modules — Module 1
(circuits), Module 2 (portfolio), and Module 3 (algorithms) — route through the same persistence
layer, so the behaviour is consistent across the platform. The active backend is always reported by
`/health`.

This is intentional resilience: in a Kubernetes deployment, pods start in parallel, so the backend
may briefly start before PostgreSQL is ready. The fallback keeps the platform functional; a
`kubectl rollout restart deployment/backend` reconnects it once the database is up. In production,
an init-container or readiness gate would enforce ordering.

## 9. CI/CD and DevSecOps

A **7-stage Jenkins pipeline** (`Jenkinsfile`) runs security scanning throughout, not just at the
end:

1. **Checkout**
2. **Backend build + test** — 30 pytest tests
3. **SAST** — Bandit static analysis
4. **Dependency scan** — pip-audit
5. **Frontend build**
6. **Docker build**
7. **Container scan** — Trivy

Three independent security layers (SAST, dependency, container) reflect defence-in-depth. Jenkins
was chosen over GitLab CE for a lighter resource footprint on the development hardware; both are
listed in the approved stack.

## 10. Monitoring and Observability

The backend is instrumented with `prometheus-fastapi-instrumentator`, exposing a `/metrics`
endpoint. Prometheus scrapes it (job `qft-backend`); Grafana is pre-wired with the Prometheus
datasource and graphs request-rate metrics such as `rate(http_requests_total[1m])`. In the
Kubernetes deployment, Prometheus and Grafana are reachable on NodePorts 30090 and 30300.

## 11. Testing

The pytest suite contains **30 tests, all passing**:

- `test_quantum_circuits.py` — 9 tests (Module 1)
- `test_algorithms.py` — 8 tests (Module 3)
- `test_portfolio_and_pqc.py` — 12 tests (Modules 2 and 5)
- `test_health.py` — 1 test

Run them from `backend/`:

```bash
python3 -m pytest -q
```

The suite includes a **regression test for the QUBO→Ising conversion** (`test_qubo_to_ising_
conversion_is_consistent`), which guards a real mathematical bug that was found and fixed during
development (see [Key Design Decisions](#12-key-quantum-computing-design-decisions)). One
deprecation warning is emitted by FastAPI's test client (a Starlette/httpx notice); it does not
affect correctness.

## 12. Key Quantum-Computing Design Decisions

- **Genuine simulation, not fabricated output.** All quantum results come from real Qiskit Aer
  execution. QAOA and VQE convergence data is produced by actual per-iteration circuit execution
  under a COBYLA optimizer — there are no hard-coded or synthetic convergence curves.
- **QUBO→Ising bug caught and regression-tested.** Portfolio selection is mapped to a QUBO, then to
  an Ising Hamiltonian for QAOA. An error in that conversion was detected by exhaustively checking
  all bitstrings against the classical optimum, fixed, and locked behind a regression test.
- **Honest classical baseline.** The classical comparison is exact brute force, feasible because
  asset counts are capped at 8. This yields a verifiable classical-vs-quantum comparison rather
  than an unfalsifiable claim of quantum advantage. For these small problems brute force is often
  faster in wall-clock time; QAOA's advantage is asymptotic, which the platform states plainly.
- **Gate-level algorithm construction.** Grover, QFT, QAOA, and VQE are built gate by gate rather
  than via high-level pre-built routines, so every gate can be explained.
- **Framework independence.** The same Bell state is reproduced in Qiskit, PennyLane, and Cirq,
  demonstrating the results are correct and not an artefact of one framework.

## 13. Assumptions and Limitations

- **Simulated data only.** All market data is synthetic and seeded for reproducibility. No live
  market feeds or real transactions.
- **Simulator, not quantum hardware.** Quantum work runs on classical simulators (Qiskit Aer,
  PennyLane `default.qubit`, Cirq simulator), as the assessment permits and expects.
- **Small problem sizes.** Portfolio optimization caps assets at 8 so the exact brute-force
  baseline remains feasible and QAOA runtimes stay reasonable.
- **Single-node Kubernetes.** Deployment targets Minikube, which is genuine CNCF-certified
  Kubernetes but single-node; a production deployment would use a multi-node managed cluster.
- **Scope boundary — production enhancements not built.** Several items in the approved technology
  stack were deliberately *not* implemented because they have no named deliverable in the project
  scope and half-building them would add risk without demonstrating quantum competency. These are
  documented as production enhancements rather than presented as complete: Keycloak (IAM), Open
  Policy Agent (policy enforcement), Wazuh (host security monitoring), Loki/OpenTelemetry (log
  aggregation/tracing), and a scikit-learn machine-learning component. The security posture that
  *is* implemented consists of the three DevSecOps scanning layers (Bandit, pip-audit, Trivy).

## 14. Standards and Frameworks Considered

The design reflects consideration of: ISO/IEC 23837 (quantum computing concepts and vocabulary),
NIST Post-Quantum Cryptography standards, NIST Cybersecurity Framework 2.0, ISO/IEC 27001, 27017,
and 27018, COBIT 2019, ITIL 4, the OWASP Top 10, and the CIS Critical Security Controls. How each
applies to enterprise quantum adoption, financial-systems architecture, cryptographic governance,
and long-term cybersecurity planning is detailed in the standards write-up under [`docs/`](docs/).

## 15. Recommendations for Future Improvements

- Enforce database readiness in Kubernetes via an init-container or readiness gate, removing
  reliance on the in-memory fallback during startup.
- Implement the documented production-enhancement stack (Keycloak, OPA, Wazuh, Loki/OpenTelemetry)
  for a full enterprise security and observability posture.
- Add a machine-learning component (scikit-learn) for, e.g., predicting QAOA parameter starting
  points to reduce optimizer iterations.
- Extend portfolio optimization beyond brute-force-verifiable sizes using approximate classical
  solvers as the baseline, enabling larger, more realistic asset universes.
- Provision a multi-node managed Kubernetes cluster (EKS/GKE) via Terraform for true production
  deployment, with the same IaC provisioning the cluster itself.

## 16. Documentation Index

Full documentation lives in [`docs/`](docs/):

- **Installation Guide** — prerequisites and environment setup.
- **Deployment Guide** — Docker Compose, Kubernetes, and Terraform deployment procedures.
- **User Guide** — using each of the six modules through the web interface.
- **Administrator Guide** — operations, persistence, monitoring, and troubleshooting.
- **API Documentation** — endpoint reference (also available live at `/docs`).
- **Reports** — quantum experiment report, portfolio optimization report, performance testing report.

---

*This project was developed for the Al Nafi International College Diploma in AIOPS EduQual Level 6
Enterprise Capstone (ANPP-OP). QFT Bank is fictional; all data is simulated.*
