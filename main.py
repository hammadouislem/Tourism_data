"""
CLI entry only. Keeps top-level imports minimal so Vercel can load this file safely
when scanning Python entrypoints (pipeline deps are not installed on Vercel).

Run the full pipeline: python main.py
"""

from __future__ import annotations


def main() -> None:
    from pipeline import run_pipeline

    run_pipeline()


if __name__ == "__main__":
    main()
