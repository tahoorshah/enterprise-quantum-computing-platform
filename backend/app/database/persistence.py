"""
Unified persistence layer with graceful in-memory fallback.

Writes an ExecutionRun (audit header, with actor from the request context
and measured duration) plus an ExecutionResult (payload) per call, or falls
back to in-memory dicts if the database is unreachable.
"""
import logging
from typing import Optional, List
from datetime import datetime, timezone

from app.database import connection
from app.auth.context import get_current_username

logger = logging.getLogger("qft.persistence")

_memory_store: dict = {}


def _memory_save(module, execution_id, subtype, result_json, timestamp, username, duration_ms):
    _memory_store.setdefault(module, {})[execution_id] = {
        "execution_id": execution_id,
        "module": module,
        "subtype": subtype,
        "user": username,
        "duration_ms": duration_ms,
        "timestamp": timestamp,
        "result_json": result_json,
    }


def save_execution(
    module: str,
    execution_id: str,
    result_json: dict,
    subtype: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    username = get_current_username()

    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRun, ExecutionResult, User
            user_id = None
            if username:
                user = session.query(User).filter(User.username == username).first()
                user_id = user.id if user else None

            run = ExecutionRun(
                execution_id=execution_id,
                user_id=user_id,
                module=module,
                subtype=subtype,
                duration_ms=duration_ms,
            )
            session.add(run)
            session.flush()  # get run.id before commit
            session.add(ExecutionResult(run_id=run.id, result_json=result_json))
            session.commit()
            return
        except Exception as e:
            logger.warning("DB save failed (%s); falling back to memory for this record.", type(e).__name__)
            if session:
                session.rollback()
        finally:
            if session:
                session.close()

    _memory_save(module, execution_id, subtype, result_json, timestamp, username, duration_ms)


def get_execution(module: str, execution_id: str) -> Optional[dict]:
    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRun
            run = (
                session.query(ExecutionRun)
                .filter(ExecutionRun.execution_id == execution_id, ExecutionRun.module == module)
                .first()
            )
            if run and run.result:
                d = run.to_summary()
                d["result_json"] = run.result.result_json
                return d
            return None
        except Exception as e:
            logger.warning("DB read failed (%s); checking memory.", type(e).__name__)
        finally:
            if session:
                session.close()
    return _memory_store.get(module, {}).get(execution_id)


def list_executions(module: str) -> List[dict]:
    if connection.DATABASE_AVAILABLE:
        session = connection.get_session()
        try:
            from app.database.models import ExecutionRun
            runs = (
                session.query(ExecutionRun)
                .filter(ExecutionRun.module == module)
                .order_by(ExecutionRun.created_at.desc())
                .all()
            )
            out = []
            for r in runs:
                d = r.to_summary()
                d["result_json"] = r.result.result_json if r.result else None
                out.append(d)
            return out
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
    if not connection.DATABASE_AVAILABLE:
        return "in-memory (fallback)"
    try:
        return connection.engine.dialect.name if connection.engine else "database"
    except Exception:
        return "database"
