"""
Display currency for prices (charts, Streamlit, hover text).

Set PRICE_CURRENCY in .env to an ISO 4217 code (e.g. EUR, USD, GBP).
Numbers in CSVs are unchanged; only labels and formatting use this.
"""

from __future__ import annotations

import os
from typing import Optional

# ISO 4217 -> symbol for UI (extend as needed)
_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "JPY": "¥",
    "CHF": "CHF ",
    "CAD": "C$",
    "AUD": "A$",
    "NZD": "NZ$",
    "DZD": "د.ج ",
    "MAD": "DH ",
    "TND": "TND ",
    "XOF": "CFA ",
}


def get_currency_code() -> str:
    code = os.environ.get("PRICE_CURRENCY", "USD").strip().upper()
    return code if code else "USD"


def get_currency_symbol() -> str:
    return _SYMBOLS.get(get_currency_code(), f"{get_currency_code()} ")


def format_price(value: Optional[float]) -> str:
    if value is None:
        return "—"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "—"
    if v != v:  # NaN
        return "—"
    return f"{get_currency_symbol()}{v:,.2f}"


def price_axis_label() -> str:
    return f"Price ({get_currency_code()})"


def cost_per_day_axis_label() -> str:
    return f"Cost per day ({get_currency_code()})"


def mean_price_axis_label() -> str:
    return f"Mean price ({get_currency_code()})"
