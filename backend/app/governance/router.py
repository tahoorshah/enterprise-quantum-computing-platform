"""
Governance API - platform-wide roles, approval requirements, decision
criteria behind phase transitions, and the risk register.

Endpoints:
    GET /api/governance/model             - full accountability model
    GET /api/governance/roles             - role definitions only
    GET /api/governance/phase/{phase}     - approvals + exit criteria for one phase
    GET /api/governance/risk-register     - full risk register
    GET /api/governance/risk-register/summary - executive risk rollup
"""

from fastapi import APIRouter, HTTPException

from app.governance.roles import (
    ROLES,
    PHASE_APPROVAL_REQUIREMENTS,
    PHASE_EXIT_CRITERIA,
    governance_model,
)
from app.governance.risk_register import get_risk_register, risk_register_summary

router = APIRouter()


@router.get("/model")
def get_governance_model():
    """Full governance model: roles, approval gates, and exit criteria."""
    return governance_model()


@router.get("/roles")
def get_roles():
    """Role definitions and what each is accountable for."""
    return ROLES


@router.get("/phase/{phase}")
def get_phase_governance(phase: int):
    """Approval requirements and exit criteria for a single migration phase."""
    if phase not in PHASE_APPROVAL_REQUIREMENTS:
        raise HTTPException(
            status_code=404,
            detail=f"No governance defined for phase {phase}. Valid phases: {sorted(PHASE_APPROVAL_REQUIREMENTS)}",
        )

    return {
        "phase": phase,
        "required_approvals": [
            {"role": r, "title": ROLES[r]["title"], "authority": ROLES[r]["approval_authority"]}
            for r in PHASE_APPROVAL_REQUIREMENTS[phase]
        ],
        "exit_criteria": PHASE_EXIT_CRITERIA[phase],
        "note": "Criteria must be evidenced before approval is meaningful; approval without evidence is a record, not a control.",
    }


@router.get("/risk-register")
def get_full_risk_register():
    """Every platform risk, scored and owned."""
    return get_risk_register()


@router.get("/risk-register/summary")
def get_risk_register_executive_summary():
    """Executive rollup: counts by rating/category, unmitigated items, top 5 by score."""
    return risk_register_summary()
