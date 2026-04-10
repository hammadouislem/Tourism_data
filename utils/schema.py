import os
from typing import Dict, Iterable, Optional

import pandas as pd

from utils.helpers import parse_duration_to_days, parse_price_to_float


TARGET_COLUMNS = [
    "name",
    "type",
    "location",
    "price",
    "duration",
    "rating",
    "source",
    "review_text",
]


def map_to_unified_schema(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    source_name: str,
    default_type: str = "offer",
) -> pd.DataFrame:
    """
    Map arbitrary dataframe columns into project unified schema.
    mapping keys are target columns, values are source dataframe column names.
    """
    if df.empty:
        return pd.DataFrame(columns=TARGET_COLUMNS)

    out = pd.DataFrame()
    for target in TARGET_COLUMNS:
        source_col = mapping.get(target)
        if source_col and source_col in df.columns:
            out[target] = df[source_col]
        else:
            out[target] = pd.NA

    out["source"] = source_name
    out["type"] = out["type"].fillna(default_type)

    out["name"] = out["name"].astype(str).str.strip()
    out["location"] = out["location"].astype(str).str.strip()
    out["type"] = out["type"].astype(str).str.strip().str.lower()
    if "review_text" in out.columns:
        out["review_text"] = out["review_text"].apply(
            lambda v: pd.NA
            if v is None or (isinstance(v, float) and pd.isna(v)) or str(v).strip() == ""
            or str(v).strip().lower() == "nan"
            else str(v).strip()
        )

    out["price"] = out["price"].apply(parse_price_to_float)
    out["duration"] = out["duration"].apply(parse_duration_to_days)
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce")

    return out[TARGET_COLUMNS]


def combine_frames(frames: Iterable[Optional[pd.DataFrame]]) -> pd.DataFrame:
    """Combine non-empty dataframes into one standardized dataframe."""
    valid = [f for f in frames if f is not None and not f.empty]
    if not valid:
        return pd.DataFrame(columns=TARGET_COLUMNS)
    return pd.concat(valid, ignore_index=True, sort=False)


def write_raw_csv(df: pd.DataFrame, path: str) -> None:
    """
    Write raw scrape/import output. Empty results still emit a header row
    so merge can read the file without 'No columns to parse' errors.
    """
    if df.empty:
        out = pd.DataFrame(columns=TARGET_COLUMNS)
    else:
        out = df.copy()
        for col in TARGET_COLUMNS:
            if col not in out.columns:
                out[col] = pd.NA
        out = out[TARGET_COLUMNS]
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    out.to_csv(path, index=False, encoding="utf-8")
