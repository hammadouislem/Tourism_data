"""
Tourism data pipeline: collect (TripAdvisor/Booking-style feeds + scrapers),
clean to CSV, ML insights (clustering + recommendations + sentiment), Plotly dashboard.
"""

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from utils.env_loader import load_project_dotenv
from utils.kaggle_credentials import sync_kaggle_json_from_env

load_project_dotenv(SCRIPT_DIR)
sync_kaggle_json_from_env(SCRIPT_DIR)

from analysis.analysis import run_analysis
from analysis.clustering import run_clustering
from analysis.insights import run_insights
from analysis.recommendation import run_recommendations
from analysis.sentiment import run_sentiment
from processing.merge_data import run as run_merge
from scraping.booking_adapter import run_booking_adapter
from scraping.expedia_hotels_adapter import run_expedia_hotels_adapter
from scraping.external_import import run as run_external_import
from scraping.onat_scraper import run as run_official_scraper
from scraping.source_specs import (
    BOOKING_SPECS,
    EXPEDIA_HOTELS_SPECS,
    GENERIC_EXTERNAL_SPECS,
    TRIPADVISOR_SPECS,
)
from scraping.tripadvisor_adapter import run_tripadvisor_adapter
from scraping.kaggle_hotel_booking_import import run as run_kaggle_booking_import
from scraping.ouedkniss_scraper import run as run_market_scraper
from visualization.dashboard import build_dashboard


def run_pipeline() -> None:
    print("[1/13] Scraping official/agency offers...")
    run_official_scraper()

    print("[2/13] Scraping marketplace offers...")
    run_market_scraper()

    print("[3/13] Importing external datasets (data/external + optional URLs)...")
    run_external_import(source_specs=GENERIC_EXTERNAL_SPECS)

    print("[4/13] Booking.com-style feed (CSV export / mapped columns)...")
    run_booking_adapter(feed_specs=BOOKING_SPECS)

    print("[5/13] Expedia/Hotels adapter (optional export)...")
    run_expedia_hotels_adapter(feed_specs=EXPEDIA_HOTELS_SPECS)

    print("[6/13] TripAdvisor-style feed (CSV export / mapped columns)...")
    run_tripadvisor_adapter(feed_specs=TRIPADVISOR_SPECS)

    print("[7/13] Kaggle Hotel Booking Demand (auto-download if missing + import)...")
    run_kaggle_booking_import()

    print("[8/13] Merging + cleaning -> output/clean_data.csv ...")
    run_merge()

    print("[9/13] Sentiment (VADER) -> output/enriched_listings.csv ...")
    run_sentiment()

    print("[10/13] Insights (popular destinations, best-rated, price vs rating)...")
    run_insights()

    print("[11/13] Summary stats + price distribution chart...")
    run_analysis()

    print("[12/13] K-means clustering + recommendations...")
    run_clustering()
    run_recommendations()

    print("[13/13] Plotly dashboard (output/dashboard.html)...")
    build_dashboard()

    print("Pipeline complete. See output/ (and output/insights/).")


if __name__ == "__main__":
    run_pipeline()
