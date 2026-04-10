import os
from typing import List

import pandas as pd
from bs4 import BeautifulSoup

from utils.helpers import fetch_html, normalize_whitespace, parse_duration_to_days, parse_price_to_float
from utils.schema import write_raw_csv


DEFAULT_OFFER_URLS: List[str] = [
    # Replace these with pages that match your current target markets.
    "https://www.onat.dz/",
]

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_onat.csv")


def _extract_offer_cards(soup: BeautifulSoup) -> List[dict]:
    """Extract tourism offers from common card-like HTML patterns."""
    rows: List[dict] = []
    cards = soup.select(".offer-card, .card, article, .tour-item, .product")

    for card in cards:
        title_el = card.select_one(".title, .offer-title, h2, h3")
        location_el = card.select_one(".location, .destination, .city")
        price_el = card.select_one(".price, .amount, [class*='price']")
        duration_el = card.select_one(".duration, [class*='duration']")
        rating_el = card.select_one(".rating, [class*='rating']")

        name = normalize_whitespace(title_el.get_text(" ", strip=True)) if title_el else ""
        location = normalize_whitespace(location_el.get_text(" ", strip=True)) if location_el else ""
        price_raw = price_el.get_text(" ", strip=True) if price_el else ""
        duration_raw = duration_el.get_text(" ", strip=True) if duration_el else ""
        rating_raw = rating_el.get_text(" ", strip=True) if rating_el else ""

        if not name and not price_raw:
            continue

        rows.append(
            {
                "name": name or None,
                "type": "offer",
                "location": location or None,
                "price": parse_price_to_float(price_raw),
                "duration": parse_duration_to_days(duration_raw),
                "rating": parse_price_to_float(rating_raw),
                "source": "onat_like_site",
            }
        )

    return rows


def scrape_onat_like_sources(urls: List[str] = None) -> pd.DataFrame:
    """Scrape offer-like pages from official or agency tourism websites."""
    target_urls = urls or DEFAULT_OFFER_URLS
    all_rows: List[dict] = []

    for url in target_urls:
        try:
            html = fetch_html(url)
            soup = BeautifulSoup(html, "html.parser")
            rows = _extract_offer_cards(soup)
            all_rows.extend(rows)
            print(f"[onat_scraper] {url} -> {len(rows)} rows")
        except Exception as exc:
            print(f"[onat_scraper] Failed {url}: {exc}")

    return pd.DataFrame(all_rows)


def run(output_path: str = OUTPUT_PATH, urls: List[str] = None) -> pd.DataFrame:
    df = scrape_onat_like_sources(urls=urls)
    write_raw_csv(df, output_path)
    print(f"[onat_scraper] Saved {len(df)} rows -> {output_path}")
    return df


if __name__ == "__main__":
    run()
