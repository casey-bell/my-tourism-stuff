"""
Clean and standardise overseas visitors dataset.

Normalises column names and types, derives quarterly period labels,
harmonises categorical fields, and returns a cleaned DataFrame with a
normalised schema suitable for downstream processing and tests. Optional
file-based helpers are provided for reading raw Excel and writing
Parquet.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd


# Default locations
RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")
DEFAULT_INPUT = RAW_DIR / "overseas-visitors-to-britain-2024.xlsx"
DEFAULT_OUTPUT = INTERIM_DIR / "visitors_clean.parquet"


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def _to_snake(s: str) -> str:
    s = s.strip()
    s = s.replace("£", "gbp")
    s = s.replace("(", "").replace(")", "")
    s = s.replace("/", " ").replace("-", " ")
    s = s.replace("%", "pct")
    s = " ".join(s.split())
    return "_".join(s.lower().split())


def _standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [_to_snake(c) for c in df.columns]

    # Canonical renames into the expected schema
    rename_map: Dict[str, str] = {
        # temporal
        "qtr": "quarter",
        "quarter": "quarter",
        "year": "year",
        "period": "period",  # may be parsed to year/quarter then rebuilt

        # metrics (expected: visits_thousands, expenditure_millions,
        # nights_thousands)
        "visits": "visits_thousands",
        "number_of_visits": "visits_thousands",
        "number_of_visits_thousands": "visits_thousands",
        "expenditure_gbp_millions": "expenditure_millions",
        "expenditure_millions": "expenditure_millions",
        "expenditure_gbp": "expenditure_millions",  # will be coerced later
        "nights": "nights_thousands",
        "number_of_nights": "nights_thousands",
        "nights_stayed_thousands": "nights_thousands",

        # categories
        "purpose_of_visit": "purpose",
        "mode_of_transport": "transport",
        "transport_mode": "transport",
        "region": "geography",
        "geographic_region": "geography",
        "country_of_residence": "country",
        "residence_country": "country",
        "uk_region_visited": "uk_region",
    }

    for k, v in rename_map.items():
        if k in df.columns and v not in df.columns:
            df.rename(columns={k: v}, inplace=True)

    return df


def _coerce_numerics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    def to_numeric(series: pd.Series) -> pd.Series:
        return pd.to_numeric(series, errors="coerce").astype("Float64")

    # Coerce metrics to numeric with expected names
    metric_cols = [
        "visits_thousands", "expenditure_millions", "nights_thousands"
    ]
    for col in metric_cols:
        if col in df.columns:
            df[col] = to_numeric(df[col])

    # If expenditure provided in GBP, convert to millions
    if "expenditure_millions" in df.columns:
        mask = df["expenditure_millions"] > 1_000_000
        if mask.any():
            logging.info("Converting expenditure from GBP to millions.")
            df.loc[mask, "expenditure_millions"] = (
                df.loc[mask, "expenditure_millions"] / 1_000_000
            )

    # Enforce non-negative values across numeric metrics
    for col in metric_cols:
        if col in df.columns:
            df[col] = df[col].clip(lower=0)

    return df


def _derive_quarter_and_period(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Try existing year + quarter codes
    if "year" in df.columns and "quarter" in df.columns:
        q = (df["quarter"].astype(str).str.upper()
             .str.extract(r"(\d)").squeeze())
        df["quarter"] = "Q" + q.fillna("").replace("", np.nan)

    # If only a free-form period is present, parse year and quarter from it
    if "period" in df.columns and (
        ("year" not in df.columns) or ("quarter" not in df.columns)
    ):
        period = df["period"].astype(str).str.upper()
        year = period.str.extract(r"(20\d{2})", expand=False)
        q = period.str.extract(r"Q([1-4])", expand=False)
        df["year"] = pd.to_numeric(year, errors="coerce")
        df["quarter"] = q.where(
            q.isin(["1", "2", "3", "4"]), np.nan
        ).map(lambda x: f"Q{x}" if pd.notna(x) else np.nan)

    # Build the expected string label 'period' as "Q# YYYY"
    if "year" in df.columns and "quarter" in df.columns:
        valid_q = df["quarter"].isin(["Q1", "Q2", "Q3", "Q4"])
        df.loc[valid_q, "period"] = (
            df.loc[valid_q, "quarter"] + " "
            + df.loc[valid_q, "year"].astype("Int64").astype(str)
        )
    else:
        df["period"] = pd.NA

    return df


def _normalise_categories(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Purpose of visit
    if "purpose" in df.columns:
        std = df["purpose"].astype(str).str.strip().str.lower()
        purpose_map = {
            "holiday": "Holiday",
            "leisure": "Holiday",
            "business": "Business",
            "vfr": "Visiting friends and relatives",
            "visiting friends and relatives": "Visiting friends and relatives",
            "visiting friends or relatives": "Visiting friends and relatives",
            "misc": "Miscellaneous",
            "miscellaneous": "Miscellaneous",
            "study": "Study",
        }
        df["purpose"] = std.map(lambda x: purpose_map.get(x, x.title()))

    # Transport mode
    if "transport" in df.columns:
        std = df["transport"].astype(str).str.strip().str.lower()
        transport_map = {
            "air": "Air",
            "sea": "Sea",
            "ferry": "Sea",
            "tunnel": "Tunnel",
            "rail": "Tunnel",
        }
        df["transport"] = std.map(lambda x: transport_map.get(x, x.title()))

    # Geography (macro regions)
    if "geography" in df.columns:
        std = df["geography"].astype(str).str.strip().str.lower()
        geography_map = {
            "europe": "Europe",
            "north america": "North America",
            "other countries": "Other Countries",
            "other": "Other Countries",
        }
        df["geography"] = std.map(lambda x: geography_map.get(x, x.title()))

    return df


def _add_coverage_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Coverage is United Kingdom up to 2023; Great Britain from 2024
    # onwards
    if "year" in df.columns:
        df["coverage"] = np.where(
            df["year"].fillna(0) >= 2024, "Great Britain",
            "United Kingdom"
        )
    else:
        df["coverage"] = pd.NA
    return df


def _finalise_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Produce the final DataFrame with the exact columns expected by tests:
    ['period', 'coverage', 'geography', 'purpose', 'transport',
     'visits_thousands', 'expenditure_millions', 'nights_thousands']
    """
    df = df.copy()

    # Ensure columns exist even if absent in input
    for col in [
        "period",
        "coverage",
        "geography",
        "purpose",
        "transport",
        "visits_thousands",
        "expenditure_millions",
        "nights_thousands",
    ]:
        if col not in df.columns:
            df[col] = pd.NA

    final_order = [
        "period",
        "coverage",
        "geography",
        "purpose",
        "transport",
        "visits_thousands",
        "expenditure_millions",
        "nights_thousands",
    ]

    # Return only the required columns in the defined order
    return df[final_order]


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pure cleaning function: accepts a DataFrame and returns a cleaned
    DataFrame. No file I/O occurs in this function (suitable for unit
    tests).
    """
    logging.info("Standardising column names.")
    df = _standardise_columns(df)

    logging.info("Coercing numeric fields.")
    df = _coerce_numerics(df)

    logging.info("Deriving quarter and period label.")
    df = _derive_quarter_and_period(df)

    logging.info("Normalising categorical values.")
    df = _normalise_categories(df)

    logging.info("Adding coverage flag.")
    df = _add_coverage_flag(df)

    logging.info("Finalising schema.")
    df = _finalise_schema(df)

    logging.info("Cleaning complete.")
    return df


def read_raw_excel(input_path: Path) -> pd.DataFrame:
    """
    Reads the raw Excel file and returns a DataFrame for cleaning.
    """
    logging.info(f"Reading raw data from: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logging.info("Reading worksheet '1' with header at row 9")
    return pd.read_excel(input_path, sheet_name="1", header=8, dtype=str)


def write_parquet(df: pd.DataFrame, output_path: Path) -> Path:
    """
    Writes a DataFrame to Parquet at the specified path.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    logging.info(f"Writing interim dataset to: {output_path}")
    df.to_parquet(output_path, index=False)
    return output_path


def clean_file(input_path: Path, output_path: Path) -> Path:
    """
    File-based cleaning entry point: reads raw Excel, cleans, and
    writes Parquet.
    """
    raw_df = read_raw_excel(input_path)
    cleaned_df = clean(raw_df)
    return write_parquet(cleaned_df, output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean and standardise the raw visitors dataset."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=DEFAULT_INPUT,
        help="Path to the raw Excel file.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Path to write the cleaned Parquet file.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clean_file(args.input, args.output)


if __name__ == "__main__":
    main()
