import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils.currency import mean_price_axis_label, price_axis_label
from utils.env_loader import load_project_dotenv
from utils.pipeline_paths import analytics_input_path

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_PATH = os.path.join(ROOT_DIR, "output", "clean_data.csv")
SUMMARY_PATH = os.path.join(ROOT_DIR, "output", "analysis_summary.csv")
VIZ_DIR = os.path.join(ROOT_DIR, "output", "viz")
PRICE_DIST_PATH = os.path.join(VIZ_DIR, "price_distribution.png")
RATING_DIST_PATH = os.path.join(VIZ_DIR, "rating_distribution.png")
PRICE_BY_LOC_PATH = os.path.join(VIZ_DIR, "avg_price_top_locations.png")


def _setup_axes_style(ax: plt.Axes) -> None:
    ax.grid(True, alpha=0.35, linestyle="--")
    ax.set_facecolor("#fafafa")


def run_analysis(input_path=None) -> Dict[str, pd.DataFrame]:
    load_project_dotenv(ROOT_DIR)
    input_path = input_path or analytics_input_path()
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}. Run merge_data first.")

    df = pd.read_csv(input_path, encoding="utf-8")
    if df.empty:
        print("[analysis] No data to analyze.")
        return {"data": df, "summary": pd.DataFrame()}

    df["cost_per_day"] = (
        pd.to_numeric(df["price"], errors="coerce") / pd.to_numeric(df["duration"], errors="coerce")
    ).round(2)
    df["cost_per_day"] = df["cost_per_day"].replace([float("inf"), float("-inf")], pd.NA)

    summary = (
        df.groupby("type", as_index=False)
        .agg(
            avg_price=("price", "mean"),
            median_price=("price", "median"),
            avg_cost_per_day=("cost_per_day", "mean"),
            count=("name", "count"),
        )
        .round(2)
    )

    os.makedirs(os.path.dirname(SUMMARY_PATH), exist_ok=True)
    os.makedirs(VIZ_DIR, exist_ok=True)
    summary.to_csv(SUMMARY_PATH, index=False, encoding="utf-8")

    price = pd.to_numeric(df["price"], errors="coerce").dropna()
    rating = pd.to_numeric(df["rating"], errors="coerce").dropna()

    # --- Price histogram (log-spaced bins if range is wide)
    fig, ax = plt.subplots(figsize=(9, 5))
    _setup_axes_style(ax)
    if len(price) > 0:
        pmin, pmax = float(price.min()), float(price.max())
        if pmax > 0 and pmax / max(pmin, 1e-9) > 50:
            bins = np.logspace(np.log10(max(pmin, 1e-6)), np.log10(pmax), 40)
            ax.hist(price, bins=bins, color="#2563eb", edgecolor="white", linewidth=0.5)
            ax.set_xscale("log")
            ax.set_xlabel(f"{price_axis_label()} (log scale)")
        else:
            ax.hist(price, bins=min(50, max(15, int(len(price) ** 0.5))), color="#2563eb", edgecolor="white", linewidth=0.5)
            ax.set_xlabel(price_axis_label())
    ax.set_title("Price distribution")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(PRICE_DIST_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Rating distribution
    fig, ax = plt.subplots(figsize=(9, 5))
    _setup_axes_style(ax)
    if len(rating) > 0:
        ax.hist(rating, bins=min(35, max(10, int(len(rating) ** 0.25))), color="#059669", edgecolor="white", linewidth=0.5)
    ax.set_title("Rating distribution")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(RATING_DIST_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # --- Average price by top locations
    loc_avg = (
        df.assign(price=pd.to_numeric(df["price"], errors="coerce"))
        .dropna(subset=["price", "location"])
        .groupby("location", as_index=False)["price"]
        .mean()
        .sort_values("price", ascending=False)
        .head(15)
    )
    fig, ax = plt.subplots(figsize=(10, 5))
    _setup_axes_style(ax)
    if not loc_avg.empty:
        ax.barh(loc_avg["location"][::-1], loc_avg["price"][::-1], color="#7c3aed", edgecolor="white", linewidth=0.5)
    ax.set_title("Average price — top 15 locations")
    ax.set_xlabel(mean_price_axis_label())
    fig.tight_layout()
    fig.savefig(PRICE_BY_LOC_PATH, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"[analysis] Summary -> {SUMMARY_PATH}")
    print(f"[analysis] Charts -> {VIZ_DIR}/")
    return {"data": df, "summary": summary}


if __name__ == "__main__":
    run_analysis()
