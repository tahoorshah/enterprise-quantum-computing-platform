"""Pydantic schemas for Module 2 - Financial Portfolio Optimization Platform."""
from pydantic import BaseModel, Field
from typing import Dict, Any


class PortfolioOptimizationRequest(BaseModel):
    num_assets: int = Field(..., ge=3, le=8, description="Number of simulated assets (capped at 8 for brute-force comparison feasibility)")
    budget: int = Field(..., ge=1, description="Exact number of assets to select (must be less than num_assets)")
    risk_aversion: float = Field(default=0.5, ge=0.0, le=5.0, description="Higher = more risk-averse (weights variance more heavily vs return)")
    penalty_weight: float = Field(default=2.0, ge=0.1, le=10.0, description="How strongly to enforce the 'select exactly `budget` assets' constraint")
    shots: int = Field(default=512, ge=64, le=5000)
    max_iterations: int = Field(default=30, ge=5, le=100)
    p_layers: int = Field(default=1, ge=1, le=3)
    seed: int = Field(default=42, description="Random seed for reproducible simulated market data")
    trials: int = Field(default=5, ge=1, le=20, description="Independent QAOA runs. QAOA is stochastic, so repeated evaluation gives a reliability rate instead of a single outcome.")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"num_assets": 4, "budget": 2, "risk_aversion": 0.5, "shots": 512, "max_iterations": 30, "trials": 5}
            ]
        }
    }


class PortfolioOptimizationResult(BaseModel):
    execution_id: str
    timestamp: str
    result: Dict[str, Any]
