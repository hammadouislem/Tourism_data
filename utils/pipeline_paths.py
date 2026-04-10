"""Shared paths for pipeline stages (clean vs sentiment-enriched)."""

import os

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")
CLEAN_DATA_CSV = os.path.join(OUTPUT_DIR, "clean_data.csv")
ENRICHED_LISTINGS_CSV = os.path.join(OUTPUT_DIR, "enriched_listings.csv")


def analytics_input_path() -> str:
    """Prefer enriched listings after sentiment; fall back to clean_data."""
    if os.path.isfile(ENRICHED_LISTINGS_CSV):
        return ENRICHED_LISTINGS_CSV
    return CLEAN_DATA_CSV
