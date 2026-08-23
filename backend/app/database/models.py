"""
Database schema: users, execution_runs (audit header), execution_results (payload).

DESIGN: execution_runs and execution_results are split so the audit trail
(who ran what, when, which module, how long it took) can be retained
independently of the heavy JSON payload — supports a retention policy where
old result_json rows are purged while the audit header stays for compliance.
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(32), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    runs = relationship("ExecutionRun", back_populates="user")


class ExecutionRun(Base):
    __tablename__ = "execution_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    module = Column(String(64), index=True, nullable=False)
    subtype = Column(String(64), nullable=True)
    status = Column(String(16), default="success", nullable=False)
    duration_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", back_populates="runs")
    result = relationship("ExecutionResult", back_populates="run", uselist=False, cascade="all, delete-orphan")

    def to_summary(self) -> dict:
        return {
            "execution_id": self.execution_id,
            "module": self.module,
            "subtype": self.subtype,
            "status": self.status,
            "duration_ms": self.duration_ms,
            "user": self.user.username if self.user else None,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }


class ExecutionResult(Base):
    __tablename__ = "execution_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("execution_runs.id"), unique=True, nullable=False, index=True)
    result_json = Column(JSON, nullable=False)

    run = relationship("ExecutionRun", back_populates="result")
