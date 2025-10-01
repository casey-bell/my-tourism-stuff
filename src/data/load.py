"""
Data loading utility for the tourism project.

Provides a single function to read the ONS Excel workbook from data/raw,
restricted to the worksheet labelled exactly "1". Handles common edge cases
such as missing files and empty sheets, with the header row fixed at 9.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd


# Project-relative locations
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_FILENAME = "overseas-visitors-to-britain-2024.xlsx"
TARGET_SHEET = "1"
HEADER_ROW = 8  # zero-based index for row 9


def raw_file_path(filename: Optional[str] = None) -> Path:
    """
    Resolve the path to the raw Excel workbook.

    If filename is not provided, uses the default expected file name within data/raw.
    """
    name = filename or DEFAULT_FILENAME
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    return path


def load_sheet(
    path: Union[str, Path, None] = None,
    engine: str = "openpyxl",
) -> pd.DataFrame:
    """
    Load the worksheet labelled exactly "1" from the ONS workbook.

    Returns an empty DataFrame if the sheet exists but contains no rows.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {excel_path}")

    try:
        df = pd.read_excel(
            excel_path,
            sheet_name=TARGET_SHEET,
            header=HEADER_ROW,
            engine=engine,
        )
    except ValueError as e:
        raise ValueError(f"Failed to read sheet '{TARGET_SHEET}' from workbook '{excel_path}': {e}") from e

    if df is None or df.shape[0] == 0:
        return pd.DataFrame()

    # Trim leading/trailing whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]
    return df


if __name__ == "__main__":
    # Quick diagnostic run: prints sheet name and basic shape
    try:
        p = raw_file_path()
        print(f"Workbook: {p}")
        df = load_sheet(p)
        print(f"Sheet '{TARGET_SHEET}': {df.shape[0]} rows, {df.shape[1]} columns")
    except Exception as exc:
        print(f"Error: {exc}")
