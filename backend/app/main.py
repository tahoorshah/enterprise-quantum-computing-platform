"""
QFT Bank - Enterprise Quantum Computing Platform
Main FastAPI application entry point.

All six module routers (quantum circuits, portfolio optimization,
algorithms, executive dashboard, PQC readiness, multi-framework demo)
are included below. The app initialises the database (with graceful
in-memory fallback), exposes Prometheus metrics, and provides a /health
endpoint that reports the active storage backend.
"""

from fastapi import FastAPI
from datetime import datetime, timezone
from app.quantum.router import router as quantum_router
from app.algorithms.router import router as algorithms_router
from app.optimization.router import router as optimization_router
from app.dashboard.router import router as dashboard_router
from app.pqc.router import router as pqc_router
from app.database.connection import init_db
from app.database import persistence
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from app.frameworks.router import router as frameworks_router
from app.ml.router import router as ml_router
from app.analytics.router import router as analytics_router
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
        "timestamp": datetime.now(timezone.utc).isoformat(),
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
app.include_router(frameworks_router, prefix="/api/frameworks", tags=["Multi-Framework Demo"])
app.include_router(ml_router, prefix="/api/ml", tags=["Machine Learning"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Market Analytics"])
