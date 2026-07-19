"""
Database models (schema) for execution history persistence.

DESIGN CHOICE: a single unified `executions` table for all modules rather
than four separate tables. Every module's history record shares the same
core shape (an id, a timestamp, which module/type it was, and a JSON blob
of the full result), so one table with a `module` discriminator column is
simpler, easier to query for the dashboard's cross-module views, and avoids
four near-identical tables. The full per-execution detail is stored as JSON,
which suits results whose exact shape differs between algorithms.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from datetime import datetime, timezone

from app.database.connection import Base


class ExecutionRecord(Base):
    __tablename__ = "executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(64), unique=True, index=True, nullable=False)
    module = Column(String(64), index=True, nullable=False)  # e.g. "quantum_circuits", "algorithms"
    subtype = Column(String(64), nullable=True)  # e.g. "grover", "vqe" - null for modules with no subtype
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    result_json = Column(JSON, nullable=False)  # full result payload

    def to_summary(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "module": self.module,
            "subtype": self.subtype,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }
