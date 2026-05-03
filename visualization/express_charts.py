"""
Plotly Express figures for the Streamlit explorer tab.

Each function expects a pre-filtered dataframe with numeric price, rating, duration where applicable.
"""

from __future__ import annotations

import pandas as pd

try:
    import plotly.express as px
except ImportError:  # pragma: no cover
    px = None  # type: ignore


def ensure_plotly_express() -> None:
    if px is None:
        raise ImportError("plotly is required for express charts")


def apply_chart_theme(fig: object) -> object:
    """Light sage + charcoal — matches Streamlit beige / HIKE IT–style UI."""
    charcoal = "#3d3d3a"
    grid = "rgba(96, 140, 123, 0.18)"
    fig.update_layout(
        template="plotly_white",
        font=dict(family="Plus Jakarta Sans, Segoe UI, system-ui, sans-serif", size=12, color=charcoal),
        title=dict(font=dict(size=15, color=charcoal, family="Plus Jakarta Sans, Segoe UI, system-ui, sans-serif")),
        paper_bgcolor="rgba(255, 253, 208, 0.95)",
        plot_bgcolor="#fffef2",
        margin=dict(t=52, l=52, r=28, b=48),
        colorway=["#608c7b", "#4a7c6a", "#7aaf9a", "#8fbcab", "#c4a574", "#5a7d72"],
        legend=dict(font=dict(color=charcoal)),
    )
    fig.update_xaxes(gridcolor=grid, zerolinecolor=grid, color=charcoal)
    fig.update_yaxes(gridcolor=grid, zerolinecolor=grid, color=charcoal)
    return fig


def prepare_analytics_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce")
    out["duration"] = pd.to_numeric(out["duration"], errors="coerce").replace(0, 1.0).fillna(1.0)
    if "cost_per_day" not in out.columns:
        out["cost_per_day"] = (out["price"] / out["duration"]).replace(
            [float("inf"), float("-inf")], pd.NA
        )
    for col in ("location", "type", "source", "name"):
        if col in out.columns:
            out[col] = out[col].astype(str)
    return out


def fig_top_locations(df: pd.DataFrame, top_n: int = 12) -> object:
    ensure_plotly_express()
    if df.empty or "location" not in df.columns:
        return apply_chart_theme(px.bar(title="No data for locations"))
    g = (
        df.groupby("location", as_index=False)
        .size()
        .rename(columns={"size": "listings"})
        .sort_values("listings", ascending=False)
        .head(max(1, top_n))
    )
    fig = px.bar(
        g,
        x="location",
        y="listings",
        color="listings",
        color_continuous_scale=[[0, "#4a7c6a"], [0.5, "#608c7b"], [1, "#9bc4b4"]],
        title=f"Top {len(g)} destinations by listing count",
        labels={"location": "Destination", "listings": "Number of listings"},
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-35)
    return apply_chart_theme(fig)


def fig_price_rating_scatter(
    df: pd.DataFrame,
    color_by: str = "type",
    max_points: int = 4000,
    currency: str = "EUR",
) -> object:
    ensure_plotly_express()
    sub = df.dropna(subset=["price", "rating"])
    if sub.empty:
        return apply_chart_theme(px.scatter(title="No rows with both price and rating"))
    if len(sub) > max_points:
        sub = sub.sample(max_points, random_state=42)
    color_col = color_by if color_by in sub.columns else None
    hover_cols = [c for c in ("name", "location", "type", "source") if c in sub.columns]
    fig = px.scatter(
        sub,
        x="price",
        y="rating",
        color=color_col,
        hover_data=hover_cols,
        opacity=0.55,
        title=f"Price vs rating (up to {max_points:,} points · {currency})",
        labels={"price": f"Price ({currency})", "rating": "Rating"},
    )
    fig.update_traces(marker=dict(size=8, line=dict(width=0)))
    fig.update_layout(legend_title_text=color_col or "")
    return apply_chart_theme(fig)


def fig_price_histogram(df: pd.DataFrame, currency: str = "EUR") -> object:
    ensure_plotly_express()
    sub = df.dropna(subset=["price"])
    if sub.empty:
        return apply_chart_theme(px.histogram(title="No price values"))
    n = len(sub)
    fig = px.histogram(
        sub,
        x="price",
        nbins=min(45, max(15, int(n**0.5))),
        color_discrete_sequence=["#608c7b"],
        title="Distribution of total price",
        labels={"price": f"Price ({currency})"},
    )
    return apply_chart_theme(fig)


def fig_rating_by_type_box(df: pd.DataFrame) -> object:
    ensure_plotly_express()
    sub = df.dropna(subset=["rating", "type"])
    if sub.empty:
        return apply_chart_theme(px.box(title="No rating/type pairs"))
    fig = px.box(
        sub,
        x="type",
        y="rating",
        color="type",
        points="outliers",
        title="Rating distribution by listing type",
        labels={"type": "Listing type", "rating": "Rating"},
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-25)
    return apply_chart_theme(fig)


def fig_source_share(df: pd.DataFrame) -> object:
    ensure_plotly_express()
    if "source" not in df.columns or df.empty:
        return apply_chart_theme(px.pie(title="No source column"))
    counts = df["source"].value_counts().reset_index()
    counts.columns = ["source", "count"]
    fig = px.pie(
        counts,
        names="source",
        values="count",
        hole=0.35,
        title="Share of listings by data source",
    )
    return apply_chart_theme(fig)


def fig_sentiment_histogram(df: pd.DataFrame) -> object:
    ensure_plotly_express()
    if "sentiment_compound" not in df.columns:
        return apply_chart_theme(px.histogram(title="Sentiment scores not available (run sentiment step)"))
    sub = df.dropna(subset=["sentiment_compound"])
    if sub.empty:
        return apply_chart_theme(px.histogram(title="No sentiment values"))
    fig = px.histogram(
        sub,
        x="sentiment_compound",
        nbins=32,
        color_discrete_sequence=["#8b7355"],
        title="Review sentiment (VADER compound)",
        labels={"sentiment_compound": "Compound score (−1 to +1)"},
    )
    return apply_chart_theme(fig)
