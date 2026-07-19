"""
Module 5 continued: simulated cryptographic inventory and risk scoring.

The capstone spec explicitly requires 'cryptographic inventory management
(simulated)' - real production systems don't exist for this fictional
QFT Bank, so this generates a reproducible, plausible inventory of
banking systems and their current cryptographic usage, then scores each
one for post-quantum migration urgency.
"""

import random
from typing import List, Dict


# A plausible set of systems a bank like QFT Bank would actually run,
# each using a specific classical algorithm today, with a data
# sensitivity classification driving how urgently it needs to migrate.
SYSTEM_TEMPLATES = [
    {"name": "Core Banking Transaction Ledger", "current_algorithm": "RSA-2048", "data_sensitivity": "CRITICAL", "data_lifetime_years": 30},
    {"name": "Customer Authentication Service", "current_algorithm": "ECDSA-P256", "data_sensitivity": "CRITICAL", "data_lifetime_years": 10},
    {"name": "SWIFT Payment Gateway", "current_algorithm": "RSA-4096", "data_sensitivity": "CRITICAL", "data_lifetime_years": 20},
    {"name": "Internal Employee VPN", "current_algorithm": "ECDH-P384", "data_sensitivity": "HIGH", "data_lifetime_years": 5},
    {"name": "Customer Mobile Banking App TLS", "current_algorithm": "ECDHE-RSA", "data_sensitivity": "HIGH", "data_lifetime_years": 7},
    {"name": "Archived Customer Records (Cold Storage)", "current_algorithm": "AES-256", "data_sensitivity": "CRITICAL", "data_lifetime_years": 50},
    {"name": "Internal Microservice mTLS", "current_algorithm": "ECDSA-P256", "data_sensitivity": "MEDIUM", "data_lifetime_years": 3},
    {"name": "Wealth Management Portfolio Database", "current_algorithm": "RSA-2048", "data_sensitivity": "HIGH", "data_lifetime_years": 15},
    {"name": "Fraud Detection Model Weights (at rest)", "current_algorithm": "AES-256", "data_sensitivity": "MEDIUM", "data_lifetime_years": 5},
    {"name": "Digital Trading Platform Signatures", "current_algorithm": "ECDSA-P256", "data_sensitivity": "HIGH", "data_lifetime_years": 10},
    {"name": "Email/Document Signing (Compliance)", "current_algorithm": "RSA-2048", "data_sensitivity": "MEDIUM", "data_lifetime_years": 10},
    {"name": "Public Website TLS Certificate", "current_algorithm": "ECDHE-RSA", "data_sensitivity": "LOW", "data_lifetime_years": 2},
]

# Base risk contribution per algorithm - RSA/ECC/DH are CRITICAL because
# Shor's algorithm breaks them entirely (not just weakens them), while
# AES-256 only needs a bit-length upgrade consideration under Grover's.
ALGORITHM_BASE_RISK = {
    "RSA-2048": 9, "RSA-4096": 8,  # 4096 buys a bit more time but still fully broken by Shor's eventually
    "ECDSA-P256": 9, "ECDSA-P384": 9, "ECDH-P384": 9, "ECDHE-RSA": 9,
    "AES-256": 2,  # genuinely lower risk - only weakened (not broken) by Grover's
}

SENSITIVITY_WEIGHT = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}


def generate_inventory(seed: int = 42) -> List[Dict]:
    """
    Generate a reproducible simulated cryptographic inventory. Uses a
    fixed seed so repeated calls give consistent results (auditable),
    while still simulating some realistic variation (e.g. last-scanned
    dates) via the random module.
    """
    rng = random.Random(seed)
    inventory = []

    for i, system in enumerate(SYSTEM_TEMPLATES):
        base_risk = ALGORITHM_BASE_RISK.get(system["current_algorithm"], 5)
        sensitivity_weight = SENSITIVITY_WEIGHT[system["data_sensitivity"]]

        # Harvest-now-decrypt-later factor: longer data lifetime = more
        # urgent, since "harvested" ciphertext stays valuable to attack
        # for as long as the underlying data needs to stay confidential.
        # multiplier ranges 1x (short-lived) to 4x (30+ year retention),
        # scaled so a CRITICAL, long-lived, Shor's-broken system can
        # actually reach the IMMEDIATE tier - a worst-case system should
        # not be mathematically capped below the top urgency category.
        lifetime_factor = min(system["data_lifetime_years"] / 10, 3.0)
        multiplier = 1 + lifetime_factor

        raw_score = base_risk * sensitivity_weight * multiplier
        risk_score = round(min(raw_score, 100), 1)

        if risk_score >= 70:
            urgency = "IMMEDIATE"
        elif risk_score >= 45:
            urgency = "HIGH"
        elif risk_score >= 20:
            urgency = "MEDIUM"
        else:
            urgency = "LOW"

        inventory.append({
            "system_id": f"SYS-{i+1:03d}",
            "system_name": system["name"],
            "current_algorithm": system["current_algorithm"],
            "data_sensitivity": system["data_sensitivity"],
            "data_lifetime_years": system["data_lifetime_years"],
            "quantum_risk_score": risk_score,
            "migration_urgency": urgency,
            "recommended_replacement": _recommend_replacement(system["current_algorithm"]),
        })

    return inventory


def _recommend_replacement(current_algorithm: str) -> str:
    """Map each classical algorithm to its NIST PQC replacement."""
    if "RSA" in current_algorithm or "ECDH" in current_algorithm:
        return "ML-KEM (FIPS 203) for key exchange"
    if "ECDSA" in current_algorithm:
        return "ML-DSA (FIPS 204), with SLH-DSA (FIPS 205) as conservative backup for high-value signatures"
    if "AES-256" in current_algorithm:
        return "No urgent change required - AES-256 remains adequate under Grover's algorithm; monitor NIST guidance"
    return "Requires manual review - algorithm not in standard mapping"


def organizational_risk_summary(inventory: List[Dict]) -> Dict:
    """Roll up individual system risk scores into an organization-level summary."""
    if not inventory:
        return {"total_systems": 0}

    total = len(inventory)
    avg_risk = round(sum(s["quantum_risk_score"] for s in inventory) / total, 1)
    urgency_counts = {}
    for s in inventory:
        urgency_counts[s["migration_urgency"]] = urgency_counts.get(s["migration_urgency"], 0) + 1

    critical_sensitivity_systems = [s for s in inventory if s["data_sensitivity"] == "CRITICAL"]
    immediate_action_systems = [s for s in inventory if s["migration_urgency"] == "IMMEDIATE"]

    return {
        "total_systems_scanned": total,
        "average_quantum_risk_score": avg_risk,
        "systems_by_urgency": urgency_counts,
        "critical_sensitivity_system_count": len(critical_sensitivity_systems),
        "systems_requiring_immediate_action": [s["system_id"] for s in immediate_action_systems],
        "overall_organizational_risk_rating": (
            "CRITICAL" if avg_risk >= 60 else
            "HIGH" if avg_risk >= 40 else
            "MODERATE" if avg_risk >= 20 else
            "LOW"
        ),
    }
