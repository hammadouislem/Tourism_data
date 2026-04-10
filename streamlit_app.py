"""
Tourism analytics web UI (Streamlit).

Run from project root:
    pip install streamlit
    streamlit run streamlit_app.py

Requires pipeline outputs under output/ (run python main.py first).
"""

from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pandas as pd
import streamlit as st

from utils.currency import format_price, get_currency_code
from utils.env_loader import load_project_dotenv
from utils.pipeline_paths import CLEAN_DATA_CSV, ENRICHED_LISTINGS_CSV, analytics_input_path
from visualization.dashboard import build_dashboard_figure

load_project_dotenv(ROOT)

VIZ_DIR = os.path.join(ROOT, "output", "viz")
INSIGHTS_DIR = os.path.join(ROOT, "output", "insights")
SUMMARY_CSV = os.path.join(ROOT, "output", "analysis_summary.csv")


@st.cache_data(show_spinner=False)
def load_main_table() -> pd.DataFrame:
    path = analytics_input_path()
    if not os.path.isfile(path):
        return pd.DataFrame()
    return pd.read_csv(path, encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_summary() -> pd.DataFrame:
    if not os.path.isfile(SUMMARY_CSV):
        return pd.DataFrame()
    return pd.read_csv(SUMMARY_CSV, encoding="utf-8")


def main() -> None:
    st.set_page_config(
        page_title="Tourism analytics",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Tourism listings analytics")
    st.caption(
        "Live view of pipeline outputs · Refresh after `python main.py`. "
        f"Prices are labeled in **{get_currency_code()}** (set `PRICE_CURRENCY` in `.env`, e.g. EUR or USD)."
    )

    df = load_main_table()
    if df.empty:
        st.error(
            f"No analytics file found. Expected `{ENRICHED_LISTINGS_CSV}` or `{CLEAN_DATA_CSV}`. "
            "Run **`python main.py`** from the project root, then reload this page."
        )
        st.stop()

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    with st.sidebar:
        st.header("Data source")
        st.code(analytics_input_path(), language="text")
        st.metric("Rows loaded", f"{len(df):,}")
        st.metric("Unique locations", f"{df['location'].nunique():,}")
        if os.path.isfile(os.path.join(ROOT, "output", "results.csv")):
            st.success("Clustering results present (`results.csv`).")
        else:
            st.warning("No `results.csv` — run the full pipeline for tier charts.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Avg price", format_price(df["price"].mean()) if df["price"].notna().any() else "—")
    m2.metric("Median price", format_price(df["price"].median()) if df["price"].notna().any() else "—")
    m3.metric("Avg rating", f"{df['rating'].mean():.2f}" if df["rating"].notna().any() else "—")
    m4.metric("Sources", df["source"].nunique() if "source" in df.columns else "—")

    tab_plotly, tab_static, tab_table, tab_files = st.tabs(
        ["Interactive charts", "Static figures", "Data table", "Insight files"]
    )

    with tab_plotly:
        st.subheader("Plotly dashboard")
        try:
            fig = build_dashboard_figure(project_root=ROOT)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as exc:
            st.error(f"Could not build chart: {exc}")

    with tab_static:
        st.subheader("Matplotlib exports (`output/viz/`)")
        names = [
            "price_distribution.png",
            "rating_distribution.png",
            "avg_price_top_locations.png",
            "clusters.png",
            "cluster_tier_counts.png",
        ]
        cols = st.columns(2)
        i = 0
        for name in names:
            p = os.path.join(VIZ_DIR, name)
            if os.path.isfile(p):
                with cols[i % 2]:
                    st.image(p, caption=name, use_container_width=True)
                i += 1
        if i == 0:
            st.info("No PNG files yet. Run `python main.py` to generate figures under `output/viz/`.")

    with tab_table:
        n = st.slider("Preview rows", min_value=50, max_value=min(5000, max(len(df), 50)), value=min(500, len(df)), step=50)
        st.dataframe(df.head(n), use_container_width=True, height=480)
        csv_bytes = df.head(10_000).to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download preview CSV (up to 10k rows)",
            data=csv_bytes,
            file_name="tourism_preview.csv",
            mime="text/csv",
        )

    with tab_files:
        st.write("**Analysis summary** (`output/analysis_summary.csv`)")
        summary = load_summary()
        if summary.empty:
            st.caption("File missing — run the pipeline.")
        else:
            st.dataframe(summary, use_container_width=True)

        st.write("**Insights folder**")
        if os.path.isdir(INSIGHTS_DIR):
            for fn in sorted(os.listdir(INSIGHTS_DIR)):
                st.text(os.path.join("output/insights", fn))
        else:
            st.caption("No insights directory yet.")

        html_path = os.path.join(ROOT, "output", "dashboard.html")
        if os.path.isfile(html_path):
            st.info(f"Standalone HTML also saved at: `{html_path}` (open in a browser).")


if __name__ == "__main__":
    main()
