"""
Module 5 continued: migration planning.

Generates a phased migration roadmap from the inventory + risk scores -
the spec requires 'migration planning' and 'future migration
recommendations' as explicit deliverables. Each phase is tied to who
must approve it and what evidence closes it (app.governance.roles) -
a roadmap with dates but no decision-makers is a wishlist, not a plan.
"""

from typing import List, Dict

from app.governance.roles import ROLES, PHASE_APPROVAL_REQUIREMENTS, PHASE_EXIT_CRITERIA


def _governance_for_phase(phase: int) -> Dict:
    required_roles = PHASE_APPROVAL_REQUIREMENTS.get(phase, [])
    return {
        "required_approvals": [
            {"role": r, "title": ROLES[r]["title"]} for r in required_roles
        ],
        "exit_criteria": PHASE_EXIT_CRITERIA.get(phase, []),
    }


def generate_migration_plan(inventory: List[Dict]) -> Dict:
    """
    Group systems into migration phases by urgency, attach a rough
    timeline, and attach who must approve each phase closing and what
    evidence that approval requires.
    """
    immediate = [s for s in inventory if s["migration_urgency"] == "IMMEDIATE"]
    high = [s for s in inventory if s["migration_urgency"] == "HIGH"]
    medium = [s for s in inventory if s["migration_urgency"] == "MEDIUM"]
    low = [s for s in inventory if s["migration_urgency"] == "LOW"]

    phases = [
        {
            "phase": 1,
            "name": "Crypto-Agility Foundation",
            "timeline": "Months 1-3",
            "description": (
                "Before migrating any single system, establish the ability to "
                "swap cryptographic algorithms without major re-architecture: "
                "abstract crypto operations behind interfaces, inventory all "
                "certificate authorities and key management systems, and pilot "
                "ML-KEM/ML-DSA in a non-production environment."
            ),
            "systems_involved": [],
            "governance": _governance_for_phase(1),
        },
        {
            "phase": 2,
            "name": "Immediate-Risk System Migration",
            "timeline": "Months 3-9",
            "description": "Migrate all IMMEDIATE-urgency systems first - these combine long data retention with algorithms fully broken by Shor's algorithm.",
            "systems_involved": [s["system_id"] for s in immediate],
            "governance": _governance_for_phase(2),
        },
        {
            "phase": 3,
            "name": "High-Risk System Migration",
            "timeline": "Months 9-18",
            "description": "Migrate HIGH-urgency systems, prioritizing customer-facing and revenue-critical systems within this tier.",
            "systems_involved": [s["system_id"] for s in high],
            "governance": _governance_for_phase(3),
        },
        {
            "phase": 4,
            "name": "Remaining System Migration + Hybrid Deployment",
            "timeline": "Months 18-30",
            "description": (
                "Migrate MEDIUM and LOW urgency systems. Deploy hybrid classical+PQC "
                "schemes (e.g. X25519+ML-KEM) during this phase for systems requiring "
                "interoperability with parties not yet PQC-ready."
            ),
            "systems_involved": [s["system_id"] for s in medium + low],
            "governance": _governance_for_phase(4),
        },
        {
            "phase": 5,
            "name": "Full PQC-Only Operation + Continuous Monitoring",
            "timeline": "Month 30+",
            "description": (
                "Deprecate classical-only fallback paths. Establish continuous "
                "monitoring for new NIST guidance (e.g. FN-DSA finalization, HQC "
                "rollout) and periodic re-scanning of the cryptographic inventory."
            ),
            "systems_involved": [],
            "governance": _governance_for_phase(5),
        },
    ]

    return {
        "total_systems": len(inventory),
        "phases": phases,
        "estimated_total_duration": "Approximately 30+ months for full migration",
        "key_recommendation": (
            "Begin Phase 1 (crypto-agility foundation) immediately regardless of "
            "current risk scores - the 'harvest now, decrypt later' threat means "
            "delaying migration start has an ongoing cost even before a "
            "cryptographically-relevant quantum computer exists."
        ),
        "governance_note": (
            "Approval requirements and exit criteria above describe the "
            "accountability model this platform is designed to operate under. "
            "See /api/governance/model for the full role definitions and the "
            "current proof-of-concept's scope limitation (one operator holding "
            "every role)."
        ),
    }
