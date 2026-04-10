import os
from typing import Dict, List

import pandas as pd

from scraping.external_import import import_sources
from utils.schema import combine_frames, write_raw_csv


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
OUTPUT_PATH = os.path.join(ROOT_DIR, "data", "raw_expedia_hotels.csv")


def run_expedia_hotels_adapter(feed_specs: List[Dict] = None, output_path: str = OUTPUT_PATH) -> pd.DataFrame:
    """Expedia/Hotels adapter using public feeds or exported datasets."""
    specs = feed_specs or []
    df = import_sources(specs)
    final_df = combine_frames([df])
    write_raw_csv(final_df, output_path)
    print(f"[expedia_hotels_adapter] Saved {len(final_df)} rows -> {output_path}")
    return final_df


if __name__ == "__main__":
    run_expedia_hotels_adapter()
