import re


def parse_price_to_float(raw: str) -> float:
    """Extract numeric price from mixed text like '$1,250 / night'."""
    if raw is None:
        return float("nan")
    text = str(raw).replace(",", " ").replace("\u00a0", " ")
    match = re.findall(r"\d+(?:[.,]\d+)?", text)
    if not match:
        return float("nan")
    number = match[0].replace(",", ".")
    try:
        return float(number)
    except ValueError:
        return float("nan")


def parse_duration_to_days(raw: str) -> float:
    """
    Parse duration text into days.
    Examples:
    - '7 days' -> 7
    - '2 weeks' -> 14
    - '48h' -> 2
    """
    if raw is None:
        return float("nan")

    text = str(raw).lower().strip()
    number_match = re.findall(r"\d+(?:[.,]\d+)?", text)
    if not number_match:
        return float("nan")

    try:
        value = float(number_match[0].replace(",", "."))
    except ValueError:
        return float("nan")

    if "week" in text:
        return round(value * 7, 2)
    if "hour" in text or "hr" in text or "h" == text[-1:]:
        return round(value / 24.0, 2)
    if "night" in text:
        return round(value, 2)
    return round(value, 2)
