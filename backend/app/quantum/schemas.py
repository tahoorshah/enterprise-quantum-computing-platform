"""
Pydantic schemas for Module 1 - Quantum Circuit Design Platform.

These define exactly what shape of JSON the API accepts and returns.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# Gates supported and how many qubits + params each one needs.
# This is also used to VALIDATE incoming requests before touching Qiskit,
# so bad input fails with a clear error instead of a confusing Qiskit traceback.
SUPPORTED_GATES = {
    "h":    {"qubits": 1, "params": 0, "description": "Hadamard - creates superposition"},
    "x":    {"qubits": 1, "params": 0, "description": "Pauli-X - bit flip (quantum NOT)"},
    "y":    {"qubits": 1, "params": 0, "description": "Pauli-Y - bit and phase flip"},
    "z":    {"qubits": 1, "params": 0, "description": "Pauli-Z - phase flip"},
    "s":    {"qubits": 1, "params": 0, "description": "S gate - quarter phase rotation"},
    "t":    {"qubits": 1, "params": 0, "description": "T gate - eighth phase rotation"},
    "rx":   {"qubits": 1, "params": 1, "description": "Rotation around X-axis by theta"},
    "ry":   {"qubits": 1, "params": 1, "description": "Rotation around Y-axis by theta"},
    "rz":   {"qubits": 1, "params": 1, "description": "Rotation around Z-axis by theta"},
    "cx":   {"qubits": 2, "params": 0, "description": "CNOT - entangles two qubits"},
    "cz":   {"qubits": 2, "params": 0, "description": "Controlled-Z"},
    "swap": {"qubits": 2, "params": 0, "description": "Swaps the state of two qubits"},
    "ccx":  {"qubits": 3, "params": 0, "description": "Toffoli - controlled-controlled-NOT"},
}


class GateInstruction(BaseModel):
    """One gate to apply, e.g. {"gate": "h", "qubits": [0]}"""
    gate: str = Field(..., description=f"One of: {', '.join(SUPPORTED_GATES.keys())}")
    qubits: List[int] = Field(..., description="Qubit indices this gate acts on")
    params: Optional[List[float]] = Field(
        default=None,
        description="Angle(s) in radians, only needed for rx/ry/rz"
    )


class CircuitRequest(BaseModel):
    """Request body for building and running a circuit."""
    num_qubits: int = Field(..., ge=1, le=20, description="Number of qubits (max 20 to protect low-RAM machines)")
    gates: List[GateInstruction] = Field(..., min_length=1, description="Ordered list of gates to apply")
    shots: int = Field(default=1024, ge=1, le=10000, description="Number of measurement shots")
    measure_all: bool = Field(default=True, description="Measure all qubits at the end")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "num_qubits": 2,
                    "gates": [
                        {"gate": "h", "qubits": [0]},
                        {"gate": "cx", "qubits": [0, 1]}
                    ],
                    "shots": 1024,
                    "measure_all": True
                }
            ]
        }
    }


class CircuitResult(BaseModel):
    """Response returned after building and executing a circuit."""
    execution_id: str
    timestamp: datetime
    num_qubits: int
    gates_applied: List[GateInstruction]
    shots: int
    circuit_diagram_text: str
    counts: dict
    probabilities: dict
    execution_time_ms: float


class HistorySummary(BaseModel):
    """Lightweight summary shown in the history list endpoint."""
    execution_id: str
    timestamp: datetime
    num_qubits: int
    num_gates: int
    shots: int
