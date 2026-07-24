import { useState, useEffect, useRef } from "react";
import Plotly from "plotly.js-basic-dist";
import { api } from "../api";

/**
 * Market Analytics screen.
 *
 * Deliberately surfaces all THREE charting technologies side by side, because
 * each answers a different question:
 *
 *   1. Pandas summary table  - the numbers themselves, describe()-style stats.
 *   2. Matplotlib static PNG - server-rendered raster, the artifact that goes
 *                              into an exported PDF report. Cannot be zoomed.
 *   3. Plotly interactive    - hover, zoom, pan. The exploratory tool an
 *                              analyst uses to interrogate the risk surface.
 *
 * NOTE ON THE PLOTLY INTEGRATION: react-plotly.js declares peer deps of
 * React <=18 and is not React 19 compatible, so rather than force-install a
 * mismatched wrapper we call Plotly's imperative API directly from an effect
 * and handle purge/cleanup ourselves. Fewer dependencies, full control over
 * the lifecycle.
 */
export default function Analytics() {
  const [numAssets, setNumAssets] = useState(6);
  const [seed, setSeed] = useState(42);

  const [summary, setSummary] = useState(null);
  const [pngB64, setPngB64] = useState(null);
  const [figure, setFigure] = useState(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const plotRef = useRef(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [s, png, interactive] = await Promise.all([
        api.marketAnalytics(numAssets, seed),
        api.marketChartPng(numAssets, seed),
        api.marketChartInteractive(numAssets, seed),
      ]);
      setSummary(s);
      setPngB64(png.image_base64);
      setFigure(interactive.figure);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Render / re-render the Plotly figure whenever new figure JSON arrives.
  useEffect(() => {
    const node = plotRef.current;
    if (!node || !figure) return;

    Plotly.newPlot(node, figure.data, figure.layout, {
      responsive: true,
      displaylogo: false,
      modeBarButtonsToRemove: ["select2d", "lasso2d"],
    });

    // Purge on unmount / figure change - Plotly attaches listeners and a
    // WebGL-ish context to the node; without this we leak on every reload.
    return () => Plotly.purge(node);
  }, [figure]);

  return (
    <div>
      <h2>Market Analytics</h2>
      <p className="subtitle">
        Pandas-structured market data with three complementary visualisation
        layers: tabular statistics, a static report image, and an interactive
        exploratory chart.
      </p>

      <div className="card">
        <div className="row">
          <label>
            Assets
            <input
              type="number"
              min="2"
              max="20"
              value={numAssets}
              onChange={(e) => setNumAssets(Number(e.target.value))}
            />
          </label>
          <label>
            Seed
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </label>
          <button onClick={load} disabled={loading}>
            {loading ? "Loading..." : "Generate Analytics"}
          </button>
        </div>
        <p className="subtitle">
          The seed makes every run reproducible - the same seed always yields
          the same simulated market.
        </p>
      </div>

      {error && <div className="card error">Error: {error}</div>}

      {summary && (
        <div className="card">
          <h3>1. Market Data (Pandas)</h3>
          <table className="data-table">
            <thead>
              <tr>
                <th>Asset</th>
                <th>Expected Return</th>
                <th>Volatility</th>
                <th>Mean Correlation</th>
                <th>Return / Risk</th>
              </tr>
            </thead>
            <tbody>
              {summary.assets.map((a) => (
                <tr key={a.asset}>
                  <td>{a.asset}</td>
                  <td>{a.expected_return}</td>
                  <td>{a.volatility}</td>
                  <td>{a.mean_correlation}</td>
                  <td>{a.return_risk_ratio}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <div className="row" style={{ marginTop: "1rem", flexWrap: "wrap" }}>
            <span className="pill">
              Highest return: <strong>{summary.highest_return_asset}</strong>
            </span>
            <span className="pill">
              Lowest risk: <strong>{summary.lowest_risk_asset}</strong>
            </span>
            <span className="pill">
              Best return/risk: <strong>{summary.best_return_risk_asset}</strong>
            </span>
          </div>
        </div>
      )}

      {figure && (
        <div className="card">
          <h3>2. Interactive Exploration (Plotly)</h3>
          <p className="subtitle">
            Hover a point for exact figures; drag to zoom; double-click to
            reset. Colour encodes return per unit of risk.
          </p>
          <div ref={plotRef} style={{ width: "100%", height: "460px" }} />
        </div>
      )}

      {pngB64 && (
        <div className="card">
          <h3>3. Static Report Image (Matplotlib)</h3>
          <p className="subtitle">
            Rendered server-side as a PNG. This is the artifact that gets
            embedded into an exported PDF report - fixed, printable, and
            identical for every reader.
          </p>
          <img
            src={`data:image/png;base64,${pngB64}`}
            alt="Risk versus return scatter chart"
            style={{ maxWidth: "100%", borderRadius: "6px" }}
          />
        </div>
      )}
    </div>
  );
}
