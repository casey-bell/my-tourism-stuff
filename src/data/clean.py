"""
Clean and standardise overseas visitors dataset.

Reads the raw Excel file, normalises column names and types, derives quarterly periods,
harmonises categorical fields, and writes an interim Parquet dataset for downstream use.
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Optional, Dict

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

    # Common renames into a consistent schema if present
    rename_map: Dict[str, str] = {
        "year": "year",
        "qtr": "quarter",
        "quarter": "quarter",
        "period": "period",
        "visits": "visits",
        "number_of_visits": "visits",
        "expenditure_gbp_millions": "expenditure_millions",
        "expenditure_millions": "expenditure_millions",
        "expenditure_gbp": "expenditure_millions",  # will be coerced later
        "nights": "nights",
        "number_of_nights": "nights",
        "purpose": "purpose",
        "purpose_of_visit": "purpose",
        "mode_of_transport": "transport",
        "transport_mode": "transport",
        "region": "region",
        "geographic_region": "region",
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
        return (
            pd.to_numeric(series, errors="coerce")
            .astype("Float64")
        )

    for col in ["visits", "expenditure_millions", "nights"]:
        if col in df.columns:
            df[col] = to_numeric(df[col])

    # If expenditure provided in GBP, convert to millions
    if "expenditure_millions" in df.columns:
        # Detect very large numbers likely in GBP
        mask = df["expenditure_millions"] > 1_000_000
        if mask.any():
            logging.info("Converting expenditure from GBP to millions.")
            df.loc[mask, "expenditure_millions"] = df.loc[mask, "expenditure_millions"] / 1_000_000

    return df


def _derive_quarter(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Try existing year + quarter codes
    if "year" in df.columns and "quarter" in df.columns:
        # Normalise quarter values like "Q1", 1, "1" → "Q1"
        q = df["quarter"].astype(str).str.upper().str.extract(r"(\d)").squeeze()
        df["quarter"] = "Q" + q.fillna("").replace("", np.nan)
    elif "period" in df.columns:
        # Attempt to parse strings like "2024 Q1" or "Q1 2024"
        period = df["period"].astype(str).str.upper()
        year = period.str.extract(r"(20\d{2})", expand=False)
        q = period.str.extract(r"Q([1-4])", expand=False)
        df["year"] = pd.to_numeric(year, errors="coerce")
        df["quarter"] = q.where(q.isin(["1", "2", "3", "4"]), np.nan).map(lambda x: f"Q{x}" if pd.notna(x) else np.nan)

    # Construct pandas Period for quarter if possible
    if "year" in df.columns and "quarter" in df.columns:
        valid_q = df["quarter"].isin(["Q1", "Q2", "Q3", "Q4"])
        df.loc[valid_q, "period_q"] = (
            df.loc[valid_q, ["year", "quarter"]]
            .astype({"year": "Int64"})
            .apply(lambda r: pd.Period(f"{int(r['year'])}{r['quarter']}", freq="Q"), axis=1)
        )
    else:
        df["period_q"] = pd.NaT

    return df


def _normalise_categories(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Purpose of visit
    if "purpose" in df.columns:
        std = (
            df["purpose"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        purpose_map = {
            "holiday": "Holiday",
            "leisure": "Holiday",
            "business": "Business",
            "vfr": "Visiting friends or relatives",
            "visiting friends or relatives": "Visiting friends or relatives",
            "misc": "Miscellaneous",
            "miscellaneous": "Miscellaneous",
            "study": "Study",
        }
        df["purpose"] = std.map(lambda x: purpose_map.get(x, x.title()))

    # Transport mode
    if "transport" in df.columns:
        std = (
            df["transport"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        transport_map = {
            "air": "Air",
            "sea": "Sea",
            "ferry": "Sea",
            "tunnel": "Tunnel",
            "rail": "Tunnel",  # Eurostar/Channel Tunnel typically captured as tunnel/rail
        }
        df["transport"] = std.map(lambda x: transport_map.get(x, x.title()))

    # Region (macro)
    if "region" in df.columns:
        std = (
            df["region"]
            .astype(str)
            .str.strip()
            .str.lower()
        )
        region_map = {
            "europe": "Europe",
            "north america": "North America",
            "other countries": "Other Countries",
            "other": "Other Countries",
        }
        df["region"] = std.map(lambda x: region_map.get(x, x.title()))

    return df


def _add_coverage_flag(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Coverage is UK up to 2023; GB from 2024 onwards
    if "year" in df.columns:
        df["coverage"] = np.where(df["year"].fillna(0) >= 2024, "Great Britain", "United Kingdom")
    else:
        df["coverage"] = pd.NA
    return df


def clean(input_path: Path, output_path: Path, sheet: Optional[str] = None) -> Path:
    logging.info(f"Reading raw data from: {input_path}")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Read Excel – first sheet by default unless specified
    if sheet is None:
        df = pd.read_excel(input_path, dtype=str)
    else:
        df = pd.read_excel(input_path, sheet_name=sheet, dtype=str)

    logging.info("Standardising column names.")
    df = _standardise_columns(df)

    logging.info("Coercing numeric fields.")
    df = _coerce_numerics(df)

    logging.info("Deriving quarterly periods.")
    df = _derive_quarter(df)

    logging.info("Normalising categorical values.")
    df = _normalise_categories(df)

    logging.info("Adding coverage flag.")
    df = _add_coverage_flag(df)

    # Basic ordering for readability
    preferred_order = [
        "year",
        "quarter",
        "period_q",
        "coverage",
        "region",
        "country",
        "uk_region",
        "purpose",
        "transport",
        "visits",
        "expenditure_millions",
        "nights",
    ]
    cols = [c for c in preferred_order if c in df.columns] + [c for c in df.columns if c not in preferred_order]
    df = df[cols]

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logging.info(f"Writing interim dataset to: {output_path}")
    df.to_parquet(output_path, index=False)

    logging.info("Cleaning complete.")
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean and standardise the raw visitors dataset.")
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
    parser.add_argument(
        "--sheet",
        type=str,
        default=None,
        help="Optional Excel sheet name to read.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    clean(args.input, args.output, args.sheet)


if __name__ == "__main__":
    main()
