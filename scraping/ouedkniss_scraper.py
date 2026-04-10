import os
from typing import List
from urllib.parse import urljoin

import pandas as pd
from bs4 import BeautifulSoup

from utils.helpers import fetch_html, normalize_whitespace, parse_price_to_float, sleep_between_requests
from utils.schema import write_raw_csv


DEFAULT_MARKETPLACE_URL = "https://www.ouedkniss.com/tourisme-voyages"
MAX_PAGES = 3
OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_ouedkniss.csv")

HOTEL_KEYWORDS = {"hotel", "resort", "inn", "hostel", "motel", "suite", "room", "accommodation"}


def classify_type(title: str) -> str:
    t = (title or "").lower()
    if any(k in t for k in HOTEL_KEYWORDS):
        return "hotel"
    return "offer"


def _extract_cards(soup: BeautifulSoup) -> List[dict]:
    rows: List[dict] = []
    cards = soup.select("article, .listing, .ad-item, .card")

    for card in cards:
        title_el = card.select_one("h2, h3, .title, [class*='title']")
        location_el = card.select_one(".location, [class*='location'], .city")
        price_el = card.select_one(".price, [class*='price'], .amount")

        title = normalize_whitespace(title_el.get_text(" ", strip=True)) if title_el else ""
        location = normalize_whitespace(location_el.get_text(" ", strip=True)) if location_el else ""
        price_raw = price_el.get_text(" ", strip=True) if price_el else ""

        if not title and not price_raw:
            continue

        rows.append(
            {
                "name": title or None,
                "type": classify_type(title),
                "location": location or None,
                "price": parse_price_to_float(price_raw),
                "duration": float("nan"),
                "rating": float("nan"),
                "source": "marketplace",
            }
        )
    return rows


def _find_next_page(base_url: str, soup: BeautifulSoup) -> str:
    next_el = soup.select_one("a[rel='next'], a.next, .pagination-next a")
    if not next_el or not next_el.get("href"):
        return ""
    return urljoin(base_url, next_el["href"])


def scrape_marketplace(url: str = DEFAULT_MARKETPLACE_URL, max_pages: int = MAX_PAGES, delay_seconds: float = 1.5) -> pd.DataFrame:
    all_rows: List[dict] = []
    current = url

    for page in range(1, max_pages + 1):
        if not current:
            break
        try:
            html = fetch_html(current)
            soup = BeautifulSoup(html, "html.parser")
            rows = _extract_cards(soup)
            all_rows.extend(rows)
            print(f"[ouedkniss_scraper] Page {page}: {len(rows)} rows")
            next_url = _find_next_page(current, soup)
            current = next_url
            sleep_between_requests(delay_seconds)
        except Exception as exc:
            print(f"[ouedkniss_scraper] Failed on page {page} ({current}): {exc}")
            break

    return pd.DataFrame(all_rows)


def run(output_path: str = OUTPUT_PATH, url: str = DEFAULT_MARKETPLACE_URL, max_pages: int = MAX_PAGES) -> pd.DataFrame:
    df = scrape_marketplace(url=url, max_pages=max_pages)
    write_raw_csv(df, output_path)
    print(f"[ouedkniss_scraper] Saved {len(df)} rows -> {output_path}")
    return df


if __name__ == "__main__":
    run()
