"""
Review sentiment (VADER). Adds compound / pos / neg scores to enriched listings.
"""

from __future__ import annotations

import os

import pandas as pd

from utils.pipeline_paths import CLEAN_DATA_CSV, ENRICHED_LISTINGS_CSV

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:
    SentimentIntensityAnalyzer = None  # type: ignore


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))


def _scores(text: str, analyzer: SentimentIntensityAnalyzer) -> dict:
    if not text or str(text).strip() == "" or str(text).lower() == "nan":
        return {"compound": 0.0, "pos": 0.0, "neu": 1.0, "neg": 0.0}
    return analyzer.polarity_scores(str(text))


def run_sentiment(input_path: str = CLEAN_DATA_CSV, output_path: str = ENRICHED_LISTINGS_CSV) -> pd.DataFrame:
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Missing {input_path}. Run merge first.")

    df = pd.read_csv(input_path, encoding="utf-8")
    if df.empty:
        df.to_csv(output_path, index=False, encoding="utf-8")
        print("[sentiment] Empty input; wrote empty enriched file.")
        return df

    if "review_text" not in df.columns:
        df["review_text"] = pd.NA

    if SentimentIntensityAnalyzer is None:
        print("[sentiment] vaderSentiment not installed; copying clean_data without sentiment columns.")
        df.to_csv(output_path, index=False, encoding="utf-8")
        return df

    analyzer = SentimentIntensityAnalyzer()
    compounds = []
    pos = []
    neg = []
    neu = []
    for val in df["review_text"].fillna(""):
        s = _scores(str(val), analyzer)
        compounds.append(s["compound"])
        pos.append(s["pos"])
        neg.append(s["neg"])
        neu.append(s["neu"])

    out = df.copy()
    out["sentiment_compound"] = compounds
    out["sentiment_pos"] = pos
    out["sentiment_neg"] = neg
    out["sentiment_neu"] = neu

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    out.to_csv(output_path, index=False, encoding="utf-8")
    print(f"[sentiment] Enriched listings -> {output_path}")
    return out


if __name__ == "__main__":
    run_sentiment()
