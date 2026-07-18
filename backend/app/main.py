"""
QFT Bank - Enterprise Quantum Computing Platform
Main FastAPI application entry point.

Module routers (quantum, optimization, algorithms, dashboard, pqc)
get included here as each one is built. For now, just a health check
to prove the container, database, and redis are all wired correctly.
"""

from fastapi import FastAPI
from datetime import datetime
from app.quantum.router import router as quantum_router
from app.algorithms.router import router as algorithms_router
from app.optimization.router import router as optimization_router
from app.dashboard.router import router as dashboard_router
app = FastAPI(
    title="QFT Bank Quantum Computing Platform",
    description="Enterprise Quantum Computing Platform - EduQual L6 Capstone (ANPP-OP)",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "service": "QFT Quantum Computing Platform",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.get("/health")
def health_check():
    """Basic liveness check. Extend later to also ping Postgres/Redis."""
    return {"status": "healthy"}
app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"])
app.include_router(algorithms_router, prefix="/api/algorithms", tags=["Quantum Algorithms"])
app.include_router(optimization_router, prefix="/api/optimization", tags=["Portfolio Optimization"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Executive Dashboard"])
# Future module routers will be included like this, one at a time:
# from app.quantum.router import router as quantum_router
# app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"])
