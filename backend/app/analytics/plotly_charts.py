"""
Interactive Plotly visualisations for market analytics.

DESIGN (for the viva) - three charting technologies, three distinct jobs:
- React SVG (client-side): lightweight inline charts embedded in the UI,
  no server round-trip, rendered from JSON the API already returns.
- Matplotlib (server-side, market_analytics.py): static PNG raster output
  for EXPORTED artifacts - report images, PDF embedding. Fixed snapshot.
- Plotly (this module): figure JSON hydrated by the frontend into an
  INTERACTIVE chart with hover tooltips, zoom, pan, and legend toggling.
  This is the exploratory-analysis workflow - an analyst interrogating a
  risk/return surface, not reading a fixed report image.

The distinction is real: a PDF cannot zoom, and an interactive chart
cannot be embedded in a printed report.
"""

import json
from typing import Any, Dict

import plotly.graph_objects as go

from app.analytics.market_analytics import market_dataframe


def risk_return_figure(num_assets: int, seed: int = 42) -> go.Figure:
    """
    Build an interactive risk/return scatter for a simulated market.

    Each asset is a point positioned by volatility (x) and expected return (y),
    colour-scaled by its return/risk ratio so the most capital-efficient assets
    are visually obvious without reading the underlying numbers.
    """
    df = market_dataframe(num_assets, seed=seed)

    # Plotly 6.x binary-encodes NumPy arrays / Pandas Series into
    # {"dtype": ..., "bdata": ...} blobs. Compact, and react-plotly.js
    # reads them fine - but it makes this REST response opaque to any
    # other API consumer and unreadable in the Swagger docs. Converting
    # to plain lists here keeps the public contract plain JSON arrays.
    volatility = df["volatility"].tolist()
    expected_return = df["expected_return"].tolist()
    asset_names = df["asset"].tolist()
    return_risk_ratio = df["return_risk_ratio"].tolist()

    figure = go.Figure(
        data=[
            go.Scatter(
                x=volatility,
                y=expected_return,
                mode="markers+text",
                text=asset_names,
                textposition="top center",
                textfont=dict(color="#cbd5e0", size=10),
                customdata=return_risk_ratio,
                marker=dict(
                    size=16,
                    color=return_risk_ratio,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(
                        title=dict(text="Return / Risk", font=dict(color="#cbd5e0")),
                        tickfont=dict(color="#a0aec0"),
                    ),
                    line=dict(width=1.5, color="#9f7aea"),
                ),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Expected return: %{y:.4f}<br>"
                    "Volatility (risk): %{x:.4f}<br>"
                    "Return/risk ratio: %{customdata:.4f}"
                    "<extra></extra>"
                ),
            )
        ]
    )

    figure.update_layout(
        title=dict(
            text="Simulated Market: Risk vs Return (Interactive)",
            font=dict(color="#ffffff", size=15),
        ),
        xaxis=dict(
            title=dict(text="Risk (volatility)", font=dict(color="#cbd5e0")),
            gridcolor="#2d3748",
            tickfont=dict(color="#a0aec0"),
            zeroline=False,
        ),
        yaxis=dict(
            title=dict(text="Expected return", font=dict(color="#cbd5e0")),
            gridcolor="#2d3748",
            tickfont=dict(color="#a0aec0"),
            zeroline=False,
        ),
        paper_bgcolor="#1a202c",
        plot_bgcolor="#1a202c",
        font=dict(color="#e2e8f0"),
        margin=dict(l=70, r=40, t=60, b=60),
        hovermode="closest",
    )

    return figure


def risk_return_figure_json(num_assets: int, seed: int = 42) -> Dict[str, Any]:
    """
    Serialise the figure to plain JSON for transport to the frontend.

    Plotly's own encoder is used deliberately: the figure carries NumPy
    arrays and Pandas Series, which the stdlib JSON encoder cannot handle.

    Note that the NumPy/Pandas -> plain-list conversion happens upstream
    in ``risk_return_figure``, not here: Plotly binary-encodes array-likes
    at figure construction, so serialisation options alone cannot undo it.
    """
    figure = risk_return_figure(num_assets, seed=seed)
    return json.loads(figure.to_json())
