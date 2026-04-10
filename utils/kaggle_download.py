"""
Auto-download Kaggle 'Hotel Booking Demand' when hotel_booking.csv is missing.

Called from the pipeline so `python main.py` fetches data if credentials exist.
"""

from __future__ import annotations

import glob
import os
from typing import Optional

DATASET_SLUG = "jessemostipak/hotel-booking-demand"


def _has_data_rows(csv_path: str) -> bool:
    if not os.path.isfile(csv_path):
        return False
    try:
        with open(csv_path, encoding="utf-8", errors="replace") as f:
            for i, _ in enumerate(f):
                if i >= 1:
                    return True
        return False
    except OSError:
        return False


def find_hotel_booking_csv(kaggle_dir: str) -> Optional[str]:
    """Prefer hotel_booking.csv at root or anywhere under kaggle_dir."""
    if not os.path.isdir(kaggle_dir):
        return None
    for name in ("hotel_booking.csv", "Hotel_booking.csv", "hotel_bookings.csv", "Hotel_bookings.csv"):
        p = os.path.join(kaggle_dir, name)
        if os.path.isfile(p):
            return p
    for root, _, files in os.walk(kaggle_dir):
        for fn in files:
            low = fn.lower()
            if low in ("hotel_booking.csv", "hotel_bookings.csv"):
                return os.path.join(root, fn)
    csvs = glob.glob(os.path.join(kaggle_dir, "*.csv"))
    return csvs[0] if len(csvs) == 1 else None


def ensure_hotel_booking_csv(project_root: str) -> bool:
    """
    If data/kaggle/hotel_booking.csv (or equivalent) is missing, download via Kaggle API.
    Returns True if a usable CSV is present after this call, else False.
    """
    kaggle_dir = os.path.join(project_root, "data", "kaggle")
    existing = find_hotel_booking_csv(kaggle_dir)
    if existing and _has_data_rows(existing):
        print(f"[kaggle] Using existing dataset: {existing}")
        return True

    from utils.kaggle_credentials import sync_kaggle_json_from_env

    sync_kaggle_json_from_env(project_root)
    cfg = os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json")
    if not os.path.isfile(cfg):
        print(
            "[kaggle] Skipping download: no credentials. "
            "Set KAGGLE_USERNAME and KAGGLE_KEY in .env (or ~/.kaggle/kaggle.json)."
        )
        return False

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("[kaggle] Skipping download: install kaggle (pip install kaggle).")
        return False

    os.makedirs(kaggle_dir, exist_ok=True)
    try:
        api = KaggleApi()
        api.authenticate()
        print(f"[kaggle] Downloading {DATASET_SLUG} ...")
        api.dataset_download_files(DATASET_SLUG, path=kaggle_dir, unzip=True, quiet=False)
    except Exception as exc:
        print(f"[kaggle] Download failed: {exc}")
        return False

    found = find_hotel_booking_csv(kaggle_dir)
    if found and _has_data_rows(found):
        print(f"[kaggle] Ready: {found}")
        return True
    print("[kaggle] Download finished but hotel_booking.csv not found under data/kaggle/.")
    return False
