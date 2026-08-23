"""
Platform-wide governance: roles, responsibilities, and approval authority.

WHY THIS IS A SHARED MODULE, NOT PQC-SPECIFIC: governance applies across
the platform - cryptographic migration needs sign-off, but so do
deployments, schema changes, and incident closure. Defining roles once
and referencing them from each domain avoids three divergent definitions
of "who approves what".

SCOPE HONESTY: this platform is built and operated by a single developer.
The roles below describe the accountability model QFT Bank WOULD operate
under; in the current proof-of-concept every role resolves to the same
person. That is stated explicitly rather than implied, because an
approval workflow with one participant is a record, not a control.
"""

from typing import Dict, List


ROLES: Dict[str, Dict] = {
    "CISO": {
        "title": "Chief Information Security Officer",
        "accountable_for": [
            "Cryptographic migration programme outcome",
            "Acceptance of residual security risk",
            "Approval to advance between migration phases",
        ],
        "approval_authority": "Final sign-off on phase transitions and risk acceptance",
    },
    "crypto_architect": {
        "title": "Cryptographic Architect",
        "accountable_for": [
            "Algorithm selection and replacement mapping",
            "Crypto-agility design standards",
            "Technical validation of migrated systems",
        ],
        "approval_authority": "Technical sign-off on algorithm choices",
    },
    "system_owner": {
        "title": "System Owner (per system)",
        "accountable_for": [
            "Migration execution for their own system",
            "Confirming data sensitivity and retention classification",
            "Post-migration functional verification",
        ],
        "approval_authority": "Confirms their system's migration is complete",
    },
    "risk_and_compliance": {
        "title": "Risk & Compliance Officer",
        "accountable_for": [
            "Regulatory alignment (NIST, ISO 27001, financial-sector guidance)",
            "Evidence retention for audit",
            "Escalation of overdue high-urgency systems",
        ],
        "approval_authority": "Compliance sign-off before phase closure",
    },
    "platform_operations": {
        "title": "Platform Operations",
        "accountable_for": [
            "Deployment execution and rollback",
            "Monitoring and incident response during migration windows",
            "Change record accuracy",
        ],
        "approval_authority": "Operational readiness sign-off for deployment",
    },
}


PHASE_APPROVAL_REQUIREMENTS: Dict[int, List[str]] = {
    1: ["crypto_architect", "CISO"],
    2: ["system_owner", "crypto_architect", "platform_operations", "risk_and_compliance", "CISO"],
    3: ["system_owner", "crypto_architect", "platform_operations", "risk_and_compliance", "CISO"],
    4: ["system_owner", "crypto_architect", "platform_operations", "CISO"],
    5: ["crypto_architect", "risk_and_compliance", "CISO"],
}


PHASE_EXIT_CRITERIA: Dict[int, List[str]] = {
    1: [
        "Cryptographic operations abstracted behind a swappable interface",
        "Full certificate authority and key management inventory documented",
        "ML-KEM/ML-DSA pilot executed in non-production with recorded results",
    ],
    2: [
        "Every IMMEDIATE-urgency system migrated or granted a documented exception",
        "Functional verification passed for each migrated system",
        "Rollback tested for at least one representative system",
    ],
    3: [
        "Every HIGH-urgency system migrated or granted a documented exception",
        "No customer-facing regression attributable to the migration",
    ],
    4: [
        "MEDIUM and LOW urgency systems migrated",
        "Hybrid classical+PQC interoperability verified with external counterparties",
    ],
    5: [
        "Classical-only fallback paths removed or explicitly justified",
        "Continuous NIST guidance monitoring process operating",
        "Cryptographic inventory re-scan scheduled and owned",
    ],
}


def assign_system_owner(system_id: str, data_sensitivity: str) -> str:
    """
    Map a system to its accountable owning function. Deterministic (driven
    by sensitivity classification) rather than random, so the same system
    always reports the same owner across scans - an owner that changes
    between runs would be useless for accountability.
    """
    if data_sensitivity == "CRITICAL":
        return "Head of Core Banking Technology"
    if data_sensitivity == "HIGH":
        return "Head of Digital Channels"
    if data_sensitivity == "MEDIUM":
        return "Head of Internal Platforms"
    return "Head of Public Web Services"


def escalation_path(migration_urgency: str) -> Dict:
    """
    Who gets notified, and how fast, when a system's migration slips.
    Urgency drives escalation speed - an IMMEDIATE system overdue is a
    board-level matter; a LOW one is a backlog item.
    """
    paths = {
        "IMMEDIATE": {
            "review_frequency": "Weekly",
            "escalates_to": "CISO, then Board Risk Committee if unresolved after 30 days",
            "overdue_threshold_days": 30,
        },
        "HIGH": {
            "review_frequency": "Fortnightly",
            "escalates_to": "CISO if unresolved after 60 days",
            "overdue_threshold_days": 60,
        },
        "MEDIUM": {
            "review_frequency": "Monthly",
            "escalates_to": "Risk & Compliance Officer if unresolved after 120 days",
            "overdue_threshold_days": 120,
        },
        "LOW": {
            "review_frequency": "Quarterly",
            "escalates_to": "Tracked in backlog; no automatic escalation",
            "overdue_threshold_days": 365,
        },
    }
    return paths.get(migration_urgency, paths["LOW"])


def governance_model() -> Dict:
    """The full accountability model, for the API and readiness report."""
    return {
        "roles": ROLES,
        "phase_approval_requirements": PHASE_APPROVAL_REQUIREMENTS,
        "phase_exit_criteria": PHASE_EXIT_CRITERIA,
        "implementation_status": "Designed and represented in the platform; not enforced by workflow tooling",
        "scope_limitation": (
            "This proof-of-concept is built and operated by one person, so every "
            "role above currently resolves to the same individual. The separation "
            "of duties described is the model QFT Bank would operate, not a "
            "control currently in force. Enforcing it would require an identity "
            "provider with role mapping (see deferred Keycloak decision) and a "
            "workflow system holding approval state."
        ),
    }
