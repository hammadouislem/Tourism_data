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

from analysis.recommendation import recommend_for_preferences
from utils.currency import format_price, get_currency_code
from utils.env_loader import load_project_dotenv
from utils.pipeline_paths import CLEAN_DATA_CSV, ENRICHED_LISTINGS_CSV, analytics_input_path
from visualization.dashboard import build_dashboard_figure
from visualization.express_charts import (
    apply_chart_theme,
    fig_price_histogram,
    fig_price_rating_scatter,
    fig_rating_by_type_box,
    fig_sentiment_histogram,
    fig_source_share,
    fig_top_locations,
    prepare_analytics_df,
)

load_project_dotenv(ROOT)

VIZ_DIR = os.path.join(ROOT, "output", "viz")
INSIGHTS_DIR = os.path.join(ROOT, "output", "insights")
SUMMARY_CSV = os.path.join(ROOT, "output", "analysis_summary.csv")


def inject_app_theme() -> None:
    """Beige background + sage green accents (HIKE IT–style palette)."""
    st.markdown(
        """
<style>
@import url("https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap");

:root {
  --bg-beige: #a8a899;
  --sage: #608c7b;
  --sage-dark: #4a7c6a;
  --cream: #fffdd0;
  --cream-soft: #fffef5;
  --charcoal: #3d3d3a;
  --muted: #6b6b66;
  --tab-inactive-bg: #f2f0c8;
}

html, body, [class*="stApp"] {
  font-family: "Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif;
  background-color: var(--bg-beige) !important;
  color: var(--charcoal);
}

/* Main column: cream instead of default white shell */
section.main > div {
  background-color: var(--cream) !important;
}
[data-testid="stAppViewContainer"] {
  background-color: var(--bg-beige) !important;
}

.block-container {
  padding-top: 1.25rem;
  padding-bottom: 1.5rem;
  max-width: 1200px;
  background: var(--cream);
  border-radius: 20px;
  padding-left: 2rem !important;
  padding-right: 2rem !important;
  margin-top: 0.75rem;
  box-shadow: 0 12px 40px rgba(61, 61, 58, 0.12);
  border: 1px solid rgba(96, 140, 123, 0.22);
}

/* Main text */
.stMarkdown p, .stMarkdown li, [data-testid="stCaption"] {
  color: var(--muted);
}
.stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
  color: var(--charcoal) !important;
}

/* Hero: sage kicker on cream */
.hero-wrap {
  background: var(--cream);
  border-radius: 16px;
  padding: 1.5rem 1.75rem 1.35rem;
  margin: 0 0 1.25rem 0;
  box-shadow: 0 8px 32px rgba(61, 61, 58, 0.1);
  border: 1px solid rgba(96, 140, 123, 0.35);
}
.hero-wrap h1 {
  font-family: "Plus Jakarta Sans", sans-serif;
  font-weight: 700;
  font-size: clamp(1.4rem, 2.4vw, 1.85rem);
  color: var(--charcoal);
  margin: 0 0 0.35rem 0;
  letter-spacing: -0.02em;
  line-height: 1.2;
  border: none;
  padding: 0;
}
.hero-kicker {
  display: inline-block;
  font-size: 0.65rem;
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: #ffffff;
  background: var(--sage);
  padding: 0.35rem 0.75rem;
  border-radius: 10px 10px 10px 4px;
  margin: 0 0 0.65rem 0;
  font-weight: 700;
}
.hero-sub {
  color: var(--muted);
  font-size: 0.9rem;
  margin: 0;
  line-height: 1.55;
}
.hero-sub code {
  background: rgba(255, 253, 208, 0.85);
  color: var(--sage-dark);
  padding: 0.1rem 0.4rem;
  border-radius: 6px;
  font-size: 0.85em;
  border: 1px solid rgba(96, 140, 123, 0.25);
}
.hero-authors {
  font-size: 0.82rem;
  color: var(--muted);
  margin: 0.85rem 0 0 0;
  line-height: 1.45;
}
.hero-authors strong {
  color: var(--charcoal);
  font-weight: 600;
}

[data-testid="stMetric"] {
  background: var(--cream-soft);
  border: 1px solid rgba(96, 140, 123, 0.35);
  border-radius: 14px;
  padding: 0.75rem 0.9rem;
  box-shadow: 0 4px 16px rgba(61, 61, 58, 0.06);
}
[data-testid="stMetricLabel"] p {
  font-size: 0.7rem !important;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--muted) !important;
  font-weight: 600 !important;
}
[data-testid="stMetricValue"] {
  font-size: 1.25rem !important;
  font-weight: 700 !important;
  color: var(--sage-dark) !important;
}

/* Tabs: active = sage (HIKE IT), inactive = light grey */
.stTabs [data-baseweb="tab-list"] {
  gap: 6px;
  background: var(--tab-inactive-bg);
  padding: 8px 10px;
  border-radius: 14px;
  border: 1px solid rgba(96, 140, 123, 0.2);
}
.stTabs [data-baseweb="tab"] {
  border-radius: 12px;
  padding: 0.5rem 1rem;
  font-weight: 600;
  font-size: 0.86rem;
  color: var(--muted);
}
.stTabs [aria-selected="true"] {
  background: var(--sage) !important;
  color: #ffffff !important;
  box-shadow: 0 2px 10px rgba(74, 124, 106, 0.25);
}

div[data-testid="stExpander"] details {
  border: 1px solid rgba(96, 140, 123, 0.3);
  border-radius: 12px;
  background: var(--cream-soft);
}
div[data-testid="stExpander"] summary {
  color: var(--charcoal);
}

section[data-testid="stSidebar"] > div {
  background: linear-gradient(180deg, var(--cream) 0%, #f5f5c8 100%) !important;
  border-right: 1px solid rgba(96, 140, 123, 0.25);
}
section[data-testid="stSidebar"] .stMarkdown h2 {
  color: var(--sage-dark) !important;
  font-weight: 700;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
  color: var(--charcoal) !important;
}
section[data-testid="stSidebar"] .stCaption {
  color: var(--muted) !important;
}

[data-testid="stPlotlyChart"] {
  border: 1px solid rgba(96, 140, 123, 0.28);
  border-radius: 14px;
  padding: 6px 8px 4px;
  background: var(--cream-soft);
  margin-bottom: 0.35rem;
  box-shadow: 0 4px 18px rgba(61, 61, 58, 0.07);
}

/* Footer: sage band, light text */
.tgen-footer {
  background: linear-gradient(180deg, var(--sage) 0%, var(--sage-dark) 100%);
  color: #f8faf8;
  margin: 2rem 0 0;
  padding: 1.75rem 0.75rem 0;
  border-radius: 0 0 16px 16px;
}
.tgen-footer-columns {
  display: flex;
  flex-wrap: wrap;
  gap: 2rem 3rem;
  justify-content: space-between;
  max-width: 1100px;
  margin: 0 auto;
  padding-bottom: 1.25rem;
}
.tgen-col { flex: 1 1 200px; min-width: 180px; }
.tgen-brand {
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #ffffff;
  margin: 0 0 0.45rem 0;
}
.tgen-desc, .tgen-col p, .tgen-col li {
  font-size: 0.86rem;
  line-height: 1.55;
  color: rgba(248, 250, 248, 0.88);
  margin: 0;
}
.tgen-col h4 {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: rgba(255, 255, 255, 0.92);
  margin: 0 0 0.55rem 0;
  font-weight: 700;
}
.tgen-col ul { list-style: none; padding: 0; margin: 0; }
.tgen-col li { margin-bottom: 0.3rem; }
.tgen-footer-bar {
  border-top: 1px solid rgba(255, 255, 255, 0.22);
  padding: 0.75rem 0.5rem;
  font-size: 0.72rem;
  color: rgba(248, 250, 248, 0.8);
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem 1.25rem;
  justify-content: space-between;
  max-width: 1100px;
  margin: 0 auto;
}
.tgen-footer code {
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
}
</style>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    """Sage footer band (HIKE IT–style)."""
    st.markdown(
        """
<div class="tgen-footer">
  <div class="tgen-footer-columns">
    <div class="tgen-col">
      <p class="tgen-brand">TOURISM ANALYTICS</p>
      <p class="tgen-desc">
        Explore merged listings — prices, ratings, sources and review sentiment — in one interactive workspace.
      </p>
    </div>
    <div class="tgen-col">
      <h4>Liens utiles</h4>
      <ul>
        <li>Explore — charts Plotly Express</li>
        <li>Overview grid — export HTML</li>
        <li>Recommendations — filtres & scoring</li>
      </ul>
    </div>
    <div class="tgen-col">
      <h4>Contact</h4>
      <p class="tgen-desc">Dataset & pipeline : voir README du projet.<br/>Lancer <code>python main.py</code> puis recharger l’app.</p>
    </div>
  </div>
  <div class="tgen-footer-bar">
    <span>© 2026 Tourism analytics · projet data science</span>
    <span>Streamlit + Plotly · usage éducatif</span>
  </div>
</div>
        """,
        unsafe_allow_html=True,
    )


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


def apply_explorer_filters(
    df: pd.DataFrame,
    price_range: tuple[float, float],
    rating_range: tuple[float, float],
    locations: list[str],
    sources: list[str],
    types: list[str],
    include_missing_price: bool,
    include_missing_rating: bool,
) -> pd.DataFrame:
    out = df
    p_lo, p_hi = price_range
    mask_p = out["price"].between(p_lo, p_hi)
    if include_missing_price:
        mask_p = mask_p | out["price"].isna()
    out = out[mask_p]

    r_lo, r_hi = rating_range
    mask_r = out["rating"].between(r_lo, r_hi)
    if include_missing_rating:
        mask_r = mask_r | out["rating"].isna()
    out = out[mask_r]

    if locations:
        out = out[out["location"].astype(str).isin(locations)]
    if sources and "source" in out.columns:
        out = out[out["source"].astype(str).isin(sources)]
    if types:
        tset = {t.lower() for t in types}
        out = out[out["type"].astype(str).str.lower().isin(tset)]
    return out


def main() -> None:
    st.set_page_config(
        page_title="Tourism Analytics Studio",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_app_theme()

    df = load_main_table()
    if df.empty:
        st.error(
            f"No analytics file found. Expected `{ENRICHED_LISTINGS_CSV}` or `{CLEAN_DATA_CSV}`. "
            "Run **`python main.py`** from the project root, then reload this page."
        )
        st.stop()

    df = prepare_analytics_df(df)
    cur = get_currency_code()

    with st.sidebar:
        st.header("Data source")
        st.code(analytics_input_path(), language="text")
        st.metric("Rows loaded", f"{len(df):,}")
        st.metric("Unique locations", f"{df['location'].nunique():,}")
        if os.path.isfile(os.path.join(ROOT, "output", "results.csv")):
            st.success("Clustering results present (`results.csv`).")
        else:
            st.warning("No `results.csv` — run the full pipeline for tier charts.")

        st.divider()
        st.header("Explorer filters")
        st.caption("Adjust these controls to refresh all Plotly Express charts in the **Explore** tab.")
        prices = df["price"].dropna()
        ratings = df["rating"].dropna()
        if prices.empty:
            p_lo, p_hi = 0.0, 1.0
        else:
            p_lo, p_hi = float(prices.min()), float(prices.max())
            if p_lo >= p_hi:
                p_hi = p_lo + 1.0
        price_range = st.slider(
            "Price range",
            min_value=p_lo,
            max_value=p_hi,
            value=(p_lo, p_hi),
            help=f"Total listing price ({cur}).",
        )
        if ratings.empty:
            r_lo, r_hi = 0.0, 5.0
        else:
            r_lo, r_hi = float(ratings.min()), float(ratings.max())
            r_hi = min(5.0, max(r_hi, r_lo + 0.1))
        rating_range = st.slider(
            "Rating range",
            min_value=0.0,
            max_value=5.0,
            value=(max(0.0, r_lo), min(5.0, r_hi)),
            step=0.1,
        )
        loc_opts = sorted(df["location"].dropna().astype(str).unique().tolist())
        src_opts = sorted(df["source"].dropna().astype(str).unique().tolist()) if "source" in df.columns else []
        type_opts = sorted(df["type"].dropna().astype(str).str.strip().unique().tolist())
        filter_locs = st.multiselect("Destinations (none = all)", options=loc_opts)
        if src_opts:
            filter_sources = st.multiselect("Data sources (none = all)", options=src_opts)
        else:
            filter_sources = []
            st.caption("No `source` column values — source filter disabled.")
        if type_opts:
            filter_types = st.multiselect("Listing types (none = all)", options=type_opts)
        else:
            filter_types = []
            st.caption("No listing types — type filter disabled.")
        top_n_locs = st.slider("Top destinations (bar chart)", 5, 25, 12)
        scatter_cap = st.slider("Scatter plot sample size", 500, 25_000, 8000, step=100)
        color_scatter = st.selectbox("Color scatter by", options=[c for c in ("type", "source", "location") if c in df.columns] or ["type"])
        incl_na_price = st.checkbox("Include rows with missing price", value=False)
        incl_na_rating = st.checkbox("Include rows with missing rating", value=False)

    st.markdown(
        f"""
<div class="hero-wrap">
  <p class="hero-kicker">Tourism data · explore &amp; present</p>
  <h1>Tourism listings analytics</h1>
  <p class="hero-sub">
    Live pipeline view — refresh after <code>python main.py</code>.
    Prices in <strong>{cur}</strong> (<code>PRICE_CURRENCY</code> in <code>.env</code>).
  </p>
  <p class="hero-authors"><strong>Authors:</strong> HAMMADOU Islem · MOKEDDEM Akram · BOKHELKHAL Chameseddine</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    filtered = apply_explorer_filters(
        df,
        price_range,
        rating_range,
        filter_locs,
        filter_sources,
        filter_types,
        incl_na_price,
        incl_na_rating,
    )

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Rows (filtered)", f"{len(filtered):,}")
    m2.metric("Avg price (filtered)", format_price(filtered["price"].mean()) if filtered["price"].notna().any() else "—")
    m3.metric("Median price (filtered)", format_price(filtered["price"].median()) if filtered["price"].notna().any() else "—")
    m4.metric("Avg rating (filtered)", f"{filtered['rating'].mean():.2f}" if filtered["rating"].notna().any() else "—")
    m5.metric("Sources (all data)", df["source"].nunique() if "source" in df.columns else "—")

    with st.expander("Dataset description (for slides / report)", expanded=False):
        st.markdown(
            """
### What the rows represent
Each row is one **tourism listing** (hotel stay, package, or similar offer) after merging feeds
(Booking-style exports, TripAdvisor-style exports, external CSVs, and optional Kaggle hotel demand data).

### Attributes
| Attribute | Role | Suggested type | Notes |
|-----------|------|----------------|-------|
| `name` | Listing title | Categorical (nominal) | Text identity for hover / tables. |
| `type` | Product category | Categorical (nominal) | e.g. hotel, offer — used for grouping and color. |
| `location` | Destination | Categorical (nominal) | City or region; bars and filters. |
| `price` | Total price | Quantitative (continuous) | Axis position, histogram bins. |
| `duration` | Stay length (days) | Quantitative (discrete / continuous) | Derived **cost per day** = price ÷ duration. |
| `rating` | Quality score | Quantitative (continuous) | Often 0–5; vertical position, box plots. |
| `source` | Provenance | Categorical (nominal) | Data feed; pie / color. |
| `review_text` | Free text | — | Input to VADER → `sentiment_*` scores. |
| `sentiment_compound` | Review polarity | Quantitative (continuous, bounded ~[−1,1]) | Histogram when enriched file is loaded. |

### Visual channels used here
- **Position (x / y)** — price vs rating scatter: appropriate for two continuous variables; trend and outliers are visible.
- **Bar length** — counts per destination: nominal categories on one axis, magnitude on the other.
- **Histogram frequency** — price and sentiment: standard for univariate continuous distributions.
- **Box plot** — rating by type: compares continuous rating across nominal categories.
- **Color (scatter)** — nominal split (type / source / location) without implying order.
- **Pie / donut angles** — parts-of-whole for source mix (nominal shares).

### Layout rationale
The app uses a **wide Streamlit layout**: KPI metrics on top, **sidebar filters** for analytical context,
and a dedicated **Explore** tab with a **two-column grid** so overview charts (destinations, mix) sit beside
relationship and distribution plots. This follows a *overview → filter → detail* flow suited to a 10-minute demo:
set filters, narrate one chart, then drill into another without scrolling excessively.
            """
        )

    tab_explore, tab_composite, tab_reco, tab_static, tab_table, tab_files = st.tabs(
        [
            "Explore",
            "Overview grid",
            "Recommendations",
            "Static figures",
            "Data table",
            "Insight files",
        ]
    )

    with tab_explore:
        st.markdown("##### Interactive charts")
        st.caption(
            "Six chart types driven by the same filtered subset · **Plotly Express** · adjust the sidebar to refresh."
        )
        if filtered.empty:
            st.warning("No rows match the current filters — widen price/rating ranges or clear multiselects.")
        else:
            r1c1, r1c2 = st.columns(2)
            with r1c1:
                st.plotly_chart(fig_top_locations(filtered, top_n=top_n_locs), width="stretch")
            with r1c2:
                st.plotly_chart(fig_source_share(filtered), width="stretch")
            r2c1, r2c2 = st.columns(2)
            with r2c1:
                st.plotly_chart(
                    fig_price_rating_scatter(filtered, color_by=color_scatter, max_points=scatter_cap, currency=cur),
                    width="stretch",
                )
            with r2c2:
                st.plotly_chart(fig_price_histogram(filtered, currency=cur), width="stretch")
            r3c1, r3c2 = st.columns(2)
            with r3c1:
                st.plotly_chart(fig_rating_by_type_box(filtered), width="stretch")
            with r3c2:
                st.plotly_chart(fig_sentiment_histogram(filtered), width="stretch")

    with tab_composite:
        st.markdown("##### Six-panel composite (HTML export)")
        st.caption("Same figure as `output/dashboard.html` after `python main.py`.")
        try:
            fig = apply_chart_theme(build_dashboard_figure(project_root=ROOT))
            st.plotly_chart(fig, width="stretch")
        except Exception as exc:
            st.error(f"Could not build chart: {exc}")

    with tab_reco:
        st.subheader("Match listings to your preferences")
        st.caption(
            "Set a budget ceiling and minimum rating, optionally pick destinations and categories. "
            "We filter the dataset, then rank what remains by similarity to a typical listing in that group "
            "(scaled price, duration, rating, cost/day, location/type features — cosine similarity). "
            "This is a content-based score, not a trained prediction model."
        )
        prices = df["price"].dropna()
        if prices.empty:
            st.warning("No valid prices in the dataset — cannot rank recommendations.")
        else:
            p_lo, p_hi = float(prices.min()), float(prices.max())
            loc_options = sorted(df["location"].dropna().astype(str).unique().tolist())
            type_options = sorted(df["type"].dropna().astype(str).str.strip().unique().tolist())

            with st.form("prefs_form"):
                use_cap = st.checkbox("Limit maximum price", value=True)
                max_price = st.slider(
                    "Maximum price (budget)",
                    min_value=p_lo,
                    max_value=max(p_hi, p_lo + 1e-6),
                    value=min(float(prices.quantile(0.75)), p_hi),
                    help="Only listings at or below this total price.",
                )
                min_rating = st.slider(
                    "Minimum rating",
                    min_value=0.0,
                    max_value=5.0,
                    value=0.0,
                    step=0.5,
                    help="Use 0 for no minimum.",
                )
                pref_locs = st.multiselect(
                    "Preferred destinations (optional)",
                    options=loc_options,
                    help="Leave empty to consider all locations.",
                )
                pref_types = st.multiselect(
                    "Listing types (optional)",
                    options=type_options,
                    help="Leave empty for all types.",
                )
                top_k = st.slider("How many suggestions", min_value=3, max_value=25, value=10)
                submitted = st.form_submit_button("Find best matches")

            if submitted and not prices.empty:
                work = df.copy()
                if pref_types:
                    tset = {t.lower() for t in pref_types}
                    work = work[work["type"].astype(str).str.lower().isin(tset)]
                if work.empty:
                    st.warning("No listings match the selected types.")
                else:
                    mp = max_price if use_cap else None
                    mr = min_rating if min_rating > 0.05 else None
                    plocs = pref_locs if pref_locs else None
                    try:
                        rec = recommend_for_preferences(
                            work,
                            max_price=mp,
                            min_rating=mr,
                            preferred_locations=plocs,
                            top_k=top_k,
                        )
                    except Exception as exc:
                        st.error(f"Recommendation step failed: {exc}")
                        rec = pd.DataFrame()

                    if rec is None or rec.empty:
                        st.info(
                            "No listings matched your filters — try raising the budget, lowering the minimum "
                            "rating, or choosing different destinations."
                        )
                    else:
                        show = rec.copy()
                        if "price" in show.columns:
                            show["price_fmt"] = show["price"].apply(
                                lambda x: format_price(x) if pd.notna(x) else "—"
                            )
                        st.success(f"Top {len(show)} picks (higher similarity is a closer match to the group norm).")
                        disp_cols = [
                            c
                            for c in (
                                "name",
                                "location",
                                "type",
                                "price_fmt",
                                "duration",
                                "rating",
                                "cost_per_day",
                                "similarity_to_ideal",
                            )
                            if c in show.columns
                        ]
                        st.dataframe(
                            show[disp_cols].rename(columns={"price_fmt": f"price ({get_currency_code()})"}),
                            width="stretch",
                            height=min(520, 60 + 36 * len(show)),
                        )
                        csv_out = rec.to_csv(index=False).encode("utf-8")
                        st.download_button(
                            "Download results as CSV",
                            data=csv_out,
                            file_name="recommendations_for_me.csv",
                            mime="text/csv",
                        )

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
                    st.image(p, caption=name, width="stretch")
                i += 1
        if i == 0:
            st.info("No PNG files yet. Run `python main.py` to generate figures under `output/viz/`.")

    with tab_table:
        n = st.slider("Preview rows", min_value=50, max_value=min(15_000, max(len(df), 50)), value=min(1000, len(df)), step=50)
        st.dataframe(df.head(n), width="stretch", height=480)
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
            st.dataframe(summary, width="stretch")

        st.write("**Insights folder**")
        if os.path.isdir(INSIGHTS_DIR):
            for fn in sorted(os.listdir(INSIGHTS_DIR)):
                st.text(os.path.join("output/insights", fn))
        else:
            st.caption("No insights directory yet.")

        html_path = os.path.join(ROOT, "output", "dashboard.html")
        if os.path.isfile(html_path):
            st.info(f"Standalone HTML also saved at: `{html_path}` (open in a browser).")

    render_footer()


if __name__ == "__main__":
    main()
