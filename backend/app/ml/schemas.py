"""Pydantic schemas for Module 7 - Classical ML vs Quantum Optimization."""

from pydantic import BaseModel, Field
from typing import Dict, Any


class MLComparisonRequest(BaseModel):
    num_assets: int = Field(..., ge=3, le=8, description="Number of simulated assets (capped at 8, matches Module 2 brute-force feasibility)")
    budget: int = Field(..., ge=1, description="Exact number of assets to select (must be less than num_assets)")
    risk_aversion: float = Field(default=0.5, ge=0.0, le=5.0, description="Higher = weights variance more heavily vs return")
    penalty_weight: float = Field(default=2.0, ge=0.1, le=10.0, description="Strength of the 'select exactly budget assets' constraint in the QUBO label generation")
    num_scenarios: int = Field(default=60, ge=20, le=200, description="Number of distinct simulated markets used to build the training set")
    eval_seed: int = Field(default=42, description="Seed for the fresh evaluation market the trained model is tested on")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"num_assets": 5, "budget": 2, "num_scenarios": 60, "eval_seed": 42}
            ]
        }
    }


class MLComparisonResult(BaseModel):
    execution_id: str
    timestamp: str
    result: Dict[str, Any]
