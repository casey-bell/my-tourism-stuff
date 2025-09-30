# src/pipeline.py
from __future__ import annotations

import sys
import logging
import argparse
from pathlib import Path

import pandas as pd

from src.data.load import load_raw_excel
from src.data.clean import clean_visitors
from src.data.transform import to_quarterly_aggregates, write_outputs


def configure_logging(quiet: bool = False) -> None:
    level = logging.WARNING if quiet else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run(
    raw_path: str = "data/raw/overseas-visitors-to-britain-2024.xlsx",
    interim_dir: str = "data/interim",
    processed_dir: str = "data/processed",
) -> None:
    raw_file = Path(raw_path)
    interim = Path(interim_dir)
    processed = Path(processed_dir)

    if not raw_file.exists():
        logging.error(f"Raw data not found at: {raw_file}")
        sys.exit(1)

    interim.mkdir(parents=True, exist_ok=True)
    processed.mkdir(parents=True, exist_ok=True)

    logging.info(f"Loading raw data from: {raw_file}")
    df_raw = load_raw_excel(str(raw_file))

    logging.info("Cleaning dataset")
    df_clean = clean_visitors(df_raw)

    interim_out = interim / "visitors_interim.parquet"
    logging.info(f"Writing interim output to: {interim_out}")
    df_clean.to_parquet(interim_out, index=False)

    logging.info("Creating quarterly aggregates")
    df_quarterly = to_quarterly_aggregates(df_clean)

    logging.info(f"Writing processed outputs to: {processed}")
    write_outputs(df_quarterly, out_dir=str(processed))

    logging.info("Pipeline complete")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the tourism data pipeline: load → clean → aggregate → write"
    )
    parser.add_argument(
        "--raw-path",
        default="data/raw/overseas-visitors-to-britain-2024.xlsx",
        help="Path to the raw Excel file",
    )
    parser.add_argument(
        "--interim-dir",
        default="data/interim",
        help="Directory for interim outputs",
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Directory for processed outputs",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Reduce log verbosity",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    configure_logging(quiet=args.quiet)
    try:
        run(
            raw_path=args.raw_path,
            interim_dir=args.interim_dir,
            processed_dir=args.processed_dir,
        )
    except Exception as exc:
        logging.exception(f"Pipeline failed: {exc}")
        sys.exit(1)
