"""
Module 5 - Post-Quantum Cryptography Readiness Platform: API endpoints.

Endpoints:
    GET  /api/pqc/algorithms/classical    - current algorithms at risk
    GET  /api/pqc/algorithms/nist-pqc     - NIST-approved PQC replacements
    GET  /api/pqc/threat-context          - harvest-now-decrypt-later + regulatory context
    POST /api/pqc/threat-demo             - genuine QPE demo (reuses Module 3's QFT)
    POST /api/pqc/inventory/scan          - run a simulated cryptographic inventory scan
    GET  /api/pqc/risk-assessment         - organizational risk rollup from last scan
    GET  /api/pqc/migration-plan          - phased migration roadmap
    GET  /api/pqc/readiness-report        - full executive readiness report
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from app.pqc.schemas import InventoryScanRequest, QuantumThreatDemoRequest
from app.pqc.crypto_reference import CLASSICAL_ALGORITHMS_AT_RISK, NIST_PQC_STANDARDS, QUANTUM_THREAT_TIMELINE_CONTEXT
from app.pqc.inventory import generate_inventory, organizational_risk_summary
from app.pqc.migration_plan import generate_migration_plan
from app.pqc.quantum_threat_demo import run_qpe_demo
from app.dashboard import metrics

router = APIRouter()

# Simple in-memory cache of the last inventory scan - this module doesn't
# need a full history log like Modules 1-3 (there's no "convergence" to
# track), just the most recent snapshot for the risk/migration/report
# endpoints to build on.
_last_inventory_cache = {"inventory": None, "generated_at": None, "seed": None}


@router.get("/algorithms/classical")
def classical_algorithms_at_risk():
    """Reference data: current cryptographic algorithms and their quantum vulnerability."""
    return CLASSICAL_ALGORITHMS_AT_RISK


@router.get("/algorithms/nist-pqc")
def nist_pqc_standards():
    """Reference data: NIST-finalized post-quantum replacement algorithms."""
    return NIST_PQC_STANDARDS


@router.get("/threat-context")
def threat_context():
    """Educational context: harvest-now-decrypt-later threat and regulatory timelines."""
    return QUANTUM_THREAT_TIMELINE_CONTEXT


@router.post("/threat-demo")
def quantum_threat_demo(request: QuantumThreatDemoRequest):
    """
    Genuine Quantum Phase Estimation demo - the actual subroutine Shor's
    algorithm builds on to break RSA/ECC. Reuses this platform's own QFT
    implementation from Module 3, directly connecting the 'why is this a
    threat' explanation to real, tested quantum code rather than a
    conceptual claim alone.
    """
    try:
        result = run_qpe_demo(request.theta, request.num_counting_qubits, request.shots)
    except ValueError as e:
        metrics.record_attempt("pqc_readiness", success=False)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        metrics.record_attempt("pqc_readiness", success=False)
        raise HTTPException(status_code=500, detail=f"QPE demo failed: {e}")
    metrics.record_attempt("pqc_readiness", success=True)
    return result


@router.post("/inventory/scan")
def run_inventory_scan(request: InventoryScanRequest):
    """
    Run a simulated cryptographic inventory scan across QFT Bank's
    (fictional) systems. Results are cached for the risk-assessment,
    migration-plan, and readiness-report endpoints to build on.
    """
    try:
        inventory = generate_inventory(seed=request.seed)
    except Exception as e:
        metrics.record_attempt("pqc_readiness", success=False)
        raise HTTPException(status_code=500, detail=f"Inventory scan failed: {e}")

    metrics.record_attempt("pqc_readiness", success=True)
    _last_inventory_cache["inventory"] = inventory
    _last_inventory_cache["generated_at"] = datetime.now(timezone.utc).isoformat()
    _last_inventory_cache["seed"] = request.seed

    return {
        "generated_at": _last_inventory_cache["generated_at"],
        "seed": request.seed,
        "inventory": inventory,
    }


@router.get("/risk-assessment")
def risk_assessment():
    """Organizational-level risk rollup, computed from the most recent inventory scan."""
    if _last_inventory_cache["inventory"] is None:
        raise HTTPException(
            status_code=404,
            detail="No inventory scan has been run yet. POST /api/pqc/inventory/scan first."
        )
    summary = organizational_risk_summary(_last_inventory_cache["inventory"])
    return {
        "based_on_scan_from": _last_inventory_cache["generated_at"],
        **summary,
    }


@router.get("/migration-plan")
def migration_plan():
    """Phased migration roadmap, computed from the most recent inventory scan."""
    if _last_inventory_cache["inventory"] is None:
        raise HTTPException(
            status_code=404,
            detail="No inventory scan has been run yet. POST /api/pqc/inventory/scan first."
        )
    return generate_migration_plan(_last_inventory_cache["inventory"])


@router.get("/readiness-report")
def readiness_report():
    """
    Full executive PQC readiness report - combines inventory, risk
    assessment, migration plan, and reference material into one
    document-style response, per the spec's 'executive readiness
    reports' requirement.
    """
    if _last_inventory_cache["inventory"] is None:
        raise HTTPException(
            status_code=404,
            detail="No inventory scan has been run yet. POST /api/pqc/inventory/scan first."
        )

    inventory = _last_inventory_cache["inventory"]
    return {
        "report_generated_at": datetime.now(timezone.utc).isoformat(),
        "based_on_scan_from": _last_inventory_cache["generated_at"],
        "organizational_risk_summary": organizational_risk_summary(inventory),
        "full_inventory": inventory,
        "migration_plan": generate_migration_plan(inventory),
        "reference_nist_standards": NIST_PQC_STANDARDS,
        "threat_context": QUANTUM_THREAT_TIMELINE_CONTEXT,
    }
