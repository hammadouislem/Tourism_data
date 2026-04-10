import os
from typing import List, Optional

import pandas as pd

from processing.clean_data import clean_tourism_data


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
OUTPUT_PATH = os.path.join(ROOT_DIR, "output", "clean_data.csv")

# Default cap after merge (random sample, reproducible). PIPELINE_MAX_ROWS=0 disables.
_DEFAULT_MAX_ROWS = 30_000


def _pipeline_max_rows() -> Optional[int]:
    raw = os.environ.get("PIPELINE_MAX_ROWS", str(_DEFAULT_MAX_ROWS)).strip()
    if raw == "" or raw == "0":
        return None
    return int(raw)


def apply_row_cap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cap = _pipeline_max_rows()
    if cap is None or len(df) <= cap:
        return df

    # Prefer stratified sample by source so the cap is not "from the head" of concat order
    # and small sources still appear. Shuffle final rows for a random order.
    if "source" in df.columns and df["source"].nunique() > 1:
        try:
            from sklearn.model_selection import train_test_split

            strat = df["source"].astype(str)
            out, _ = train_test_split(
                df,
                train_size=cap,
                stratify=strat,
                random_state=42,
            )
            out = out.sample(frac=1, random_state=43).reset_index(drop=True)
            print(
                f"[merge_data] Capped to {cap:,} rows (stratified by `source`, "
                "then shuffled — PIPELINE_MAX_ROWS)"
            )
            return out
        except ValueError:
            pass

    out = df.sample(n=cap, random_state=42).reset_index(drop=True)
    out = out.sample(frac=1, random_state=43).reset_index(drop=True)
    print(f"[merge_data] Capped to {cap:,} rows (random sample + shuffle, PIPELINE_MAX_ROWS)")
    return out


def load_raw_files(data_dir: str = DATA_DIR) -> List[pd.DataFrame]:
    frames: List[pd.DataFrame] = []
    if not os.path.isdir(data_dir):
        return frames

    for filename in os.listdir(data_dir):
        if not filename.lower().endswith(".csv"):
            continue
        if not filename.lower().startswith("raw_"):
            continue
        full_path = os.path.join(data_dir, filename)
        try:
            frames.append(pd.read_csv(full_path, encoding="utf-8"))
            print(f"[merge_data] Loaded {filename}")
        except UnicodeDecodeError:
            frames.append(pd.read_csv(full_path, encoding="latin-1"))
            print(f"[merge_data] Loaded {filename} with latin-1")
        except (pd.errors.EmptyDataError, pd.errors.ParserError) as exc:
            print(f"[merge_data] Skipped empty/unreadable {filename}: {exc}")
        except Exception as exc:
            print(f"[merge_data] Failed {filename}: {exc}")
    return frames


def merge_and_clean(frames: List[pd.DataFrame]) -> pd.DataFrame:
    non_empty = [f for f in frames if f is not None and not f.empty]
    if not non_empty:
        merged = pd.DataFrame()
    else:
        merged = pd.concat(non_empty, ignore_index=True, sort=False)
    return clean_tourism_data(merged)


def run(
    data_dir: str = DATA_DIR,
    output_path: str = OUTPUT_PATH,
) -> pd.DataFrame:
    frames = load_raw_files(data_dir)
    clean_df = merge_and_clean(frames)
    clean_df = apply_row_cap(clean_df)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    clean_df.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[merge_data] Saved {len(clean_df)} rows -> {output_path}")
    return clean_df


if __name__ == "__main__":
    run()
