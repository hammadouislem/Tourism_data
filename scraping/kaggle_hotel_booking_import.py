"""
Map Kaggle 'Hotel Booking Demand' (jessemostipak/hotel-booking-demand) into the project schema.

Download first (see scripts/download_kaggle_hotel_booking.py), then run main.py.
Columns used: hotel, country, adr, stays_in_weekend_nights, stays_in_week_nights.
Ratings are not in this dataset — filled as NA and imputed in cleaning.
"""

from __future__ import annotations

import glob
import os
from typing import Optional

import pandas as pd

from utils.schema import TARGET_COLUMNS, write_raw_csv


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
KAGGLE_DIR = os.path.join(ROOT_DIR, "data", "kaggle")
OUTPUT_PATH = os.path.join(ROOT_DIR, "data", "raw_kaggle_bookings.csv")


def _find_source_csv(directory: str) -> Optional[str]:
    if not os.path.isdir(directory):
        return None
    for name in ("hotel_booking.csv", "Hotel_booking.csv", "hotel_bookings.csv", "Hotel_bookings.csv"):
        p = os.path.join(directory, name)
        if os.path.isfile(p):
            return p
    for root, _, files in os.walk(directory):
        for fn in files:
            low = fn.lower()
            if low in ("hotel_booking.csv", "hotel_bookings.csv"):
                return os.path.join(root, fn)
    csvs = glob.glob(os.path.join(directory, "*.csv"))
    return csvs[0] if len(csvs) == 1 else None


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def transform_booking_demand(
    df: pd.DataFrame,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """Build unified rows from the raw Kaggle hotel booking table."""
    df = _normalize_columns(df)
    required = {"hotel", "country", "adr", "stays_in_weekend_nights", "stays_in_week_nights"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Unexpected CSV columns. Missing: {missing}. Found: {list(df.columns)[:30]}...")

    if max_rows is not None and max_rows > 0:
        df = df.head(int(max_rows)).copy()

    weekend = pd.to_numeric(df["stays_in_weekend_nights"], errors="coerce").fillna(0)
    week = pd.to_numeric(df["stays_in_week_nights"], errors="coerce").fillna(0)
    duration = (weekend + week).clip(lower=1)

    price = pd.to_numeric(df["adr"], errors="coerce")
    hotel = df["hotel"].astype(str).str.strip()
    country = df["country"].astype(str).str.strip()

    out = pd.DataFrame(
        {
            "name": hotel + " — booking " + (df.index.astype(int) + 1).astype(str),
            "type": "hotel",
            "location": country,
            "price": price,
            "duration": duration,
            "rating": pd.NA,
            "source": "kaggle:hotel_booking_demand",
            "review_text": pd.NA,
        }
    )
    out = out.dropna(subset=["price"])
    return out[TARGET_COLUMNS]


def run(
    source_path: Optional[str] = None,
    output_path: str = OUTPUT_PATH,
    max_rows: Optional[int] = None,
) -> pd.DataFrame:
    """
    If Kaggle CSV is present, map it to raw_kaggle_bookings.csv.
    max_rows: limit rows for faster runs (env KAGGLE_BOOKING_MAX_ROWS), or None for all.
    """
    if source_path is None:
        from utils.kaggle_download import ensure_hotel_booking_csv

        ensure_hotel_booking_csv(ROOT_DIR)

    path = source_path or _find_source_csv(KAGGLE_DIR)
    if not path or not os.path.isfile(path):
        print(
            "[kaggle_hotel_booking] No hotel_booking.csv under data/kaggle/. "
            "Add .env credentials (KAGGLE_USERNAME, KAGGLE_KEY) and re-run, or run: "
            "python scripts/download_kaggle_hotel_booking.py"
        )
        write_raw_csv(pd.DataFrame(), output_path)
        return pd.DataFrame(columns=TARGET_COLUMNS)

    env_max = os.environ.get("KAGGLE_BOOKING_MAX_ROWS", "").strip()
    if max_rows is None and env_max:
        try:
            max_rows = int(env_max)
        except ValueError:
            max_rows = None

    print(f"[kaggle_hotel_booking] Reading {path} ...")
    raw = pd.read_csv(path, encoding="utf-8", low_memory=False)
    try:
        mapped = transform_booking_demand(raw, max_rows=max_rows)
    except ValueError as exc:
        print(f"[kaggle_hotel_booking] Skipping: {exc}")
        write_raw_csv(pd.DataFrame(), output_path)
        return pd.DataFrame(columns=TARGET_COLUMNS)

    write_raw_csv(mapped, output_path)
    print(f"[kaggle_hotel_booking] Saved {len(mapped)} rows -> {output_path}")
    return mapped


if __name__ == "__main__":
    run()
