import os
from typing import Dict, List

import pandas as pd

from utils.schema import combine_frames, map_to_unified_schema, write_raw_csv


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
EXTERNAL_DIR = os.path.join(DATA_DIR, "external")
OUTPUT_PATH = os.path.join(DATA_DIR, "raw_external.csv")


def _safe_read_csv(path_or_url: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path_or_url, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path_or_url, encoding="latin-1")


def import_sources(source_specs: List[Dict]) -> pd.DataFrame:
    """
    Import datasets from local files or URLs and map to unified schema.
    source_specs example:
    [
      {
        "name": "kaggle_hotels",
        "path_or_url": "https://.../dataset.csv",
        "mapping": {"name": "hotel_name", "location": "city", "price": "price", "rating": "rating"},
        "default_type": "hotel"
      }
    ]
    """
    frames = []
    for spec in source_specs:
        try:
            name = spec["name"]
            location = spec["path_or_url"]
            mapping = spec.get("mapping", {})
            default_type = spec.get("default_type", "offer")

            raw_df = _safe_read_csv(location)
            mapped = map_to_unified_schema(raw_df, mapping=mapping, source_name=name, default_type=default_type)
            frames.append(mapped)
            print(f"[external_import] {name} -> {len(mapped)} rows")
        except Exception as exc:
            print(f"[external_import] Failed import ({spec}): {exc}")

    return combine_frames(frames)


def load_local_external_csvs(external_dir: str = EXTERNAL_DIR) -> pd.DataFrame:
    """
    Auto-load all CSV files from data/external.
    Uses heuristic mapping for common column names.
    """
    if not os.path.isdir(external_dir):
        return pd.DataFrame()

    frames = []
    for filename in os.listdir(external_dir):
        if not filename.lower().endswith(".csv"):
            continue
        full_path = os.path.join(external_dir, filename)
        try:
            raw = _safe_read_csv(full_path)
            cols = {c.lower(): c for c in raw.columns}
            mapping = {
                "name": cols.get("name") or cols.get("title") or cols.get("hotel_name"),
                "type": cols.get("type"),
                "location": cols.get("location") or cols.get("city") or cols.get("destination"),
                "price": cols.get("price") or cols.get("avg_price"),
                "duration": cols.get("duration") or cols.get("days") or cols.get("duration_days"),
                "rating": cols.get("rating") or cols.get("review_score"),
                "review_text": cols.get("review_text")
                or cols.get("review_snippet")
                or cols.get("comments")
                or cols.get("user_review")
                or cols.get("review"),
            }
            source_name = f"external:{os.path.splitext(filename)[0]}"
            mapped = map_to_unified_schema(raw, mapping=mapping, source_name=source_name, default_type="offer")
            frames.append(mapped)
            print(f"[external_import] Loaded {filename} -> {len(mapped)} rows")
        except Exception as exc:
            print(f"[external_import] Failed {filename}: {exc}")

    return combine_frames(frames)


def run(source_specs: List[Dict] = None, output_path: str = OUTPUT_PATH) -> pd.DataFrame:
    os.makedirs(EXTERNAL_DIR, exist_ok=True)

    url_or_path_df = import_sources(source_specs or [])
    local_df = load_local_external_csvs()
    final_df = combine_frames([url_or_path_df, local_df]).drop_duplicates()

    write_raw_csv(final_df, output_path)
    print(f"[external_import] Saved {len(final_df)} rows -> {output_path}")
    return final_df


if __name__ == "__main__":
    run()
