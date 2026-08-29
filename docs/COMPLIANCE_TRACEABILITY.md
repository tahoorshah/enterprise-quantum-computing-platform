# Compliance & Standards Traceability

Each framework below is mapped to specific evidence in this repository, with a status of
Full, Partial, Deferred or Not Applicable. Partial means the control area is addressed with
real evidence but is not fully implemented or independently validated; the specific gap is
named in each row.

| Framework | Relevant control area | Evidence in repo | Status |
|---|---|---|---|
| **NIST PQC (FIPS 203/204/205)** | Post-quantum algorithm catalogue, migration planning | `app/pqc/` module: crypto inventory scan, 5-phase migration plan, ML-KEM/ML-DSA/SLH-DSA readiness reporting | Partial - advisory/simulated, not a live crypto audit of real systems |
| **NIST CSF 2.0** | Identify / Protect / Detect / Respond / Recover | Identify: `app/governance/risk_register.py`. Protect: JWT auth against a database-backed user table, NetworkPolicy, K8s Secrets, container hardening. Detect: Prometheus/Grafana. Respond: escalation paths per risk urgency in `app/governance/roles.py`. Recover: DB in-memory fallback | Partial - escalation paths are defined but no incident runbook or on-call rota exists |
| **ISO/IEC 27001** | Access control (A.9), cryptography (A.10), risk assessment | Database-backed users table with bcrypt hashes and role claims; Secret-based credentials; 17-entry risk register scored on a 5x5 matrix with named owning roles | Partial - roles and accountability are documented, but no ISMS management review cycle operates |
| **ISO/IEC 27017** | Cloud-specific security controls | NetworkPolicy (default-deny), non-root containers, read-only root filesystem | Partial - shared responsibility model not documented for the Minikube/EC2 boundary |
| **ISO/IEC 27018** | PII protection in public cloud | Platform processes only simulated financial data; no real PII is collected | Not applicable - stated explicitly rather than force-mapped |
| **ISO/IEC 23837** | Quantum-safe security evaluation | PQC threat demonstration: quantum phase estimation built on this platform's own QFT implementation from Module 3 | Partial - an educational demonstration, not a certified evaluation |
| **COBIT 2019** | IT governance, risk management | Defined approval authority per migration phase with documented exit criteria (`app/governance/roles.py`); Jenkins pipeline gates (Bandit, pip-audit, OPA, Trivy) as automated governance checkpoints | Partial - approval gates are designed and represented but not enforced by workflow tooling |
| **ITIL 4** | Service management, incident handling | `docs/aws-ec2-setup.md` documents the deployment procedure; escalation thresholds defined per risk urgency | Deferred - no service catalogue or incident management process exists |
| **OWASP Top 10** | A01 Broken Access Control, A07 Auth Failures, A06 Vulnerable Components | JWT auth on every route verified against a real user store (A01, A07); Pydantic schema validation on all inputs; pip-audit in CI (A06); slowapi rate limiting (`app/rate_limit.py`) - a strict per-IP limit on `/api/auth/login` against brute-force, a default per-IP/per-route limit on every other `/api/*` route (A07) | Partial - rate-limit counters are in-memory per process, not shared across Kubernetes replicas |
| **CIS Critical Security Controls** | Inventory, secure configuration, vulnerability management | Trivy image scanning + SBOM, non-root and capability-dropped containers, dependency scanning | Partial - no CIS Benchmark hardening applied to the base OS or K8s configuration |

## Testing and evidence

Test coverage per mandatory area, including what is **not** covered by automated tests, is
documented in [`TESTING_COVERAGE.md`](TESTING_COVERAGE.md). Performance measurements and their
limits are in [`../backend/loadtest/FINDINGS.md`](../backend/loadtest/FINDINGS.md). Technologies
deliberately not implemented, with rationale, are in [`SCOPE_DECISIONS.md`](SCOPE_DECISIONS.md).
