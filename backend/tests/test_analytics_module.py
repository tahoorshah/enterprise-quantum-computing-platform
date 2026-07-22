"""Tests for the Market Analytics module (Pandas + Matplotlib)."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_market_analytics_returns_labelled_table():
    r = client.get("/api/analytics/market/5")
    assert r.status_code == 200
    body = r.json()
    assert len(body["assets"]) == 5
    # each asset row has the expected Pandas-derived columns
    cols = set(body["assets"][0].keys())
    assert {"asset", "expected_return", "volatility", "mean_correlation", "return_risk_ratio"} <= cols
    assert "summary_stats" in body
    assert "highest_return_asset" in body


def test_market_analytics_chart_returns_png_base64():
    r = client.get("/api/analytics/market/5/chart")
    assert r.status_code == 200
    body = r.json()
    assert body["format"] == "image/png;base64"
    # a real PNG in base64 starts with iVBOR
    assert body["image_base64"].startswith("iVBOR")


def test_market_analytics_rejects_out_of_range():
    assert client.get("/api/analytics/market/1").status_code == 422
    assert client.get("/api/analytics/market/50").status_code == 422
