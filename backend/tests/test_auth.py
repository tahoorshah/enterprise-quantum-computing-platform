"""Auth tests - closes Risk Register item #9 (no security test coverage)."""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_protected_route_rejects_missing_token():
    response = client.get("/api/dashboard/report")
    assert response.status_code == 401


def test_login_succeeds_with_correct_credentials():
    response = client.post(
        "/api/auth/login",
        data={"username": "analyst", "password": "changeme_demo_only"},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"


def test_login_rejects_wrong_password():
    response = client.post(
        "/api/auth/login",
        data={"username": "analyst", "password": "wrong"},
    )
    assert response.status_code == 401


def test_login_rejects_unknown_user():
    response = client.post(
        "/api/auth/login",
        data={"username": "nobody", "password": "irrelevant"},
    )
    assert response.status_code == 401


def test_protected_route_accepts_valid_token():
    login = client.post(
        "/api/auth/login",
        data={"username": "analyst", "password": "changeme_demo_only"},
    )
    token = login.json()["access_token"]
    response = client.get(
        "/api/dashboard/report",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200


def test_protected_route_rejects_garbage_token():
    response = client.get(
        "/api/dashboard/report",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401
