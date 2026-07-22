"""
Market analytics helpers - Pandas for structured tabular market data,
Matplotlib for server-side static chart generation (risk/return scatter).

DESIGN (for the viva):
- Pandas turns the raw simulated market arrays (returns, volatilities,
  correlations) into a labelled DataFrame - the right tool for tabular
  financial data, cleaner than carrying parallel NumPy arrays, and easy
  to summarise/serialise for reports.
- Matplotlib renders a static risk-return scatter server-side, returned
  as a base64 PNG. This is for EXPORTED artifacts (report images / PDFs),
  distinct from the interactive SVG charts the React UI draws client-side.
"""

import io
import base64
from typing import List, Dict

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")  # headless backend - no display needed on the server
import matplotlib.pyplot as plt

from app.optimization.portfolio import generate_simulated_market_data


def market_dataframe(num_assets: int, seed: int = 42) -> pd.DataFrame:
    """
    Build a labelled Pandas DataFrame of the simulated market: one row per
    asset with expected return, volatility, and mean correlation to others.
    """
    names, expected_returns, covariance = generate_simulated_market_data(num_assets, seed=seed)
    volatilities = np.sqrt(np.diag(covariance))

    outer_vol = np.outer(volatilities, volatilities)
    with np.errstate(divide="ignore", invalid="ignore"):
        correlation = np.where(outer_vol > 0, covariance / outer_vol, 0.0)

    n = num_assets
    mean_corr = [
        float(np.mean([correlation[i, j] for j in range(n) if j != i])) if n > 1 else 0.0
        for i in range(n)
    ]

    df = pd.DataFrame({
        "asset": names,
        "expected_return": np.round(expected_returns, 4),
        "volatility": np.round(volatilities, 4),
        "mean_correlation": np.round(mean_corr, 4),
    })
    # a simple return-per-unit-risk column, a genuine analytical addition
    df["return_risk_ratio"] = np.round(df["expected_return"] / df["volatility"], 4)
    return df


def market_summary(num_assets: int, seed: int = 42) -> Dict:
    """
    Pandas-powered summary statistics of the market - the kind of describe()
    output an analyst would want. Returned as JSON-serialisable records.
    """
    df = market_dataframe(num_assets, seed=seed)
    desc = df[["expected_return", "volatility", "mean_correlation", "return_risk_ratio"]].describe()
    return {
        "assets": df.to_dict(orient="records"),
        "summary_stats": {
            stat: {col: round(float(desc.loc[stat, col]), 4) for col in desc.columns}
            for stat in ["mean", "std", "min", "max"]
        },
        "highest_return_asset": df.loc[df["expected_return"].idxmax(), "asset"],
        "lowest_risk_asset": df.loc[df["volatility"].idxmin(), "asset"],
        "best_return_risk_asset": df.loc[df["return_risk_ratio"].idxmax(), "asset"],
    }


def risk_return_chart_base64(num_assets: int, seed: int = 42) -> str:
    """
    Generate a static risk-return scatter with Matplotlib, returned as a
    base64-encoded PNG (data URI body). For embedding in exported reports.
    """
    df = market_dataframe(num_assets, seed=seed)

    fig, ax = plt.subplots(figsize=(7, 5), dpi=100)
    fig.patch.set_facecolor("#1a202c")
    ax.set_facecolor("#1a202c")

    ax.scatter(df["volatility"], df["expected_return"],
               s=140, c="#4f8cff", edgecolors="#9f7aea", linewidths=1.5, zorder=3)

    for _, row in df.iterrows():
        ax.annotate(row["asset"], (row["volatility"], row["expected_return"]),
                    textcoords="offset points", xytext=(8, 4),
                    color="#cbd5e0", fontsize=9)

    ax.set_xlabel("Risk (volatility)", color="#cbd5e0")
    ax.set_ylabel("Expected return", color="#cbd5e0")
    ax.set_title("Simulated Market: Risk vs Return", color="#ffffff", fontsize=13)
    ax.tick_params(colors="#a0aec0")
    for spine in ax.spines.values():
        spine.set_color("#2d3748")
    ax.grid(True, color="#2d3748", linestyle="--", linewidth=0.5, zorder=0)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
