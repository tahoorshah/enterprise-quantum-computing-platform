## CI/CD Pipeline (Jenkins) — 11 Stages

1.  Checkout
2.  Backend: Build & Test
3.  Security: SAST (Bandit)
4.  Security: Dependency Scan (pip-audit)
5.  Frontend: Build
6.  Security: Policy as Code (OPA/Conftest) — hard gate
7.  Docker: Build Images
8.  Security: Container Scan (Trivy)
9.  Security: SBOM Generation (Trivy CycloneDX)
10. Supply Chain: Push & Sign Images (Cosign)
11. Supply Chain: Verify Signatures (Cosign) — hard gate

The pipeline runs three advisory security scans (Bandit, pip-audit, Trivy)
and two enforced hard gates: the OPA policy gate and the Cosign signature
verification gate. A failing gate stops the build.
