"""
Every /api/* route now requires a JWT (main.py:
include_router(..., dependencies=[Depends(get_current_user)])).
test_auth.py specifically tests that mechanism against a real in-memory
SQLite database. Every other test module (grover, portfolio, PQC,
dashboard, etc.) is testing business logic, not auth, so we override the
auth dependency for them rather than making every test log in first.
"""
import os
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import connection
from app.main import app
from app.auth.security import get_current_user

_TEST_USER = {"username": "analyst", "role": "financial_analyst"}


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    # StaticPool pins the whole engine to one physical connection, so the
    # SQLite in-memory DB isn't wiped/recreated on every new connection.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _fk_pragma(dbapi_conn, _):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    from app.database import models  # noqa: F401
    connection.Base.metadata.create_all(bind=engine)
    connection.engine = engine
    connection.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    connection.DATABASE_AVAILABLE = True

    connection._seed_demo_users()
    yield


@pytest.fixture(autouse=True)
def _bypass_auth_for_non_auth_tests(request):
    if request.module.__name__.endswith("test_auth"):
        yield
        return

    app.dependency_overrides[get_current_user] = lambda: _TEST_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)
