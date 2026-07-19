"""Pydantic schemas for Module 5 - Post-Quantum Cryptography Readiness Platform."""

from pydantic import BaseModel, Field
from typing import Optional


class InventoryScanRequest(BaseModel):
    seed: int = Field(default=42, description="Random seed for reproducible simulated inventory")


class QuantumThreatDemoRequest(BaseModel):
    theta: float = Field(..., ge=0, lt=1, description="Phase to estimate, in [0, 1). E.g. 0.375")
    num_counting_qubits: int = Field(default=4, ge=1, le=8, description="Precision of the estimate: 1/2^n")
    shots: int = Field(default=1024, ge=64, le=10000)
