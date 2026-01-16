#!/usr/bin/env python3
# Placeholder cleaning script for tourism data.
#
# This module provides a minimal scaffold for turning raw source files into
# cleaned, analysis-ready datasets. It is intentionally lightweight so it can be
# adapted to your repository’s actual data contracts.
#
# CLI usage example:
#     python scripts/clean_data.py \
#         --input data/raw/source.csv \
#         --output data/interim/source_clean.parquet \
#         --schema config/schemas/tourism_schema.json \
#         --source-name VisitStats2024

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path as _Path
from typing import Dict, Optional

import pandas as pd

# ----------------------------
# Logging setup
# ----------------------------
logger = logging.getLogger("clean_data")
handler = logging.StreamHandler()
formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


# ----------------------------
# Core cleaning utilities
# ----------------------------
def load_raw(input_path: _Path) -> pd.DataFrame:
    """Load a raw file into a DataFrame based on extension (.csv, .parquet)."""
    input_path = _Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info("Loading raw data from %s", input_path)
    ext = input_path.suffix.lower()

    if ext == ".csv":
        return pd.read_csv(input_path)
    if ext == ".parquet":
        return pd.read_parquet(input_path)

    raise ValueError(f"Unsupported input extension: {ext}")


def standardise_columns(df: pd.DataFrame, column_map: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """Return a copy with standardised column names and optional explicit renames.

    - Lowercase columns
    - Replace spaces and hyphens with underscores
    - Apply optional explicit renames via column_map (after normalisation)
    """
    out = df.copy()

    def normalise(col: str) -> str:
        return (
            col.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
        )

    out.columns = [normalise(c) for c in out.columns]

    if column_map:
        out = out.rename(columns={normalise(k): v for k, v in column_map.items()})

    return out


def trim_whitespace(df: pd.DataFrame) -> pd.DataFrame:
    """Trim leading/trailing whitespace in all object (string-like) columns."""
    out = df.copy()
    for col in out.select_dtypes(include=["object", "string"]).columns:
        out[col] = out[col].astype("string").str.strip()
    return out


def to_lowercase(df: pd.DataFrame, columns: Optional[list[str]] = None) -> pd.DataFrame:
    """Lowercase textual columns to reduce casing variability."""
    out = df.copy()
    target_cols = columns or list(out.select_dtypes(include=["object", "string"]).columns)
    for col in target_cols:
        out[col] = out[col].astype("string").str.lower()
    return out


def coerce_types(df: pd.DataFrame, schema: Optional[Dict[str, str]] = None) -> pd.DataFrame:
    """Coerce column dtypes using a simple schema mapping (name -> pandas dtype).

    Example schema entries: {"arrivals": "Int64", "spend": "float64"}
    """
    out = df.copy()
    if not schema:
        return out

    for col, dtype in schema.items():
        if col in out.columns:
            try:
                out[col] = out[col].astype(dtype)
            except Exception as exc:
                logger.warning("Failed to cast column '%s' to %s: %s", col, dtype, exc)
    return out


def parse_dates(df: pd.DataFrame, date_cols: Optional[list[str]] = None) -> pd.DataFrame:
    """Parse date columns with pandas.to_datetime (errors='coerce')."""
    out = df.copy()
    if not date_cols:
        return out
    for col in date_cols:
        if col in out.columns:
            out[col] = pd.to_datetime(out[col], errors="coerce")
    return out


def add_lineage(df: pd.DataFrame, source_name: str, loaded_at: Optional[datetime] = None) -> pd.DataFrame:
    """Attach basic lineage metadata columns."""
    out = df.copy()
    out["_source_name"] = source_name
    out["_loaded_at"] = (loaded_at or datetime.utcnow()).isoformat()
    return out


def basic_clean(
    input_path: _Path,
    column_map: Optional[Dict[str, str]] = None,
    type_schema: Optional[Dict[str, str]] = None,
    date_cols: Optional[list[str]] = None,
    source_name: str = "unknown_source",
) -> pd.DataFrame:
    """End-to-end basic cleaning pipeline for a single file."""
    df = load_raw(input_path)
    df = standardise_columns(df, column_map=column_map)
    df = trim_whitespace(df)
    df = to_lowercase(df)
    df = coerce_types(df, schema=type_schema)
    df = parse_dates(df, date_cols=date_cols)
    df = add_lineage(df, source_name=source_name)
    logger.info("Finished basic cleaning (%s rows, %s columns)", len(df), len(df.columns))
    return df


# ----------------------------
# I/O helpers
# ----------------------------
def save_output(df: pd.DataFrame, output_path: _Path) -> None:
    output_path = _Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ext = output_path.suffix.lower()
    if ext == ".csv":
        df.to_csv(output_path, index=False)
    elif ext == ".parquet":
        df.to_parquet(output_path, index=False)
    else:
        raise ValueError(f"Unsupported output extension: {ext}")

    logger.info("Wrote cleaned data to %s", output_path)


# ----------------------------
# CLI
# ----------------------------
def _load_json(path: Optional[_Path]) -> Optional[dict]:
    if not path:
        return None
    p = _Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean raw tourism data into an analysis-ready format.")
    parser.add_argument("--input", required=True, type=_Path, help="Path to raw input file (.csv or .parquet)")
    parser.add_argument("--output", required=True, type=_Path, help="Destination for cleaned file (.csv or .parquet)")
    parser.add_argument("--schema", type=_Path, default=None, help="Optional JSON schema mapping column -> pandas dtype")
    parser.add_argument("--column-map", type=_Path, default=None, help="Optional JSON of explicit column renames {raw: standard}")
    parser.add_argument("--date-cols", type=str, default="", help="Comma-separated list of date columns to parse after standardisation")
    parser.add_argument("--source-name", type=str, default="unknown_source", help="Lineage label for _source_name")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    type_schema = _load_json(args.schema)
    column_map = _load_json(args.column_map)
    date_cols = [c.strip() for c in args.date_cols.split(",") if c.strip()] if args.date_cols else None

    df = basic_clean(
        input_path=args.input,
        column_map=column_map,
        type_schema=type_schema,
        date_cols=date_cols,
        source_name=args.source_name,
    )

    save_output(df, args.output)


if __name__ == "__main__":
    main()
