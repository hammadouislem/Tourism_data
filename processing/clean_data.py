import numpy as np
import pandas as pd


EXPECTED_COLUMNS = [
    "name",
    "type",
    "location",
    "price",
    "duration",
    "rating",
    "source",
    "review_text",
]


def clean_tourism_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standard cleaning for raw scraped tourism data."""
    if df.empty:
        return pd.DataFrame(columns=EXPECTED_COLUMNS)

    work = df.copy()
    work.columns = [str(c).strip().lower() for c in work.columns]

    for col in EXPECTED_COLUMNS:
        if col not in work.columns:
            work[col] = pd.NA

    work["name"] = work["name"].astype("string").str.strip()
    work["location"] = work["location"].astype("string").str.strip()
    work["type"] = work["type"].astype("string").str.lower().str.strip()
    work["source"] = work["source"].astype("string").str.strip()
    work["review_text"] = work["review_text"].astype("string").str.strip()
    work["review_text"] = work["review_text"].replace("", pd.NA)

    work["price"] = pd.to_numeric(work["price"], errors="coerce")
    work["duration"] = pd.to_numeric(work["duration"], errors="coerce")
    work["rating"] = pd.to_numeric(work["rating"], errors="coerce")

    work = work.drop_duplicates(subset=["name", "location", "price", "source"], keep="first")
    work = work[work["name"].notna() & (work["name"] != "") & (work["name"].str.lower() != "nan")]
    work = work[work["price"].notna()]

    # Default duration to 1 day when missing for single-night or generic listings.
    work["duration"] = work["duration"].fillna(1.0)
    work["duration"] = work["duration"].replace(0, 1.0)
    work["type"] = work["type"].replace("", "offer").fillna("offer")

    # Missing ratings: sample from observed ratings (same distribution, varied values).
    # Avoids filling ~100k rows with one median (e.g. all 4.5). Reproducible with seed.
    observed = pd.to_numeric(work["rating"], errors="coerce").dropna()
    missing = work["rating"].isna()
    n_miss = int(missing.sum())
    if n_miss > 0:
        if len(observed) > 0:
            rng = np.random.default_rng(42)
            draws = rng.choice(observed.to_numpy(dtype=float), size=n_miss, replace=True)
            work.loc[missing, "rating"] = draws
        else:
            # No observed ratings in this batch (e.g. only Kaggle ADR rows): spread values for charts/ML.
            rng = np.random.default_rng(42)
            work.loc[missing, "rating"] = rng.uniform(3.0, 5.0, size=n_miss)

    return work[EXPECTED_COLUMNS].reset_index(drop=True)
