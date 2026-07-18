# QFT Bank - Enterprise Quantum Computing Platform

EduQual Level 6 Enterprise Capstone Project (Code: ANPP-OP)
Diploma in AIOPS - Al Nafi International College

## Status: Scaffold created, Module 1 in progress

## Project Structure

- `backend/` — FastAPI application
  - `app/quantum/` — Module 1: Quantum Circuit Design Platform
  - `app/optimization/` — Module 2: Financial Portfolio Optimization
  - `app/algorithms/` — Module 3: Quantum Algorithm Demonstration (Grover, QFT, QAOA, VQE)
  - `app/dashboard/` — Module 4: Executive Quantum Operations Dashboard
  - `app/pqc/` — Module 5: Post-Quantum Cryptography Readiness
- `frontend/` — React dashboard (built after backend modules produce data)
- `infra/` — Terraform/OpenTofu, Kubernetes manifests, Docker configs
- `diagrams/` — All 15 mandatory architecture diagrams
- `docs/` — Installation/Deployment/User/Admin guides, reports

## Local Development

```bash
cp .env.example .env
# edit .env if needed
docker compose up -d
docker compose logs -f backend
```

Then visit: `http://localhost:8000/health`

## Quantum sanity check (run before trusting any API results)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app/quantum/sanity_check.py
```

## Deliberately NOT running yet (by design, to protect low-RAM environments)

- Kubernetes (comes after docker-compose stack is proven)
- GitLab CE self-hosted (using GitHub Actions instead)
- Keycloak / OPA (documented in diagrams, run only briefly for demo)
- Full monitoring stack (Prometheus/Grafana added in later phase)
