"""
Transform module for tourism data.

Converts cleaned, wide-form data into tidy tables and aggregated views,
annotates coverage changes (UK → Great Britain in 2024), and writes
analysis-ready outputs.

Expected wide-form columns (case-insensitive, spaces/dashes allowed):
- quarter            (e.g., "2019Q1", "2019 Q1")
- geography          (e.g., "Europe", "North America")
- purpose            (e.g., "Holiday", "Business", "VFR", "Miscellaneous")
- transport          (e.g., "Air", "Sea and Tunnel")
- visits             (number of visits)
- expenditure        (expenditure in £ millions)
- nights             (number of nights)

Usage (examples):
  python -m src.data.transform --input data/clean/cleaned.csv --out-interim data/interim --out-tables outputs/tables
  python -m src.data.transform --input data/clean/cleaned.parquet --export --out-tables outputs/tables
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd


# -----------------------
# Normalisation utilities
# -----------------------

STANDARD_COLS = {
    "quarter": "quarter",
    "geography": "geography",
    "purpose": "purpose",
    "transport": "transport",
    "visits": "visits",
    "expenditure": "expenditure_millions",
    "nights": "nights",
}

ALTERNATE_COL_MAP = {
    "quarter": {"quarter", "qtr", "q", "period"},
    "geography": {"geography", "region", "area"},
    "purpose": {"purpose", "reason", "intent"},
    "transport": {"transport", "mode", "mode_of_transport"},
    "visits": {"visits", "number_of_visits", "visit_count"},
    "expenditure": {"expenditure", "spend", "expenditure_millions", "£m", "gbp_millions"},
    "nights": {"nights", "night_count", "overnights"},
}


def _normalise_header(name: str) -> str:
    """Lowercase, strip, replace spaces/dashes/underscores for matching."""
    return (
        name.strip()
        .lower()
        .replace("-", " ")
        .replace("_", " ")
    )


def harmonise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map various header spellings to STANDARD_COLS, leaving extras intact."""
    current = {col: _normalise_header(col) for col in df.columns}

    # Build reverse lookup from ALTERNATE_COL_MAP
    target_for_normal = {}
    for standard, alts in ALTERNATE_COL_MAP.items():
        for alt in alts:
            target_for_normal[alt] = standard

    rename_map: dict[str, str] = {}
    for original, normal in current.items():
        target_key = target_for_normal.get(normal)
        if target_key:
            rename_map[original] = STANDARD_COLS[target_key]

    df = df.rename(columns=rename_map)
    return df


# -----------------------
# Quarter and coverage
# -----------------------

def normalise_quarter_label(q: str) -> str:
    """
    Return quarter as 'YYYYQn' for common input variants.
    Accepts 'YYYYQn', 'YYYY Qn', 'Qn YYYY', date-like strings 'YYYY-MM',
    and pandas Periods. If month is given, maps to its quarter.
    """
    if pd.isna(q):
        return np.nan

    if isinstance(q, pd.Period):
        if q.freqstr.upper().startswith("Q"):
            return f"{q.year}Q{q.quarter}"
        # Month or other frequency
        return f"{q.year}Q{((q.month - 1) // 3) + 1}"

    s = str(q).strip().upper().replace("  ", " ")
    # Direct 'YYYYQn' or 'YYYY Qn'
    if "Q" in s and any(str(i) in s for i in range(1, 5)):
        s = s.replace(" ", "")
        # Forms: YYYYQn or QnYYYY
        if s.startswith("Q"):
            # QnYYYY
            qn = s[1]
            year = s[2:]
            return f"{year}Q{qn}"
        # YYYYQn
        year = s[:4]
        qn = s[-1]
        return f"{year}Q{qn}"

    # Date-like 'YYYY-MM' or 'YYYY-MM-DD'
    try:
        ts = pd.to_datetime(s, errors="raise", dayfirst=False)
        year = ts.year
        qn = ((ts.month - 1) // 3) + 1
        return f"{year}Q{qn}"
    except Exception:
        # Fallback: try 'Month YYYY'
        try:
            ts = pd.to_datetime(s, errors="raise", dayfirst=True)
            year = ts.year
            qn = ((ts.month - 1) // 3) + 1
            return f"{year}Q{qn}"
        except Exception:
            return s  # leave as-is if unparseable


def annotate_coverage(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'coverage' and 'method_break' based on quarter.

    Rule:
      - quarters in 2019–2023 → 'United Kingdom'
      - quarters in 2024+     → 'Great Britain'
    """
    def _coverage(q: str) -> str:
        try:
            year = int(str(q)[:4])
        except ValueError:
            return "Unknown"
        return "Great Britain" if year >= 2024 else "United Kingdom"

    def _break(q: str) -> bool:
        try:
            year = int(str(q)[:4])
        except ValueError:
            return False
        return year >= 2024

    df["coverage"] = df["quarter"].map(_coverage)
    df["method_break"] = df["quarter"].map(_break)
    return df


# -----------------------
# Tidy and aggregate
# -----------------------

VALUE_COLS_DEFAULT = ["visits", "expenditure_millions", "nights"]


def to_tidy(
    df: pd.DataFrame,
    value_cols: Iterable[str] = VALUE_COLS_DEFAULT,
    id_cols: Iterable[str] = ("quarter", "geography", "purpose", "transport", "coverage", "method_break"),
) -> pd.DataFrame:
    """Melt wide metrics into tidy long format."""
    missing = [c for c in value_cols if c not in df.columns]
    if missing:
        raise KeyError(f"Missing value columns: {missing}")

    for col in id_cols:
        if col not in df.columns:
            df[col] = np.nan

    tidy = df.melt(
        id_vars=list(id_cols),
        value_vars=list(value_cols),
        var_name="metric",
        value_name="value",
    )
    # Stable ordering
    tidy = tidy.sort_values(["quarter", "geography", "purpose", "transport", "metric"], ignore_index=True)
    return tidy


def aggregate(df_tidy: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Produce common aggregated views from tidy data."""
    # By geography and quarter
    by_region = (
        df_tidy.groupby(["quarter", "coverage", "geography", "metric"], as_index=False)
        .agg(value=("value", "sum"))
    )

    # By purpose and quarter
    by_purpose = (
        df_tidy.groupby(["quarter", "coverage", "purpose", "metric"], as_index=False)
        .agg(value=("value", "sum"))
    )

    # By transport and quarter
    by_transport = (
        df_tidy.groupby(["quarter", "coverage", "transport", "metric"], as_index=False)
        .agg(value=("value", "sum"))
    )

    return {
        "region": by_region,
        "purpose": by_purpose,
        "transport": by_transport,
    }


# -----------------------
# Reading and writing
# -----------------------

def read_frame(path: Path) -> pd.DataFrame:
    """Read CSV or Parquet to DataFrame."""
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def write_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


# -----------------------
# Orchestration
# -----------------------

def transform(
    input_path: Path,
    out_interim_dir: Path | None = None,
    out_tables_dir: Path | None = None,
    export_tables: bool = False,
    value_cols: Iterable[str] = VALUE_COLS_DEFAULT,
) -> Mapping[str, pd.DataFrame]:
    """
    Execute transform:
      1) Load cleaned wide-form data
      2) Harmonise headers and normalise quarters
      3) Annotate coverage and methodological break
      4) Produce tidy and aggregated outputs
      5) Optionally write interim (Parquet) and final tables (CSV)
    """
    df = read_frame(input_path)
    df = harmonise_columns(df)

    # Ensure required columns exist
    required = ["quarter", "geography", "purpose", "transport"] + list(value_cols)
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Input missing required columns: {missing}")

    # Normalise quarter values
    df["quarter"] = df["quarter"].map(normalise_quarter_label)

    # Numeric coercion for values
    for col in value_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Annotate coverage
    df = annotate_coverage(df)

    # Tidy
    tidy = to_tidy(df, value_cols=value_cols)

    # Aggregates
    aggs = aggregate(tidy)

    # Write interim
    if out_interim_dir:
        out_interim_dir.mkdir(parents=True, exist_ok=True)
        write_parquet(tidy, out_interim_dir / "tidy.parquet")
        for name, frame in aggs.items():
            write_parquet(frame, out_interim_dir / f"{name}.parquet")

    # Export CSV tables for portability
    if export_tables and out_tables_dir:
        out_tables_dir.mkdir(parents=True, exist_ok=True)
        write_csv(tidy, out_tables_dir / "tidy.csv")
        write_csv(aggs["region"], out_tables_dir / "visits_expenditure_nights_by_region_qtr.csv")
        write_csv(aggs["purpose"], out_tables_dir / "visits_expenditure_nights_by_purpose_qtr.csv")
        write_csv(aggs["transport"], out_tables_dir / "visits_expenditure_nights_by_transport_qtr.csv")

    result: dict[str, pd.DataFrame] = {"tidy": tidy, **aggs}
    return result


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transform cleaned tourism data into tidy tables and aggregates."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to cleaned wide-form data (CSV or Parquet).",
    )
    parser.add_argument(
        "--out-interim",
        type=Path,
        default=Path("data/interim"),
        help="Directory for interim Parquet outputs.",
    )
    parser.add_argument(
        "--out-tables",
        type=Path,
        default=Path("outputs/tables"),
        help="Directory for final CSV tables.",
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Write final CSV tables to --out-tables.",
    )
    parser.add_argument(
        "--no-interim",
        action="store_true",
        help="Disable writing interim Parquet outputs.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv or sys.argv[1:])
    transform(
        input_path=args.input,
        out_interim_dir=None if args.no_interim else args.out_interim,
        out_tables_dir=args.out_tables,
        export_tables=args.export,
    )


if __name__ == "__main__":
    main()
