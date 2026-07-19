"""
Unified persistence layer with graceful in-memory fallback.

Every module (quantum circuits, algorithms, optimization, pqc) routes its
history saving/loading through this single module. If the database is
available (DATABASE_AVAILABLE is True), records go to PostgreSQL. If not,
they go to a plain in-memory dict instead - so the platform keeps working
either way.
"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from app.database import connection

logger = logging.getLogger("qft.persistence")

# In-memory fallback store: module -> {execution_id -> record dict}
_memory_store: dict = {}


def _memory_save(module: str, execution_id: str, subtype: Optional[str], result_json: dict, timestamp: str):
    _memory_store.setdefault(module, {})[execution_id] = {
        "execution_id": execution_id,
        "module": module,
        "subtype": subtype,
        "timestamp": timestamp,
        "result_json": result_json,
    }


def save_execution(module: str, execution_id: str, result_json: dict, subtype: Optional[str] = None) -> None:
    """Persist one execution record - to DB if available, else in-memory."""
    timestamp = datetime.now(timezone.utc).isoformat()

    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRecord
            record = ExecutionRecord(
                execution_id=execution_id,
                module=module,
                subtype=subtype,
                result_json=result_json,
            )
            session.add(record)
            session.commit()
            return
        except Exception as e:
            logger.warning("DB save failed (%s); falling back to memory for this record.", type(e).__name__)
            if session:
                session.rollback()
            # fall through to memory save so the record isn't lost
        finally:
            if session:
                session.close()

    _memory_save(module, execution_id, subtype, result_json, timestamp)


def get_execution(module: str, execution_id: str) -> Optional[dict]:
    """Fetch one full execution record by id, or None if not found."""
    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRecord
            rec = (
                session.query(ExecutionRecord)
                .filter(ExecutionRecord.execution_id == execution_id, ExecutionRecord.module == module)
                .first()
            )
            if rec:
                return {
                    "execution_id": rec.execution_id,
                    "module": rec.module,
                    "subtype": rec.subtype,
                    "timestamp": rec.created_at.isoformat() if rec.created_at else None,
                    "result_json": rec.result_json,
                }
            return None
        except Exception as e:
            logger.warning("DB read failed (%s); checking memory.", type(e).__name__)
        finally:
            if session:
                session.close()

    return _memory_store.get(module, {}).get(execution_id)


def list_executions(module: str) -> List[dict]:
    """List all executions for a module, most recent first (summaries)."""
    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRecord
            recs = (
                session.query(ExecutionRecord)
                .filter(ExecutionRecord.module == module)
                .order_by(ExecutionRecord.created_at.desc())
                .all()
            )
            return [
                {
                    "execution_id": r.execution_id,
                    "module": r.module,
                    "subtype": r.subtype,
                    "timestamp": r.created_at.isoformat() if r.created_at else None,
                    "result_json": r.result_json,
                }
                for r in recs
            ]
        except Exception as e:
            logger.warning("DB list failed (%s); checking memory.", type(e).__name__)
        finally:
            if session:
                session.close()

    records = list(_memory_store.get(module, {}).values())
    records.sort(key=lambda r: r["timestamp"], reverse=True)
    return records


def count_executions(module: str) -> int:
    return len(list_executions(module))


def storage_backend() -> str:
    """Report which backend is active - useful for the dashboard/health to show."""
    if not connection.DATABASE_AVAILABLE:
        return "in-memory (fallback)"
    try:
        return connection.engine.dialect.name if connection.engine else "database"
    except Exception:
        return "database"
