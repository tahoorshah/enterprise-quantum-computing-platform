"""Tests for Module 7 - Classical ML vs Quantum Optimization."""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_ml_compare_runs_and_returns_expected_shape():
    r = client.post("/api/ml/compare", json={
        "num_assets": 5, "budget": 2, "num_scenarios": 60, "eval_seed": 42
    })
    assert r.status_code == 200
    body = r.json()
    assert "execution_id" in body
    assert "result" in body

    result = body["result"]
    # training block present with honest accuracy fields
    assert "training" in result
    assert 0.0 <= result["training"]["train_accuracy"] <= 1.0
    assert 0.0 <= result["training"]["test_accuracy"] <= 1.0
    # feature importances sum to ~1 (RandomForest property)
    fi = result["training"]["feature_importance"]
    assert abs(sum(fi.values()) - 1.0) < 0.05
    # comparison + exact optimum present
    assert "comparison" in result
    assert "ml_matched_exact_optimum" in result["comparison"]
    assert "exact_optimum" in result
    assert "bitstring" in result["exact_optimum"]


def test_ml_compare_rejects_budget_ge_num_assets():
    r = client.post("/api/ml/compare", json={"num_assets": 4, "budget": 4})
    assert r.status_code == 422


def test_ml_history_records_run():
    # run one, then confirm it appears in history
    client.post("/api/ml/compare", json={"num_assets": 4, "budget": 2, "num_scenarios": 40})
    r = client.get("/api/ml/history")
    assert r.status_code == 200
    hist = r.json()
    assert isinstance(hist, list)
    assert len(hist) >= 1
    # each summary has the expected keys
    entry = hist[0]
    for key in ("execution_id", "timestamp", "num_assets", "ml_matched_optimum", "test_accuracy"):
        assert key in entry


def test_ml_budget_enforced_selection_count_matches_budget():
    # the budget-enforced bitstring must select exactly `budget` assets
    r = client.post("/api/ml/compare", json={
        "num_assets": 6, "budget": 3, "num_scenarios": 50, "eval_seed": 7
    })
    assert r.status_code == 200
    bitstring = r.json()["result"]["ml_prediction"]["budget_enforced_bitstring"]
    assert bitstring.count("1") == 3
