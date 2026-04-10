"""
Download the 'Hotel Booking Demand' dataset from Kaggle into data/kaggle/.

Credentials (pick one):
  - Project .env: KAGGLE_USERNAME and KAGGLE_KEY (same as in kaggle.json from Kaggle → API).
    This script copies them into ~/.kaggle/kaggle.json so the Kaggle client can authenticate
    reliably on Windows (env-only auth often fails).

  - Or place kaggle.json manually under C:\\Users\\<You>\\.kaggle\\

Then: pip install kaggle
     python scripts/download_kaggle_hotel_booking.py

Dataset: https://www.kaggle.com/datasets/jessemostipak/hotel-booking-demand
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.dirname(SCRIPT_DIR))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from utils.kaggle_credentials import sync_kaggle_json_from_env

KAGGLE_DIR = os.path.join(ROOT, "data", "kaggle")


def main() -> None:
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("Install the Kaggle API client: pip install kaggle", file=sys.stderr)
        sys.exit(1)

    cfg_path = os.path.join(os.path.expanduser("~"), ".kaggle", "kaggle.json")
    synced = sync_kaggle_json_from_env(ROOT)
    if synced:
        print(f"[kaggle] Synced .env → {synced}")

    if not os.path.isfile(cfg_path):
        print(
            "Kaggle credentials not found.\n"
            f"Add to {os.path.join(ROOT, '.env')}:\n"
            "  KAGGLE_USERNAME=your_username\n"
            "  KAGGLE_KEY=your_api_key\n"
            "(From Kaggle → Settings → API — same values as in kaggle.json.)\n"
            "No spaces around '='. Save the file as UTF-8.",
            file=sys.stderr,
        )
        sys.exit(1)

    os.makedirs(KAGGLE_DIR, exist_ok=True)
    api = KaggleApi()
    api.authenticate()

    dataset = "jessemostipak/hotel-booking-demand"
    print(f"Downloading {dataset} -> {KAGGLE_DIR}")
    api.dataset_download_files(dataset, path=KAGGLE_DIR, unzip=True, quiet=False)

    print("Done. You should see hotel_booking.csv under data/kaggle/")
    print("Run: python main.py")


if __name__ == "__main__":
    main()
