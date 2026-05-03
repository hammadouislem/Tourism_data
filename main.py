"""CLI entry for the tourism pipeline: python main.py"""

from __future__ import annotations


def main() -> None:
    from pipeline import run_pipeline

    run_pipeline()


if __name__ == "__main__":
    main()
