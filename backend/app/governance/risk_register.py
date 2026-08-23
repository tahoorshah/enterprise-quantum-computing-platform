"""
Platform-wide risk register.

The rejection letter names nine risk categories explicitly (technical,
financial, security, operational, data, quantum-computing, migration,
availability, implementation) and states that a "formal and sufficiently
structured risk-management approach is not clearly demonstrated." This
module is that structure: every risk has an owner (from
app.governance.roles), a likelihood/impact score, and a stated
mitigation - a risk with no owner or no mitigation is a complaint, not
a risk register entry.

SCORING: likelihood and impact are each rated 1-5 (Low..Critical).
risk_score = likelihood * impact (max 25). This is the standard
qualitative 5x5 risk matrix used in ISO 31000 / NIST RMF-aligned
registers - chosen over a quantitative model because several of these
risks (e.g. "quantum computer arrives sooner than expected") have no
reliable probability distribution to quantify.
"""

from typing import Dict, List

from app.governance.roles import ROLES


LIKELIHOOD_SCALE = {1: "Rare", 2: "Unlikely", 3: "Possible", 4: "Likely", 5: "Almost Certain"}
IMPACT_SCALE = {1: "Negligible", 2: "Minor", 3: "Moderate", 4: "Major", 5: "Severe"}


def _rating(score: int) -> str:
    if score >= 15:
        return "CRITICAL"
    if score >= 9:
        return "HIGH"
    if score >= 4:
        return "MEDIUM"
    return "LOW"


# Each entry: id, category, description, likelihood (1-5), impact (1-5),
# owning role (from ROLES), mitigation, and current status. Status is
# honest about what's actually been done versus planned - a risk marked
# "mitigated" with no corresponding code change would be an overclaim of
# exactly the kind the rejection letter warned against.
_RISKS: List[Dict] = [
    {
        "id": "RISK-TECH-01",
        "category": "Technical",
        "description": "Qiskit, PennyLane, and Cirq could silently disagree on a circuit's result due to a simulator bug or implementation error, undermining confidence in any single-framework result.",
        "likelihood": 2,
        "impact": 3,
        "owner_role": "crypto_architect",
        "mitigation": "Cross-framework validation (Module 6) statistically compares all three against theory and each other using total variation distance, with a documented tolerance derived from sampling error.",
        "status": "MITIGATED - implemented and tested (test_frameworks.py)",
    },
    {
        "id": "RISK-TECH-02",
        "category": "Technical",
        "description": "QAOA is a stochastic heuristic; a single favourable run could misrepresent its actual reliability for portfolio optimisation.",
        "likelihood": 4,
        "impact": 3,
        "owner_role": "crypto_architect",
        "mitigation": "Portfolio optimisation runs multiple independent QAOA trials and reports the optimum-recovery rate and cost spread across all of them, not a single outcome.",
        "status": "MITIGATED - implemented and tested",
    },
    {
        "id": "RISK-FIN-01",
        "category": "Financial",
        "description": "AWS EC2 compute costs for the demonstration environment (t3.xlarge or larger) accrue continuously if the instance is left running.",
        "likelihood": 4,
        "impact": 2,
        "owner_role": "platform_operations",
        "mitigation": "Instance stopped when not actively developing or demonstrating; documented in docs/aws-ec2-setup.md.",
        "status": "MITIGATED - operational practice, not code-enforced",
    },
    {
        "id": "RISK-FIN-02",
        "category": "Financial",
        "description": "A real PQC migration at a bank the size of QFT Bank (USD 850B AUM) would require substantial capital investment across ~30 months; no cost estimate is provided.",
        "likelihood": 5,
        "impact": 4,
        "owner_role": "CISO",
        "mitigation": "None currently. Deliberately out of scope: cost estimation requires vendor engagement and headcount planning outside this proof-of-concept's remit.",
        "status": "ACCEPTED - explicitly out of scope, stated rather than omitted",
    },
    {
        "id": "RISK-SEC-01",
        "category": "Security",
        "description": "Unauthenticated access to any API route would expose quantum simulation, portfolio, and PQC data with no access control.",
        "likelihood": 2,
        "impact": 4,
        "owner_role": "crypto_architect",
        "mitigation": "JWT authentication enforced on every /api/* route via a router-level dependency; verified by test_auth.py against a real database-backed user store (not mocked).",
        "status": "MITIGATED - implemented and tested",
    },
    {
        "id": "RISK-SEC-02",
        "category": "Security",
        "description": "Demo credentials (analyst/admin) are publicly documented in the repository README and this register, which is acceptable for a proof-of-concept but would be a severe finding in production.",
        "likelihood": 5,
        "impact": 2,
        "owner_role": "CISO",
        "mitigation": "Explicitly labelled as demo-only in code comments and documentation; production deployment would require a real identity provider (see SCOPE_DECISIONS.md, Keycloak decision).",
        "status": "ACCEPTED - documented limitation, not hidden",
    },
    {
        "id": "RISK-SEC-03",
        "category": "Security",
        "description": "Grafana and Prometheus dashboards are reachable within the cluster with no authentication layer of their own.",
        "likelihood": 3,
        "impact": 3,
        "owner_role": "platform_operations",
        "mitigation": "Network-level containment: only frontend is exposed via NodePort; Grafana/Prometheus are ClusterIP-only, unreachable without kubectl port-forward or a NetworkPolicy bypass.",
        "status": "PARTIALLY MITIGATED - network isolation only, no auth on the dashboards themselves",
    },
    {
        "id": "RISK-OPS-01",
        "category": "Operational",
        "description": "Single-node Minikube on one EC2 instance is a single point of failure; a pod crash or node failure interrupts the entire platform during a live demonstration.",
        "likelihood": 3,
        "impact": 4,
        "owner_role": "platform_operations",
        "mitigation": "Documented as an explicit proof-of-concept limitation in SCOPE_DECISIONS.md rather than presented as production-grade; production approach (multi-node, managed Kubernetes) is stated.",
        "status": "ACCEPTED - documented, not resolved (out of scope for a PoC)",
    },
    {
        "id": "RISK-OPS-02",
        "category": "Operational",
        "description": "No automated backup of the PostgreSQL PVC; a volume failure loses all execution history and audit records.",
        "likelihood": 2,
        "impact": 3,
        "owner_role": "platform_operations",
        "mitigation": "None implemented. Acceptable for a demonstration environment with no real financial data; would be mandatory before any production use.",
        "status": "ACCEPTED - out of scope for a PoC, stated explicitly",
    },
    {
        "id": "RISK-DATA-01",
        "category": "Data",
        "description": "Execution history stores full result payloads (including quantum circuit details) as JSON with no retention limit, which could grow unbounded.",
        "likelihood": 3,
        "impact": 2,
        "owner_role": "system_owner",
        "mitigation": "Schema design deliberately separates execution_runs (audit header) from execution_results (payload) so a retention policy could purge old payloads while keeping the audit trail - this is a design decision, not yet an enforced policy.",
        "status": "PARTIALLY MITIGATED - schema supports retention; no automated purge implemented",
    },
    {
        "id": "RISK-DATA-02",
        "category": "Data",
        "description": "All financial and cryptographic-inventory data is simulated; a reviewer could mistake generated figures for real QFT Bank data.",
        "likelihood": 2,
        "impact": 3,
        "owner_role": "risk_and_compliance",
        "mitigation": "Every simulated dataset is generated from an explicit, documented random seed and labelled as simulated in both code comments and API responses (e.g. 'Fictional Organisation for Assessment Purposes').",
        "status": "MITIGATED",
    },
    {
        "id": "RISK-QC-01",
        "category": "Quantum Computing",
        "description": "Results demonstrated on classical simulators (AerSimulator, default.qubit, Cirq Simulator) may not hold on real NISQ hardware, where noise and decoherence dominate.",
        "likelihood": 5,
        "impact": 3,
        "owner_role": "crypto_architect",
        "mitigation": "Every comparison and claim in the platform is explicitly scoped to simulator results; the cross-framework validation explanation states this limitation directly rather than implying hardware equivalence.",
        "status": "MITIGATED - by disclosure, not by hardware testing (hardware access is out of scope per the project spec)",
    },
    {
        "id": "RISK-QC-02",
        "category": "Quantum Computing",
        "description": "Quantum advantage claims for portfolio optimisation could be overstated if QAOA's small-scale demo were read as evidence of speedup.",
        "likelihood": 3,
        "impact": 4,
        "owner_role": "crypto_architect",
        "mitigation": "The comparison output explicitly states no speed advantage is claimed or measured, and that brute force is exact and typically faster at this scale by design.",
        "status": "MITIGATED - implemented and tested",
    },
    {
        "id": "RISK-MIG-01",
        "category": "Migration",
        "description": "A phased PQC migration with no defined approval authority or exit criteria could stall indefinitely or advance without adequate verification.",
        "likelihood": 4,
        "impact": 4,
        "owner_role": "CISO",
        "mitigation": "Every migration phase has named approval roles and explicit exit criteria (app.governance.roles); the readiness report surfaces both.",
        "status": "MITIGATED - implemented and tested",
    },
    {
        "id": "RISK-MIG-02",
        "category": "Migration",
        "description": "NIST PQC standards may be revised or new algorithms finalised (e.g. FN-DSA, HQC) after this platform's algorithm-to-replacement mapping was written, making recommendations stale.",
        "likelihood": 4,
        "impact": 2,
        "owner_role": "risk_and_compliance",
        "mitigation": "Phase 5 of the migration plan explicitly includes continuous monitoring for new NIST guidance as an exit criterion.",
        "status": "PARTIALLY MITIGATED - planned as a future-phase activity, not automated",
    },
    {
        "id": "RISK-AVAIL-01",
        "category": "Availability",
        "description": "If PostgreSQL becomes unreachable, execution history writes could fail silently, losing audit records without the user noticing.",
        "likelihood": 2,
        "impact": 3,
        "owner_role": "platform_operations",
        "mitigation": "Graceful in-memory fallback: the persistence layer catches DB errors, logs a warning, and continues serving from memory rather than crashing or silently dropping data. /health reports which backend is active.",
        "status": "MITIGATED - implemented and tested",
    },
    {
        "id": "RISK-IMPL-01",
        "category": "Implementation",
        "description": "Components could be inconsistently described as 'implemented' across the deck, docs, and code, repeating the exact inconsistency the rejection letter cited.",
        "likelihood": 3,
        "impact": 4,
        "owner_role": "risk_and_compliance",
        "mitigation": "SCOPE_DECISIONS.md explicitly labels every deferred technology (Keycloak, OpenTelemetry, Wazuh) as not implemented with a stated reason; this risk register itself uses MITIGATED / PARTIALLY MITIGATED / ACCEPTED status labels consistently rather than a binary done/not-done claim.",
        "status": "PARTIALLY MITIGATED - consistent in backend docs; presentation deck consistency still to be audited",
    },
]


def get_risk_register() -> List[Dict]:
    """Return every risk with its computed score and rating attached."""
    enriched = []
    for r in _RISKS:
        score = r["likelihood"] * r["impact"]
        enriched.append({
            **r,
            "likelihood_label": LIKELIHOOD_SCALE[r["likelihood"]],
            "impact_label": IMPACT_SCALE[r["impact"]],
            "risk_score": score,
            "risk_rating": _rating(score),
            "owner_title": ROLES[r["owner_role"]]["title"],
        })
    return enriched


def risk_register_summary() -> Dict:
    """Roll-up counts and the highest-scoring open items, for an executive view."""
    risks = get_risk_register()
    by_rating: Dict[str, int] = {}
    by_category: Dict[str, int] = {}
    for r in risks:
        by_rating[r["risk_rating"]] = by_rating.get(r["risk_rating"], 0) + 1
        by_category[r["category"]] = by_category.get(r["category"], 0) + 1

    unmitigated = [r for r in risks if r["status"].startswith("ACCEPTED") or r["status"].startswith("PARTIALLY")]
    top_by_score = sorted(risks, key=lambda r: r["risk_score"], reverse=True)[:5]

    return {
        "total_risks": len(risks),
        "by_rating": by_rating,
        "by_category": by_category,
        "unmitigated_or_partial_count": len(unmitigated),
        "unmitigated_or_partial_ids": [r["id"] for r in unmitigated],
        "top_5_by_score": [{"id": r["id"], "description": r["description"], "risk_score": r["risk_score"], "risk_rating": r["risk_rating"]} for r in top_by_score],
        "scoring_method": "Qualitative 5x5 matrix (likelihood 1-5 x impact 1-5, max 25), consistent with ISO 31000 practice.",
    }
