"""
Interactive Plotly dashboard (standalone HTML + reusable figure for Streamlit).

Uses results.csv (clusters) when present; subsamples large datasets for scatter performance.
"""

from __future__ import annotations

import json
import os
from typing import Any, Optional

import pandas as pd

from utils.currency import (
    cost_per_day_axis_label,
    get_currency_code,
    price_axis_label,
)
from utils.env_loader import load_project_dotenv
from utils.pipeline_paths import analytics_input_path
from visualization.express_charts import apply_chart_theme

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_HTML = os.path.join(ROOT_DIR, "output", "dashboard.html")
MAX_SCATTER_POINTS = 20_000


def build_dashboard_figure(
    data_path: Optional[str] = None,
    project_root: Optional[str] = None,
) -> Any:
    """
    Build the main Plotly figure. Used by HTML export and the Streamlit web app.
    """
    root = project_root or ROOT_DIR
    load_project_dotenv(root)
    path = data_path or analytics_input_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No data at {path}. Run the pipeline first.")

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise ImportError("Install plotly: pip install plotly") from exc

    insights_dir = os.path.join(root, "output", "insights")
    output_dir = os.path.join(root, "output")
    results_csv = os.path.join(output_dir, "results.csv")
    price_rating_json = os.path.join(insights_dir, "price_vs_rating.json")

    df = pd.read_csv(path, encoding="utf-8")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce").replace(0, 1.0).fillna(1.0)
    if "cost_per_day" not in df.columns:
        df["cost_per_day"] = (df["price"] / df["duration"]).replace([float("inf"), float("-inf")], pd.NA)

    n_rows = len(df)
    cur = get_currency_code()

    popular_path = os.path.join(insights_dir, "popular_destinations.csv")
    if os.path.isfile(popular_path):
        popular = pd.read_csv(popular_path, encoding="utf-8").head(18)
    else:
        popular = (
            df.groupby("location", as_index=False)
            .agg(listings=("name", "count"))
            .sort_values("listings", ascending=False)
            .head(18)
        )

    cluster_counts = None
    if os.path.isfile(results_csv):
        try:
            res = pd.read_csv(results_csv, encoding="utf-8")
            if "cluster_label" in res.columns:
                cluster_counts = res["cluster_label"].value_counts().reset_index()
                cluster_counts.columns = ["tier", "count"]
        except (OSError, pd.errors.EmptyDataError):
            pass

    corr_txt = ""
    if os.path.isfile(price_rating_json):
        with open(price_rating_json, encoding="utf-8") as f:
            pr = json.load(f)
        c = pr.get("pearson_correlation_price_rating")
        if c is not None and c == c:
            corr_txt = f"Pearson ρ (price vs rating) = {c:.3f} · n = {pr.get('n_points', '—')}"

    fig = make_subplots(
        rows=3,
        cols=2,
        subplot_titles=(
            "Top destinations (count)",
            "Price tier (K-means clusters)",
            f"Price vs rating ({cur})",
            f"Cost per day ({cur})",
            "Rating distribution",
            "Review sentiment (compound)",
        ),
        specs=[
            [{"type": "bar"}, {"type": "bar"}],
            [{"type": "scattergl"}, {"type": "histogram"}],
            [{"type": "histogram"}, {"type": "histogram"}],
        ],
        vertical_spacing=0.09,
        horizontal_spacing=0.07,
    )

    green_bar = popular["listings"]
    fig.add_trace(
        go.Bar(
            x=popular["location"],
            y=popular["listings"],
            marker=dict(
                color=green_bar,
                colorscale=[[0, "#1b4332"], [0.5, "#40916c"], [1, "#95d5b2"]],
                showscale=False,
            ),
            name="Listings",
            showlegend=False,
        ),
        row=1,
        col=1,
    )

    if cluster_counts is not None and not cluster_counts.empty:
        palette = {
            "budget": "#52b788",
            "mid-range": "#f4d35e",
            "premium": "#c084fc",
            "unclassified": "#94a3b8",
        }
        colors = [palette.get(str(t).lower(), "#64748b") for t in cluster_counts["tier"]]
        fig.add_trace(
            go.Bar(
                x=cluster_counts["tier"],
                y=cluster_counts["count"],
                marker_color=colors,
                name="Clusters",
                showlegend=False,
            ),
            row=1,
            col=2,
        )
    else:
        fig.add_trace(
            go.Bar(
                x=["(no cluster file)"],
                y=[0],
                marker_color="#475569",
                showlegend=False,
                hovertemplate="Run pipeline through clustering<extra></extra>",
            ),
            row=1,
            col=2,
        )

    sub = df.dropna(subset=["price", "rating"])
    if len(sub) > MAX_SCATTER_POINTS:
        sub = sub.sample(MAX_SCATTER_POINTS, random_state=42)
    hover = sub["name"].astype(str) if "name" in sub.columns else sub.index.astype(str)
    fig.add_trace(
        go.Scattergl(
            x=sub["price"],
            y=sub["rating"],
            mode="markers",
            marker=dict(
                size=7,
                color=sub["rating"],
                colorscale=[[0, "#1b4332"], [0.5, "#40916c"], [1, "#d8f3dc"]],
                opacity=0.45,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Rating", side="right", font=dict(color="#f5f0e6", size=11)),
                    tickfont=dict(color="#f5f0e6"),
                ),
            ),
            text=hover,
            hovertemplate=f"%{{text}}<br>{cur} price: %{{x:.2f}}<br>Rating: %{{y:.2f}}<extra></extra>",
            name="Listings",
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    cpd = pd.to_numeric(df["cost_per_day"], errors="coerce").dropna()
    if len(cpd) > 0:
        fig.add_trace(
            go.Histogram(
                x=cpd,
                nbinsx=min(50, max(20, int(len(cpd) ** 0.5))),
                marker_color="#52b788",
                name="cpd",
                showlegend=False,
            ),
            row=2,
            col=2,
        )

    fig.add_trace(
        go.Histogram(
            x=df["rating"].dropna(),
            nbinsx=min(40, max(15, int(len(df) ** 0.25))),
            marker_color="#74c69d",
            name="rating",
            showlegend=False,
        ),
        row=3,
        col=1,
    )

    if "sentiment_compound" in df.columns:
        sc = df["sentiment_compound"].dropna()
        if len(sc) == 0:
            sc = pd.Series([0.0])
        fig.add_trace(
            go.Histogram(
                x=sc,
                nbinsx=30,
                marker_color="#ee964b",
                name="sentiment",
                showlegend=False,
            ),
            row=3,
            col=2,
        )
    else:
        fig.add_trace(
            go.Histogram(x=[], nbinsx=1, marker_color="#475569", showlegend=False),
            row=3,
            col=2,
        )

    title = (
        f"Tourism analytics dashboard <span style='font-size:13px;color:#c4bdb0'>"
        f"({n_rows:,} listings · prices in {cur})</span>"
    )
    if corr_txt:
        title += f"<br><span style='font-size:12px;color:#95d5b2'>{corr_txt}</span>"

    fig.update_layout(title_text=title, height=1180)
    fig.update_xaxes(tickangle=35, row=1, col=1)
    fig.update_xaxes(title_text=price_axis_label(), row=2, col=1)
    fig.update_yaxes(title_text="Rating", row=2, col=1)
    fig.update_xaxes(title_text=cost_per_day_axis_label(), row=2, col=2)
    fig.update_xaxes(title_text="Rating", row=3, col=1)
    fig.update_xaxes(title_text="Compound score", row=3, col=2)

    fig = apply_chart_theme(fig)
    fig.update_layout(
        height=1180,
        margin=dict(t=100, l=56, r=36, b=52),
    )
    return fig


def build_dashboard(data_path=None, output_html: str = OUTPUT_HTML) -> str:
    fig = build_dashboard_figure(data_path=data_path)
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    fig.write_html(output_html, include_plotlyjs="cdn", full_html=True)
    print(f"[dashboard] Wrote {output_html}")
    return output_html


if __name__ == "__main__":
    build_dashboard()
