# Tourism Listings — Data Analysis Pipeline

**Authors:** HAMMADOU ISLEM · MOKKEDEM AKRAM · BOUKHELKHAL CHAMSEDDINE  

Modular pipeline for collecting, cleaning, analyzing, and visualizing tourism listings (scraping, CSV feeds, Kaggle-style exports), with ML clustering, recommendations, sentiment on reviews, and a Streamlit web app.

---

## Features

- **Collection:** Web scrapers + Booking / TripAdvisor-style CSV adapters + `data/external/` auto-import + optional Kaggle Hotel Booking Demand (`data/kaggle/`, `scraping/kaggle_hotel_booking_import.py`).
- **Cleaning:** Deduplication, duration defaults, **rating imputation** (sampled from observed ratings or uniform spread when none exist).
- **Row cap:** After merge, optional cap (default **30k** rows), stratified by `source` when possible (`PIPELINE_MAX_ROWS` in `.env`).
- **Analysis:** Summary by type, matplotlib charts under `output/viz/`, insights CSVs under `output/insights/`.
- **ML:** K-means price tiers, content-based recommendations (`analysis/recommendation.py`).
- **Sentiment:** VADER on `review_text` → `output/enriched_listings.csv`.
- **Visualization:** Plotly dashboard → `output/dashboard.html`; display currency via `PRICE_CURRENCY` in `.env` (e.g. EUR, USD).
- **Web app:** `streamlit run streamlit_app.py`.

---

## Project layout

```text
tourism_analysis/
├── analysis/          # analysis, clustering, insights, sentiment, recommendation
├── processing/      # clean_data, merge_data
├── scraping/        # scrapers, adapters, Kaggle import, external_import
├── visualization/   # Plotly dashboard (HTML + figure for Streamlit)
├── utils/             # schema, env, currency, Kaggle helpers
├── scripts/           # download_kaggle_hotel_booking.py
├── data/
│   ├── feeds/         # sample Booking / TripAdvisor-style CSVs
│   ├── external/      # extra CSVs (auto-loaded)
│   └── kaggle/        # hotel_booking*.csv after download (gitignored)
├── output/
│   ├── clean_data.csv
│   ├── enriched_listings.csv
│   ├── results.csv
│   ├── dashboard.html
│   ├── viz/           # matplotlib PNGs
│   └── insights/
├── main.py
├── streamlit_app.py
├── requirements.txt
└── README.md
```

---

## Data schema (unified)

| Field         | Description                          |
|--------------|--------------------------------------|
| name, type   | Listing title and category           |
| location     | City / country / destination         |
| price        | Numeric (display currency in `.env`) |
| duration     | Days                                 |
| rating       | Numeric (imputed if missing)         |
| source       | Origin label                         |
| review_text  | Optional, for sentiment              |

---

## How to run

### 1. Install

```bash
pip install -r requirements.txt
```

### 2. Environment (optional)

Copy `.env.example` to `.env` and set:

- `KAGGLE_USERNAME` / `KAGGLE_KEY` — for Kaggle API download (or place `kaggle.json` in `~/.kaggle/`).
- `PIPELINE_MAX_ROWS` — default `30000`; use `0` for no cap.
- `PRICE_CURRENCY` — e.g. `EUR`, `USD` (labels only).

### 3. Full pipeline

```bash
python main.py
```

Outputs: `output/clean_data.csv`, `enriched_listings.csv`, `results.csv`, `dashboard.html`, `output/viz/*.png`, `output/insights/*`.

### 4. Kaggle dataset (optional)

```bash
python scripts/download_kaggle_hotel_booking.py
```

Or rely on auto-download during `main.py` if credentials and missing CSV are configured (see `data/kaggle/README.txt`).

### 5. Web UI

```bash
python -m streamlit run streamlit_app.py
```

---

## Configure CSV sources

Edit **`scraping/source_specs.py`** for Booking/TripAdvisor feed paths and column mappings. Drop additional CSVs into **`data/external/`** (heuristic column mapping applies).

---

## Notes on sources and ethics

- Respect each site’s **terms of use**; prefer **exported CSVs** or **public datasets** over aggressive scraping.
- Update selectors in scrapers when HTML changes.
- Kaggle data: follow the dataset license on the Kaggle page.

---

## Requirements

Python 3.10+ recommended. Main libraries: `pandas`, `scikit-learn`, `matplotlib`, `plotly`, `vaderSentiment`, `streamlit`, `kaggle` (optional, for download script).
