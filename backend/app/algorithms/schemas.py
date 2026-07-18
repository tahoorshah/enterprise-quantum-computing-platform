"""Pydantic schemas for Module 3 - Quantum Algorithm Demonstration Platform."""

from pydantic import BaseModel, Field
from typing import List, Tuple, Dict, Any


class GroverRequest(BaseModel):
    num_qubits: int = Field(..., ge=1, le=6, description="Number of qubits (search space = 2^n, kept small for reasonable runtime)")
    marked_state: str = Field(..., description="The target bitstring to search for, e.g. '101'")
    shots: int = Field(default=1024, ge=1, le=10000)


class QFTRequest(BaseModel):
    num_qubits: int = Field(..., ge=1, le=6)
    input_state: str = Field(..., description="Basis state to encode before applying QFT, e.g. '101'")
    shots: int = Field(default=1024, ge=1, le=10000)


class QAOARequest(BaseModel):
    edges: List[Tuple[int, int]] = Field(..., description="Graph edges for Max-Cut, e.g. [[0,1],[1,2],[0,2]]")
    num_nodes: int = Field(..., ge=2, le=6)
    p_layers: int = Field(default=1, ge=1, le=3, description="Number of QAOA layers (higher = more expressive, slower)")
    shots: int = Field(default=512, ge=1, le=5000)
    max_iterations: int = Field(default=30, ge=1, le=100)


class VQERequest(BaseModel):
    num_qubits: int = Field(..., ge=1, le=6)
    max_iterations: int = Field(default=50, ge=1, le=200)


class AlgorithmResult(BaseModel):
    """Generic wrapper - all four algorithms return different-shaped data,
    so we keep the actual result as a flexible dict rather than forcing
    one rigid schema onto genuinely different algorithms."""
    algorithm: str
    execution_id: str
    timestamp: str
    result: Dict[str, Any]
