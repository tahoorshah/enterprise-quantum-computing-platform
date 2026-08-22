"""
QFT Bank - Enterprise Quantum Computing Platform
Main FastAPI application entry point.

All six module routers (quantum circuits, portfolio optimization,
algorithms, executive dashboard, PQC readiness, multi-framework demo)
are included below. The app initialises the database (with graceful
in-memory fallback), exposes Prometheus metrics, and provides a /health
endpoint that reports the active storage backend.
"""

import os
from fastapi import FastAPI, Depends
from datetime import datetime, timezone
from app.auth.security import get_current_user
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
from app.auth.router import router as auth_router
app = FastAPI(
    title="QFT Bank Quantum Computing Platform",
    description="Enterprise Quantum Computing Platform - EduQual L6 Capstone (ANPP-OP)",
    version="0.1.0",
)
init_db()

Instrumentator().instrument(app).expose(app)
# Allowed frontend origins. Configurable via CORS_ORIGINS so this stays
# environment-aware (dev / EC2 demo / production) without a wildcard,
# which would defeat allow_credentials and is bad security practice for
# an Enterprise Capstone submission. Comma-separated list, e.g.:
#   CORS_ORIGINS=http://localhost:5173,http://203.0.113.10:5173
_cors_origins_env = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
_allowed_origins = [o.strip() for o in _cors_origins_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
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


app.include_router(auth_router)
app.include_router(quantum_router, prefix="/api/quantum", tags=["Quantum Circuits"], dependencies=[Depends(get_current_user)])
app.include_router(algorithms_router, prefix="/api/algorithms", tags=["Quantum Algorithms"], dependencies=[Depends(get_current_user)])
app.include_router(optimization_router, prefix="/api/optimization", tags=["Portfolio Optimization"], dependencies=[Depends(get_current_user)])
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Executive Dashboard"], dependencies=[Depends(get_current_user)])
app.include_router(pqc_router, prefix="/api/pqc", tags=["Post-Quantum Cryptography"], dependencies=[Depends(get_current_user)])
app.include_router(frameworks_router, prefix="/api/frameworks", tags=["Multi-Framework Demo"], dependencies=[Depends(get_current_user)])
app.include_router(ml_router, prefix="/api/ml", tags=["Machine Learning"], dependencies=[Depends(get_current_user)])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Market Analytics"], dependencies=[Depends(get_current_user)])
