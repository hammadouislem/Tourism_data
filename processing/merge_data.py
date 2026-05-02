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


def _proportional_stratified_cap(df: pd.DataFrame, cap: int) -> Optional[pd.DataFrame]:
    """Optional: keep original population mix (charts mirror raw skew)."""
    if "source" not in df.columns or df["source"].nunique() <= 1:
        return None
    try:
        from sklearn.model_selection import train_test_split

        strat = df["source"].astype(str)
        out, _ = train_test_split(df, train_size=cap, stratify=strat, random_state=42)
        return out.sample(frac=1, random_state=43).reset_index(drop=True)
    except ValueError:
        return None


def _balanced_random_cap(df: pd.DataFrame, cap: int) -> pd.DataFrame:
    """
    ~Equal random draw per `source` (up to cap), then fill any shortfall randomly.
    Makes source mix in charts more even than proportional stratified sampling.
    """
    work = df.reset_index(drop=True)
    src = work["source"].astype(str)
    sources = sorted(src.unique())
    k = len(sources)
    per = cap // k
    remainder = cap % k
    chosen: list[int] = []
    for i, s in enumerate(sources):
        idx = work.index[src == s].tolist()
        n_take = min(len(idx), per + (1 if i < remainder else 0))
        if n_take <= 0:
            continue
        picked = work.loc[idx].sample(n=n_take, random_state=42 + i).index.tolist()
        chosen.extend(picked)
    chosen_set = set(chosen)
    if len(chosen) < cap:
        pool = [i for i in work.index if i not in chosen_set]
        need = min(cap - len(chosen), len(pool))
        if need > 0:
            extra = work.loc[pool].sample(n=need, random_state=99).index.tolist()
            chosen.extend(extra)
    out = work.loc[chosen]
    return out.sample(frac=1, random_state=43).reset_index(drop=True)


def apply_row_cap(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    cap = _pipeline_max_rows()
    proportional = os.environ.get("PIPELINE_PROPORTIONAL_SAMPLE", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )

    if cap is None or len(df) <= cap:
        out = df.sample(frac=1, random_state=43).reset_index(drop=True)
        if cap is None:
            print("[merge_data] No row cap (PIPELINE_MAX_ROWS=0); shuffled row order.")
        else:
            print("[merge_data] Row count under cap; shuffled row order.")
        return out

    if proportional:
        out = _proportional_stratified_cap(df, cap)
        if out is not None:
            print(
                f"[merge_data] Capped to {cap:,} rows (proportional by `source`, "
                "PIPELINE_PROPORTIONAL_SAMPLE) + shuffle."
            )
            return out
    elif "source" in df.columns and df["source"].nunique() > 1:
        out = _balanced_random_cap(df, cap)
        print(
            f"[merge_data] Capped to {len(out):,} rows (balanced random per `source`, "
            f"target {cap:,} — PIPELINE_MAX_ROWS)."
        )
        return out

    out = df.sample(n=cap, random_state=42).reset_index(drop=True)
    out = out.sample(frac=1, random_state=43).reset_index(drop=True)
    print(f"[merge_data] Capped to {cap:,} rows (uniform random + shuffle, PIPELINE_MAX_ROWS)")
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
