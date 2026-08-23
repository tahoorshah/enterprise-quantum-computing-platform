"""
Database connection setup for PostgreSQL persistence.

DESIGN: graceful degradation. If the database is reachable at startup,
history is persisted to PostgreSQL. If it is NOT reachable (misconfigured,
down, or running outside Docker without a DB), the platform logs a warning
and falls back to in-memory storage instead of crashing. This means:
  - In production / Docker: real persistence across restarts.
  - In a bare local run or if the DB hiccups during a live demo: the app
    still works, just without cross-restart persistence.

The database URL comes from the DATABASE_URL environment variable (set in
.env / docker-compose), defaulting to a local Postgres if unset.
"""

import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("qft.database")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://qft_admin:changeme_local_dev_only@localhost:5432/qft_quantum_db",
)

Base = declarative_base()

# These get set by init_db(). If the DB is unreachable, they stay None and
# the history layer knows to use in-memory fallback.
engine = None
SessionLocal = None
DATABASE_AVAILABLE = False


def init_db() -> bool:
    """
    Try to connect to the database and create tables. Returns True if the
    database is available and ready, False if we should fall back to
    in-memory storage. Never raises - a DB problem must not crash the app.
    """
    global engine, SessionLocal, DATABASE_AVAILABLE

    try:
        engine = create_engine(DATABASE_URL, pool_pre_ping=True)
        # Actually test the connection - create_engine alone is lazy and
        # won't reveal a dead database until first use.
        with engine.connect() as conn:
            pass

        # Import models so they're registered on Base before create_all
        from app.database import models  # noqa: F401
        Base.metadata.create_all(bind=engine)

        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        DATABASE_AVAILABLE = True
        logger.info("Database connected: persistence ENABLED (PostgreSQL).")

        _seed_demo_users()
        return True

    except SQLAlchemyError as e:
        DATABASE_AVAILABLE = False
        logger.warning(
            "Database unavailable (%s). Falling back to IN-MEMORY storage. "
            "History will NOT persist across restarts.", type(e).__name__
        )
        return False
    except Exception as e:
        DATABASE_AVAILABLE = False
        logger.warning(
            "Unexpected error initializing database (%s). Falling back to "
            "IN-MEMORY storage.", type(e).__name__
        )
        return False


def get_session():
    """Return a new DB session, or None if the database isn't available."""
    if not DATABASE_AVAILABLE or SessionLocal is None:
        return None
    return SessionLocal()


def _seed_demo_users():
    """
    Insert the two demo accounts into the real users table if not already
    present. Replaces the old hardcoded-dict user store (Security
    Architecture gap): credentials are unchanged, but now backed by a
    real row with a primary key, usable as a foreign key for auditability.
    """
    from app.database.models import User
    from app.auth.security import _SEED_USERS, pwd_context

    session = SessionLocal()
    try:
        for u in _SEED_USERS:
            if not session.query(User).filter(User.username == u["username"]).first():
                session.add(User(
                    username=u["username"],
                    hashed_password=pwd_context.hash(u["password"]),
                    role=u["role"],
                ))
        session.commit()
    finally:
        session.close()
