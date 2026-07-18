"""
QFT Bank - Enterprise Quantum Computing Platform
Main FastAPI application entry point.

Module routers (quantum, optimization, algorithms, dashboard, pqc)
get included here as each one is built. For now, just a health check
to prove the container, database, and redis are all wired correctly.
"""

from fastapi import FastAPI
from datetime import datetime

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


# Future module routers will be included like this, one at a time:
# from app.quantum.router import router as quantum_router
# app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"])
