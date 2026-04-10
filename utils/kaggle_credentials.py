"""
Sync Kaggle credentials from project .env into ~/.kaggle/kaggle.json.

The Kaggle Python client (v2+) reads legacy API keys most reliably from kaggle.json.
Environment variables alone can fail on some Windows / IDE setups.
"""

from __future__ import annotations

import json
import os
import stat
from typing import Optional, Tuple


def load_credentials_from_dotenv(project_root: str) -> Tuple[str, str]:
    """Load .env with override, return (username, key). Supports KAGGLE_USER as alias."""
    from utils.env_loader import load_project_dotenv

    load_project_dotenv(project_root, override=True)
    user = (os.environ.get("KAGGLE_USERNAME") or os.environ.get("KAGGLE_USER") or "").strip()
    key = (os.environ.get("KAGGLE_KEY") or "").strip()
    return user, key


def write_kaggle_json(username: str, key: str) -> str:
    """Write ~/.kaggle/kaggle.json. Returns path written."""
    kaggle_dir = os.path.join(os.path.expanduser("~"), ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    path = os.path.join(kaggle_dir, "kaggle.json")
    payload = {"username": username, "key": key}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    try:
        os.chmod(path, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass
    return path


def sync_kaggle_json_from_env(project_root: str) -> Optional[str]:
    """
    If .env has KAGGLE_USERNAME + KAGGLE_KEY, write kaggle.json and return its path.
    Otherwise return None.
    """
    user, key = load_credentials_from_dotenv(project_root)
    if not user or not key:
        return None
    path = write_kaggle_json(user, key)
    # Ensure process env matches (some code paths read env only)
    os.environ["KAGGLE_USERNAME"] = user
    os.environ["KAGGLE_KEY"] = key
    return path
