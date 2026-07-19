"""
Module 5 continued: migration planning.

Generates a phased migration roadmap from the inventory + risk scores -
the spec requires 'migration planning' and 'future migration
recommendations' as explicit deliverables.
"""

from typing import List, Dict


def generate_migration_plan(inventory: List[Dict]) -> Dict:
    """
    Group systems into migration phases by urgency, and attach a
    rough timeline. This is a standard phased-migration pattern used
    in real PQC transition planning (crypto-agility first, then
    highest-risk systems, then the long tail).
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
        },
        {
            "phase": 2,
            "name": "Immediate-Risk System Migration",
            "timeline": "Months 3-9",
            "description": "Migrate all IMMEDIATE-urgency systems first - these combine long data retention with algorithms fully broken by Shor's algorithm.",
            "systems_involved": [s["system_id"] for s in immediate],
        },
        {
            "phase": 3,
            "name": "High-Risk System Migration",
            "timeline": "Months 9-18",
            "description": "Migrate HIGH-urgency systems, prioritizing customer-facing and revenue-critical systems within this tier.",
            "systems_involved": [s["system_id"] for s in high],
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
    }
