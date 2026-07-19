"""
Module 5 - Post-Quantum Cryptography Readiness Platform: reference data.

This module is educational/governance in nature (per the capstone spec),
not computational - there's no quantum circuit to simulate here. What
matters is that the reference data is ACCURATE and CURRENT, not a
demonstration of quantum mechanics.

Source basis: NIST finalized ML-KEM (FIPS 203), ML-DSA (FIPS 204), and
SLH-DSA (FIPS 205) in August 2024, concluding an 8-year evaluation
process. FN-DSA (FIPS 206, based on FALCON) remained in draft as of
this writing. HQC was selected in 2025 as a structurally-different
backup KEM (code-based, not lattice-based) in case lattice problems are
ever broken. This file was built against that information rather than
older pre-2024 sources that still use draft names like "CRYSTALS-Kyber."
"""

CLASSICAL_ALGORITHMS_AT_RISK = {
    "RSA": {
        "type": "Public-key encryption / digital signatures",
        "hardness_assumption": "Integer factorization",
        "quantum_threat": "Broken by Shor's algorithm (polynomial time) - not just weakened, fully broken",
        "typical_key_sizes": "2048-4096 bit",
        "risk_level": "CRITICAL",
    },
    "ECC / ECDSA / ECDH": {
        "type": "Public-key encryption / signatures / key exchange",
        "hardness_assumption": "Elliptic curve discrete logarithm problem",
        "quantum_threat": "Broken by Shor's algorithm (polynomial time) - fully broken, same as RSA",
        "typical_key_sizes": "256-521 bit",
        "risk_level": "CRITICAL",
    },
    "Diffie-Hellman (DH/DHE)": {
        "type": "Key exchange",
        "hardness_assumption": "Discrete logarithm problem",
        "quantum_threat": "Broken by Shor's algorithm (polynomial time) - fully broken",
        "typical_key_sizes": "2048+ bit",
        "risk_level": "CRITICAL",
    },
    "AES-128": {
        "type": "Symmetric encryption",
        "hardness_assumption": "Brute-force key search",
        "quantum_threat": "Weakened (not broken) by Grover's algorithm - effective security roughly halved to ~64-bit equivalent",
        "typical_key_sizes": "128 bit",
        "risk_level": "MODERATE - recommend migrating to AES-256",
    },
    "AES-256": {
        "type": "Symmetric encryption",
        "hardness_assumption": "Brute-force key search",
        "quantum_threat": "Weakened by Grover's algorithm - effective security roughly halved to ~128-bit equivalent, still considered adequate",
        "typical_key_sizes": "256 bit",
        "risk_level": "LOW - generally considered quantum-safe for now",
    },
    "SHA-256 / SHA-3": {
        "type": "Cryptographic hash function",
        "hardness_assumption": "Collision resistance / preimage resistance",
        "quantum_threat": "Weakened by Grover's algorithm for preimage search, but no known efficient quantum collision attack",
        "typical_key_sizes": "256 bit output",
        "risk_level": "LOW - generally considered quantum-safe",
    },
}

NIST_PQC_STANDARDS = {
    "ML-KEM": {
        "fips_standard": "FIPS 203",
        "finalized": "August 2024",
        "based_on": "CRYSTALS-Kyber",
        "purpose": "Key Encapsulation Mechanism (KEM) - replaces RSA/ECDH for key exchange",
        "hardness_assumption": "Module Learning With Errors (Module-LWE), a lattice-based problem",
        "parameter_sets": ["ML-KEM-512", "ML-KEM-768", "ML-KEM-1024"],
        "public_key_size_bytes": "800-1568",
        "ciphertext_size_bytes": "768-1568",
        "replaces": ["RSA key exchange", "ECDH", "Diffie-Hellman"],
    },
    "ML-DSA": {
        "fips_standard": "FIPS 204",
        "finalized": "August 2024",
        "based_on": "CRYSTALS-Dilithium",
        "purpose": "Digital signatures - replaces RSA/ECDSA for signing and verification",
        "hardness_assumption": "Module-LWE and Module-SIS, lattice-based problems",
        "parameter_sets": ["ML-DSA-44", "ML-DSA-65", "ML-DSA-87"],
        "signature_size_bytes": "2420-4595",
        "replaces": ["RSA signatures", "ECDSA"],
    },
    "SLH-DSA": {
        "fips_standard": "FIPS 205",
        "finalized": "August 2024",
        "based_on": "SPHINCS+",
        "purpose": "Digital signatures - conservative backup to ML-DSA",
        "hardness_assumption": "Collision resistance of hash functions (SHA-256/SHA-3) - not lattice-based, a deliberately different mathematical foundation as insurance",
        "signature_size_bytes": "7856-49856 (significantly larger than ML-DSA)",
        "replaces": ["RSA signatures", "ECDSA", "used as a hedge if ML-DSA's lattice assumption is ever broken"],
        "note": "Stateless design avoids the key-management pitfalls of earlier hash-based schemes like XMSS",
    },
    "FN-DSA": {
        "fips_standard": "FIPS 206 (draft, not yet finalized as of this writing)",
        "based_on": "FALCON",
        "purpose": "Digital signatures - compact size, NTRU lattice-based",
        "hardness_assumption": "NTRU lattice problems",
        "status": "Standard published but implementation guidance still developing",
    },
    "HQC": {
        "purpose": "Key Encapsulation Mechanism - backup to ML-KEM",
        "selected": "2025",
        "hardness_assumption": "Code-based cryptography (structurally different from lattice-based ML-KEM)",
        "note": "Selected specifically as a structurally different backup - if a future breakthrough attacks lattice-based schemes, HQC's code-based foundation would be unaffected",
    },
}

QUANTUM_THREAT_TIMELINE_CONTEXT = {
    "harvest_now_decrypt_later": {
        "description": (
            "Adversaries can record encrypted traffic TODAY and decrypt it once a "
            "sufficiently powerful quantum computer exists, even years later. "
            "This means data requiring long-term confidentiality is already at "
            "risk from today's RSA/ECC-encrypted traffic, regardless of when a "
            "cryptographically-relevant quantum computer actually arrives."
        ),
        "relevance": "This is why organizations must begin PQC migration BEFORE large-scale quantum computers exist, not after.",
    },
    "regulatory_deadlines": {
        "NSA_CNSA_2.0": "Sets 2030 as the mandatory migration deadline for U.S. National Security Systems",
        "note": "Financial institutions are not currently bound by CNSA 2.0 directly, but regulators globally are expected to follow similar timelines given the systemic importance of financial infrastructure",
    },
}
