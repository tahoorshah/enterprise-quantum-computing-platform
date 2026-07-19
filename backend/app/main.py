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
from app.pqc.router import router as pqc_router
from app.database.connection import init_db
from app.database import persistence
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
app = FastAPI(
    title="QFT Bank Quantum Computing Platform",
    description="Enterprise Quantum Computing Platform - EduQual L6 Capstone (ANPP-OP)",
    version="0.1.0",
)
init_db()

Instrumentator().instrument(app).expose(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Basic liveness check. Also reports which storage backend is active."""
    return {"status": "healthy", "storage_backend": persistence.storage_backend()}


app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"])
app.include_router(algorithms_router, prefix="/api/algorithms", tags=["Quantum Algorithms"])
app.include_router(optimization_router, prefix="/api/optimization", tags=["Portfolio Optimization"])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Executive Dashboard"])
app.include_router(pqc_router, prefix="/api/pqc", tags=["Post-Quantum Cryptography"])

# Future module routers will be included like this, one at a time:
# from app.quantum.router import router as quantum_router
# app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"])
