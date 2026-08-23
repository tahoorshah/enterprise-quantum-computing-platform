# Testing Coverage Map

**Purpose:** the rejection letter states that "the presentation does not
sufficiently establish the coverage represented by the reported test
results" and asks for explicit evidence that testing covers the mandatory
quantum modules, optimisation logic, application services, persistence,
security controls, failure behaviour, deployment, and integration. This
document is that evidence: it maps every test file to what it actually
covers, and states plainly what is NOT covered rather than implying
completeness.

**Current status:** 76/76 tests passing (`pytest -v` from `backend/`).

---

## 1. Coverage by mandatory area

| Mandatory area (per rejection letter) | Covered by | What is actually tested |
|---|---|---|
| **Quantum modules** | `test_quantum_circuits.py` (9), `test_algorithms.py` (10) | Circuit construction and validation (gate rejection, qubit range checks), Bell-state entanglement correctness, Grover's search finds the marked state, QFT round-trip recovers input, QAOA finds the exact Max-Cut optimum, VQE converges near the theoretical minimum energy, and every module's REST endpoint (200 and error-path responses) |
| **Cross-framework quantum validation** | `test_frameworks.py` (13) | Qiskit/PennyLane/Cirq statistically agree with theory and each other (total variation distance), the comparison can actually detect disagreement (not just "always passes"), forbidden entangled outcomes never appear, and results are exactly reproducible under a fixed seed |
| **Optimisation logic** | `test_portfolio_and_pqc.py` (subset of 26) | QUBO-to-Ising conversion correctness, brute-force respects the cardinality constraint, QAOA matches the classical optimum, repeated-evaluation trial counts and rates are internally consistent, cardinality constraint is explicitly checked on both classical and quantum solutions, brute force is never beaten by any QAOA trial (it is exact by construction) |
| **Application services (API layer)** | Endpoint tests across every `test_*.py` file | Every router has at least one 200-path and one 4xx-path test (422 validation errors, 404 not-found, 401 unauthorized) |
| **Persistence** | `test_auth.py` (6, via the DB-backed user store), integration exercised manually via `kubectl exec` against PostgreSQL | Login succeeds/fails correctly against a real database-backed `users` table (not mocked); the `execution_runs` / `execution_results` schema and actor attribution were verified manually end-to-end (see below - **not yet covered by an automated test**) |
| **Security controls** | `test_auth.py` (6) | Missing token rejected, valid token accepted, garbage token rejected, wrong password rejected, unknown user rejected - exercised against the real JWT + database auth path via a session-scoped in-memory SQLite fixture, not a mocked dependency |
| **Failure behaviour** | Distributed across most test files | Invalid gate names, out-of-range qubit indices, wrong parameter counts, budget-exceeds-assets, out-of-range theta - each module's `ValueError`/`HTTPException` paths are tested, not just the happy path |
| **Governance / risk** | `test_portfolio_and_pqc.py` (subset of 26) | Every risk-register entry has an owner and mitigation, all 9 mandatory risk categories are present, every migration phase has required approvals and exit criteria, every phase requires CISO sign-off, the proof-of-concept's single-operator scope limitation is explicitly asserted (not just claimed in prose) |
| **Deployment** | **Not covered by pytest** | Verified manually: `kubectl get pods` (8/8 Running), Jenkins pipeline stages (Bandit, pip-audit, OPA/Conftest, Trivy), image builds. No automated test exercises the Kubernetes manifests, Terraform, or CI/CD pipeline itself. |
| **Integration (end-to-end across services)** | **Partially covered** | `TestClient`-based tests exercise the full FastAPI app stack (routing -> auth -> business logic -> response) in-process. What is NOT covered by an automated test: a real request travelling through the actual deployed frontend -> backend -> PostgreSQL -> Redis path inside the cluster. That was verified manually (see the curl-based verification run against the live pods), not by an automated integration test. |

---

## 2. Explicit gaps (stated, not hidden)

Per the rejection letter's own instruction ("must be clearly classified as
implemented, partially implemented, simulated, deferred, or future work"),
the honest state of testing coverage is:

- **No automated infrastructure tests.** Kubernetes manifests, the
  Terraform configuration, and the Jenkins pipeline are not exercised by
  any test - correctness here was verified manually during deployment
  (pod health, rollout status) and is not regression-tested.
- **No automated end-to-end test against the live cluster.** All 76 tests
  run against the FastAPI app in-process (via `TestClient`) or against an
  in-memory SQLite database. The real PostgreSQL-backed path, and the
  frontend-to-backend network path, were verified manually via `kubectl
  exec` / `curl` during development, not by a repeatable automated test.
- **No load/performance test is part of the pytest suite.** Performance
  evidence (see `docs/report_performance.md` / `backend/loadtest/`) comes
  from a separate Locust run, not from `pytest`.
- **PQC inventory scan endpoints are tested at the logic level**
  (`test_inventory_reproducible_per_seed`, `test_inventory_has_expected_fields`,
  the governance/risk tests) but the `/api/pqc/inventory/scan` -> cache ->
  `/api/pqc/risk-assessment` flow across multiple HTTP calls is not
  covered by an integration test.

## 3. What "76 tests passing" actually means

It means: every unit of business logic that can be exercised in-process
(circuit construction, algorithm correctness, optimisation logic, auth
against a real database schema, governance/risk data integrity, and every
API route's success and failure paths) is covered and passing
deterministically. It does NOT mean the deployed infrastructure, the
CI/CD pipeline, or a live cross-service request path has automated
regression coverage - those were verified manually and are documented as
such rather than implied by the test count.
