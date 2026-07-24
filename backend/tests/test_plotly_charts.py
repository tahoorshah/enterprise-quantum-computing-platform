"""
Tests for the interactive Plotly analytics layer.

These verify structural correctness (trace count, point count matching the
requested asset count) and - importantly - that the figure survives JSON
serialisation, since it carries NumPy/Pandas objects the stdlib encoder
would reject.
"""

from app.analytics.plotly_charts import risk_return_figure, risk_return_figure_json


def test_figure_has_exactly_one_scatter_trace():
    figure = risk_return_figure(4)
    assert len(figure.data) == 1
    assert figure.data[0].type == "scatter"


def test_point_count_matches_requested_asset_count():
    figure = risk_return_figure(5)
    assert len(figure.data[0].x) == 5
    assert len(figure.data[0].y) == 5
    assert len(figure.data[0].text) == 5


def test_figure_json_is_serialisable_and_well_formed():
    payload = risk_return_figure_json(3)
    assert "data" in payload
    assert "layout" in payload
    assert len(payload["data"][0]["x"]) == 3


def test_same_seed_produces_identical_figure_data():
    """Determinism matters: the demo must be reproducible in the viva."""
    a = risk_return_figure_json(4, seed=7)
    b = risk_return_figure_json(4, seed=7)
    assert a["data"][0]["x"] == b["data"][0]["x"]
    assert a["data"][0]["y"] == b["data"][0]["y"]
