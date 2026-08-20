# Compliance & Standards Traceability

Replaces the unverified "all 10 frameworks mapped" claim (Slide 13) with an honest,
evidence-linked mapping. Status is Full / Partial / Deferred per framework - not a
blanket claim of full compliance, since that would not survive Stage 2 code review.

| Framework | Relevant control area | Evidence in repo | Status |
|---|---|---|---|
| **NIST PQC (FIPS 203/204/205)** | Post-quantum algorithm catalogue, migration planning | `app/pqc/` module: crypto inventory scan, 5-phase migration plan, ML-KEM/ML-DSA/SLH-DSA readiness reporting | Partial - advisory/simulated, not a live crypto audit of real systems |
| **NIST CSF 2.0** | Identify / Protect / Detect / Respond / Recover | Identify: Risk Register. Protect: JWT auth, NetworkPolicy, K8s Secrets, container hardening. Detect: Prometheus/Grafana. Recover: DB in-memory fallback | Partial - no formal Respond process (incident runbook) exists |
| **ISO/IEC 27001** | Access control (A.9), cryptography (A.10), risk assessment | JWT authentication (this revision), Secret-based credentials, Risk Register | Partial - no formal ISMS documentation, no management review cycle |
| **ISO/IEC 27017** | Cloud-specific security controls | NetworkPolicy (default-deny), non-root containers, read-only root filesystem | Partial - shared responsibility model not documented for Minikube/EC2 boundary |
| **ISO/IEC 27018** | PII protection in public cloud | N/A by design - platform only processes simulated financial data, no real PII collected | Not applicable - stated explicitly, not silently omitted |
| **ISO/IEC 23837** | Quantum-safe security evaluation | PQC Threat Demonstration (Shor's-algorithm concept via Module 3's QFT, reused in PQC module) | Implemented as an educational/demo artifact, not a certified evaluation |
| **COBIT 2019** | IT governance, risk management | Risk Register; Jenkins pipeline gates (Bandit, pip-audit, OPA, Trivy) act as automated governance checkpoints | Partial - no formal change advisory board or approval workflow |
| **ITIL 4** | Service management, incident handling | `docs/aws-ec2-setup.md` documents deployment procedure | Deferred - no incident management or service catalogue process exists |
| **OWASP Top 10** | A01 Broken Access Control, A07 Auth Failures, A06 Vulnerable Components | JWT auth (closes A07), Pydantic schema validation on all inputs, pip-audit (A06) | Partial - no rate limiting, no CSRF protection (N/A for token-based API), input validation via schemas only |
| **CIS Critical Security Controls** | Inventory, secure configuration, vulnerability management | Trivy image scanning + SBOM, non-root/capability-dropped containers, dependency scanning | Partial - no CIS Benchmark hardening applied to the base OS/K8s config itself |

