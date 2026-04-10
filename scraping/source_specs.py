"""
Configure external source specs here.

Each spec dictionary supports:
- name: source label
- path_or_url: local CSV path or direct CSV URL
- mapping: target -> source column map
- default_type: "offer" or "hotel"
"""

import os

_ROOT = os.path.dirname(os.path.dirname(__file__))
_FEEDS = os.path.join(_ROOT, "data", "feeds")

BOOKING_SPECS = [
    {
        "name": "booking:export_sample",
        "path_or_url": os.path.join(_FEEDS, "booking_export_sample.csv"),
        "mapping": {
            "name": "hotel_name",
            "location": "city",
            "price": "price_per_night",
            "duration": "nights",
            "rating": "rating",
            "type": "property_type",
            "review_text": "review_snippet",
        },
        "default_type": "hotel",
    },
]

TRIPADVISOR_SPECS = [
    {
        "name": "tripadvisor:export_sample",
        "path_or_url": os.path.join(_FEEDS, "tripadvisor_export_sample.csv"),
        "mapping": {
            "name": "title",
            "location": "destination",
            "price": "total_price",
            "duration": "days",
            "rating": "review_rating",
            "type": "attraction_type",
            "review_text": "review_excerpt",
        },
        "default_type": "offer",
    },
]
