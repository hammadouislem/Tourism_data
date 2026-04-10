"""
Content-based tourism recommendations (similar listings).

Typical "Tourism Recommendation System" demos use item features when user–item
ratings are unavailable: scale numeric attributes and measure cosine similarity.

Reads clustered results when present (output/results.csv); otherwise clean_data.
"""

from __future__ import annotations

import os
from typing import List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
RESULTS_PATH = os.path.join(ROOT_DIR, "output", "results.csv")
CLEAN_PATH = os.path.join(ROOT_DIR, "output", "clean_data.csv")
OUTPUT_DEMO = os.path.join(ROOT_DIR, "output", "recommendations_demo.csv")

TOP_LOCATIONS = 15


def _load_listings() -> pd.DataFrame:
    if os.path.isfile(RESULTS_PATH):
        df = pd.read_csv(RESULTS_PATH, encoding="utf-8")
    elif os.path.isfile(CLEAN_PATH):
        df = pd.read_csv(CLEAN_PATH, encoding="utf-8")
    else:
        raise FileNotFoundError(
            f"No data found. Expected {RESULTS_PATH} or {CLEAN_PATH}. Run the pipeline first."
        )
    return df


def _prepare_numeric(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["price"] = pd.to_numeric(out["price"], errors="coerce")
    out["duration"] = pd.to_numeric(out["duration"], errors="coerce").replace(0, 1.0).fillna(1.0)
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce")
    med = out["rating"].median()
    if pd.isna(med):
        med = 0.0
    out["rating"] = out["rating"].fillna(med)
    out["cost_per_day"] = (out["price"] / out["duration"]).replace(
        [float("inf"), float("-inf")], np.nan
    )
    out = out.dropna(subset=["price", "cost_per_day"])
    return out.reset_index(drop=True)


def _encode_location_type(df: pd.DataFrame) -> pd.DataFrame:
    loc_counts = df["location"].astype(str).value_counts()
    top = set(loc_counts.head(TOP_LOCATIONS).index)
    loc_bucket = df["location"].astype(str).apply(lambda v: v if v in top else "Other")
    mini = pd.DataFrame(
        {
            "location_bucket": loc_bucket,
            "type": df["type"].astype(str).str.lower(),
        }
    )
    return pd.get_dummies(mini, columns=["location_bucket", "type"], dtype=float)


def build_feature_matrix(df: pd.DataFrame) -> Tuple[np.ndarray, pd.DataFrame, StandardScaler]:
    """Scaled numeric block + one-hot location/type."""
    base = _prepare_numeric(df)
    if base.empty:
        return np.array([]).reshape(0, 0), base, StandardScaler()

    numeric = base[["price", "duration", "rating", "cost_per_day"]].to_numpy(dtype=float)
    scaler = StandardScaler()
    num_scaled = scaler.fit_transform(numeric)

    dummies = _encode_location_type(base)
    if dummies.shape[1] == 0:
        features = num_scaled
    else:
        features = np.hstack([num_scaled, dummies.to_numpy(dtype=float)])

    return features, base, scaler


def recommend_similar(
    df: pd.DataFrame,
    query_index: int,
    top_k: int = 5,
    features: Optional[np.ndarray] = None,
    prepared: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """
    Return top_k rows most similar to query_index (excluding the query row).
    Similarity = cosine similarity on the feature matrix.
    """
    if features is None or prepared is None:
        features, prepared, _ = build_feature_matrix(df)

    if len(prepared) < 2 or features.size == 0:
        return pd.DataFrame()

    if query_index < 0 or query_index >= len(prepared):
        raise IndexError(f"query_index {query_index} out of range for {len(prepared)} rows.")

    q = features[query_index : query_index + 1]
    sims = cosine_similarity(q, features).ravel()
    sims[query_index] = -1.0

    k = min(top_k, len(prepared) - 1)
    if k <= 0:
        return pd.DataFrame()

    idx = np.argsort(-sims)[:k]
    rows = prepared.iloc[idx].copy()
    rows["similarity"] = sims[idx]
    rows["query_index"] = query_index
    if "name" in prepared.columns:
        qname = prepared.iloc[query_index]["name"]
        rows.insert(0, "query_name", qname)
    return rows.reset_index(drop=True)


def recommend_for_preferences(
    df: pd.DataFrame,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    preferred_locations: Optional[Sequence[str]] = None,
    top_k: int = 8,
) -> pd.DataFrame:
    """
    Filter listings by hard constraints, then rank the rest by distance to ideal point
    (median price/rating of the filtered set, or user caps).
    """
    work = _prepare_numeric(df)
    if work.empty:
        return pd.DataFrame()

    if max_price is not None:
        work = work[work["price"] <= max_price]
    if min_rating is not None:
        work = work[work["rating"] >= min_rating]
    if preferred_locations:
        prefs = {str(p).strip().lower() for p in preferred_locations}
        loc_mask = work["location"].astype(str).str.lower().isin(prefs)
        if loc_mask.any():
            work = work[loc_mask]

    if len(work) <= 1:
        return work.reset_index(drop=True)

    features, aligned, _ = build_feature_matrix(work)
    if features.size == 0:
        return work.reset_index(drop=True)

    ideal = np.median(features, axis=0, keepdims=True)
    sims = cosine_similarity(ideal, features).ravel()
    order = np.argsort(-sims)[: min(top_k, len(aligned))]
    out = aligned.iloc[order].copy()
    out["similarity_to_ideal"] = sims[order]
    return out.reset_index(drop=True)


def run_recommendations(
    input_path: Optional[str] = None,
    seeds: Optional[List[int]] = None,
    top_k: int = 5,
    output_path: str = OUTPUT_DEMO,
) -> pd.DataFrame:
    """
    Build demo recommendations for a few seed rows and save CSV.
    Default seeds: first, middle, last index (if present).
    """
    df = pd.read_csv(input_path, encoding="utf-8") if input_path else _load_listings()

    features, prepared, _ = build_feature_matrix(df)
    if len(prepared) < 2:
        print("[recommendation] Not enough rows for similarity recommendations.")
        return pd.DataFrame()

    if seeds is None:
        n = len(prepared)
        seeds = [0]
        if n > 2:
            seeds.append(n // 2)
        if n > 1:
            seeds.append(n - 1)
        seeds = sorted(set(seeds))

    chunks: List[pd.DataFrame] = []
    for idx in seeds:
        if idx >= len(prepared):
            continue
        rec = recommend_similar(df, idx, top_k=top_k, features=features, prepared=prepared)
        if not rec.empty:
            rec["seed_index"] = idx
            chunks.append(rec)

    if not chunks:
        out = pd.DataFrame()
    else:
        out = pd.concat(chunks, ignore_index=True)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[recommendation] Demo recommendations -> {output_path}")
    return out


if __name__ == "__main__":
    run_recommendations()
