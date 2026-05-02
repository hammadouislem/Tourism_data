"""
Tourism data pipeline: collect (CSV feeds + external + Kaggle),
clean to CSV, ML insights (clustering + recommendations + sentiment), Plotly dashboard.

Run via: python main.py
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
from scraping.external_import import run as run_external_import
from scraping.source_specs import BOOKING_SPECS, TRIPADVISOR_SPECS
from scraping.tripadvisor_adapter import run_tripadvisor_adapter
from scraping.kaggle_hotel_booking_import import run as run_kaggle_booking_import
from visualization.dashboard import build_dashboard


def run_pipeline() -> None:
    print("[1/10] Importing external datasets (data/external + optional URL specs)...")
    run_external_import(source_specs=[])

    print("[2/10] Booking.com-style feed (CSV export / mapped columns)...")
    run_booking_adapter(feed_specs=BOOKING_SPECS)

    print("[3/10] TripAdvisor-style feed (CSV export / mapped columns)...")
    run_tripadvisor_adapter(feed_specs=TRIPADVISOR_SPECS)

    print("[4/10] Kaggle Hotel Booking Demand (auto-download if missing + import)...")
    run_kaggle_booking_import()

    print("[5/10] Merging + cleaning -> output/clean_data.csv ...")
    run_merge()

    print("[6/10] Sentiment (VADER) -> output/enriched_listings.csv ...")
    run_sentiment()

    print("[7/10] Insights (popular destinations, best-rated, price vs rating)...")
    run_insights()

    print("[8/10] Summary stats + price distribution chart...")
    run_analysis()

    print("[9/10] K-means clustering + recommendations...")
    run_clustering()
    run_recommendations()

    print("[10/10] Plotly dashboard (output/dashboard.html)...")
    build_dashboard()

    print("Pipeline complete. See output/ (and output/insights/).")


if __name__ == "__main__":
    run_pipeline()
