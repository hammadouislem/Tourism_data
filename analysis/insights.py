"""
Business-style insights: popular destinations, best-rated listings, price vs rating.
"""

from __future__ import annotations

import json
import os
from typing import Dict, Optional

import pandas as pd

from utils.pipeline_paths import analytics_input_path

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INSIGHTS_DIR = os.path.join(ROOT_DIR, "output", "insights")
POPULAR_PATH = os.path.join(INSIGHTS_DIR, "popular_destinations.csv")
BEST_RATED_PATH = os.path.join(INSIGHTS_DIR, "best_rated_places.csv")
PRICE_RATING_PATH = os.path.join(INSIGHTS_DIR, "price_vs_rating.json")


def run_insights(input_path: Optional[str] = None) -> Dict[str, object]:
    path = input_path or analytics_input_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Input not found: {path}. Run merge/clean first.")

    df = pd.read_csv(path, encoding="utf-8")
    if df.empty:
        print("[insights] No rows to analyze.")
        return {}

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce")

    popular = (
        df.groupby("location", as_index=False)
        .agg(listings=("name", "count"), avg_price=("price", "mean"), avg_rating=("rating", "mean"))
        .sort_values("listings", ascending=False)
        .round(3)
    )

    cols = ["name", "location", "rating", "price", "source"]
    extra = [c for c in ("sentiment_compound",) if c in df.columns]
    best_rated = (
        df.sort_values(["rating", "price"], ascending=[False, True])
        .head(25)
        .loc[:, [c for c in cols + extra if c in df.columns]]
        .reset_index(drop=True)
    )

    sub = df.dropna(subset=["price", "rating"])
    if len(sub) > 2 and sub["price"].std() > 0 and sub["rating"].std() > 0:
        corr = float(sub["price"].corr(sub["rating"]))
    else:
        corr = float("nan")
    price_rating_payload = {
        "pearson_correlation_price_rating": corr,
        "n_points": int(len(sub)),
        "mean_price": float(sub["price"].mean()) if len(sub) else None,
        "mean_rating": float(sub["rating"].mean()) if len(sub) else None,
    }

    os.makedirs(INSIGHTS_DIR, exist_ok=True)
    popular.to_csv(POPULAR_PATH, index=False, encoding="utf-8")
    best_rated.to_csv(BEST_RATED_PATH, index=False, encoding="utf-8")
    with open(PRICE_RATING_PATH, "w", encoding="utf-8") as f:
        json.dump(price_rating_payload, f, indent=2)

    print(f"[insights] Popular destinations -> {POPULAR_PATH}")
    print(f"[insights] Best-rated sample -> {BEST_RATED_PATH}")
    print(f"[insights] Price vs rating stats -> {PRICE_RATING_PATH}")
    return {
        "popular_destinations": popular,
        "best_rated_places": best_rated,
        "price_vs_rating": price_rating_payload,
    }


if __name__ == "__main__":
    run_insights()
