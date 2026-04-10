import os

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans

from utils.currency import cost_per_day_axis_label, price_axis_label
from utils.env_loader import load_project_dotenv
from utils.pipeline_paths import analytics_input_path

ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
INPUT_PATH = os.path.join(ROOT_DIR, "output", "clean_data.csv")
OUTPUT_RESULTS = os.path.join(ROOT_DIR, "output", "results.csv")
VIZ_DIR = os.path.join(ROOT_DIR, "output", "viz")
OUTPUT_PLOT = os.path.join(VIZ_DIR, "clusters.png")
CLUSTER_SIZES_PLOT = os.path.join(VIZ_DIR, "cluster_tier_counts.png")
MAX_POINTS_SCATTER = 25_000


def _label_cluster_tiers(centers_df: pd.DataFrame) -> dict:
    """
    Map cluster IDs to semantic tiers based on cluster center average price.
    Lowest price -> budget, middle -> mid-range, highest -> premium.
    """
    ordered = centers_df.sort_values("price").reset_index(drop=True)
    labels = ["budget", "mid-range", "premium"]
    return {int(ordered.loc[i, "cluster"]): labels[i] for i in range(min(3, len(ordered)))}


def _tier_colors() -> dict:
    return {
        "budget": "#22c55e",
        "mid-range": "#eab308",
        "premium": "#a855f7",
        "unclassified": "#94a3b8",
    }


def run_clustering(input_path=None, n_clusters: int = 3) -> pd.DataFrame:
    load_project_dotenv(ROOT_DIR)
    input_path = input_path or analytics_input_path()
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input not found: {input_path}. Run merge_data first.")

    df = pd.read_csv(input_path, encoding="utf-8")
    if df.empty:
        print("[clustering] No data to cluster.")
        return df

    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df["duration"] = pd.to_numeric(df["duration"], errors="coerce").replace(0, 1.0).fillna(1.0)
    df["cost_per_day"] = (df["price"] / df["duration"]).replace([float("inf"), float("-inf")], pd.NA)

    model_df = df.dropna(subset=["price", "cost_per_day"]).copy()
    if len(model_df) < n_clusters:
        print(f"[clustering] Not enough rows ({len(model_df)}) for {n_clusters} clusters.")
        return model_df

    features = model_df[["price", "cost_per_day"]]
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    model_df["cluster"] = kmeans.fit_predict(features)

    centers = pd.DataFrame(kmeans.cluster_centers_, columns=["price", "cost_per_day"])
    centers["cluster"] = centers.index
    cluster_name_map = _label_cluster_tiers(centers)
    model_df["cluster_label"] = model_df["cluster"].map(cluster_name_map).fillna("unclassified")

    os.makedirs(os.path.dirname(OUTPUT_RESULTS), exist_ok=True)
    os.makedirs(VIZ_DIR, exist_ok=True)
    model_df.to_csv(OUTPUT_RESULTS, index=False, encoding="utf-8")

    # Scatter: subsample for plotting only if huge
    plot_df = model_df
    if len(plot_df) > MAX_POINTS_SCATTER:
        plot_df = plot_df.sample(MAX_POINTS_SCATTER, random_state=42)

    colors_map = _tier_colors()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.set_facecolor("#fafafa")
    ax.grid(True, alpha=0.35, linestyle="--")
    for label, grp in plot_df.groupby("cluster_label"):
        col = colors_map.get(str(label).lower(), "#64748b")
        ax.scatter(
            grp["price"],
            grp["cost_per_day"],
            c=col,
            s=14,
            alpha=0.45,
            label=str(label),
            edgecolors="none",
        )
    ax.set_title("Price vs cost/day — K-means clusters (sampled if large)")
    ax.set_xlabel(price_axis_label())
    ax.set_ylabel(cost_per_day_axis_label())
    ax.legend(title="Tier", loc="upper left", framealpha=0.95)
    fig.tight_layout()
    fig.savefig(OUTPUT_PLOT, dpi=150, bbox_inches="tight")
    plt.close(fig)

    # Bar: cluster sizes
    counts = model_df["cluster_label"].value_counts()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.set_facecolor("#fafafa")
    ax.grid(True, axis="y", alpha=0.35, linestyle="--")
    bar_colors = [colors_map.get(str(i).lower(), "#64748b") for i in counts.index]
    ax.bar(counts.index.astype(str), counts.values, color=bar_colors, edgecolor="white", linewidth=0.5)
    ax.set_title("Listings per price tier")
    ax.set_ylabel("Count")
    fig.tight_layout()
    fig.savefig(CLUSTER_SIZES_PLOT, dpi=150, bbox_inches="tight")
    plt.close(fig)

    print(f"[clustering] Results -> {OUTPUT_RESULTS}")
    print(f"[clustering] Charts -> {VIZ_DIR}/")
    return model_df


if __name__ == "__main__":
    run_clustering()
