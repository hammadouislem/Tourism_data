"""Load KEY=VALUE pairs from a project .env file into os.environ (no extra dependency)."""

import os
from typing import Optional


def load_project_dotenv(root_dir: Optional[str] = None, override: bool = True) -> None:
    """
    Read .env from root_dir (default: repo root = parent of utils/).

    override=True (default): each KEY=VALUE in the file overwrites os.environ for that KEY.
    This fixes the case where KAGGLE_USERNAME / KAGGLE_KEY exist but are empty strings
    (IDE or shell), which previously blocked real values from .env from being applied.

    override=False: only set variables that are not already present in os.environ.

    Uses utf-8-sig so files saved with a UTF-8 BOM on Windows still parse.
    """
    if root_dir is None:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root_dir, ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, encoding="utf-8-sig") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                if not key:
                    continue
                value = value.strip().strip('"').strip("'")
                if override:
                    os.environ[key] = value
                elif key not in os.environ:
                    os.environ[key] = value
    except OSError:
        pass
