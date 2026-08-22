"""
Every /api/* route now requires a JWT (main.py:
include_router(..., dependencies=[Depends(get_current_user)])).
test_auth.py specifically tests that mechanism and needs it left alone.
Every other test module (grover, portfolio, PQC, dashboard, etc.) is
testing business logic, not auth, so we override the auth dependency
for them rather than making every test log in first.
"""
import pytest
from app.main import app
from app.auth.security import get_current_user

_TEST_USER = {"username": "analyst", "role": "financial_analyst"}


@pytest.fixture(autouse=True)
def _bypass_auth_for_non_auth_tests(request):
    if request.module.__name__.endswith("test_auth"):
        yield
        return

    app.dependency_overrides[get_current_user] = lambda: _TEST_USER
    yield
    app.dependency_overrides.pop(get_current_user, None)
