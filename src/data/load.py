"""
Data loading utilities for the tourism project.

Provides functions to read the ONS Excel workbook from data/raw and return
Pandas DataFrames for downstream processing. Handles common edge cases such as
missing files, empty sheets, and header offsets.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional, Union

import pandas as pd


# Project-relative locations
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_FILENAME = "overseas-visitors-to-britain-2024.xlsx"


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


def load_workbook(
    path: Union[str, Path, None] = None,
    sheets: Optional[Iterable[str]] = None,
    header: Optional[int] = 0,
    engine: str = "openpyxl",
) -> Dict[str, pd.DataFrame]:
    """
    Load one or more sheets from the ONS workbook as DataFrames.

    - path: explicit path to the workbook; if omitted, uses data/raw/<default>.
    - sheets: iterable of sheet names to read; if omitted, reads all sheets.
    - header: row index to use as the header (0-based). Set to None to keep default column names.
    - engine: Excel reading engine (default: openpyxl).

    Returns a dict mapping sheet names to DataFrames.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {excel_path}")

    # Read either specified sheets or all available sheets
    try:
        if sheets is None:
            frames = pd.read_excel(excel_path, sheet_name=None, header=header, engine=engine)
        else:
            frames = pd.read_excel(excel_path, sheet_name=list(sheets), header=header, engine=engine)
    except ValueError as e:
        # Typically raised for unknown sheet names
        raise ValueError(f"Failed to read sheets from workbook '{excel_path}': {e}") from e

    # Ensure empty sheets are represented consistently and strip trivial whitespace
    cleaned: Dict[str, pd.DataFrame] = {}
    for name, df in frames.items():
        if df is None or df.shape[0] == 0:
            cleaned[name] = pd.DataFrame()
            continue
        # Trim leading/trailing whitespace from column names
        df.columns = [str(c).strip() for c in df.columns]
        cleaned[name] = df

    return cleaned


def load_sheet(
    sheet_name: str,
    path: Union[str, Path, None] = None,
    header: Optional[int] = 0,
    engine: str = "openpyxl",
) -> pd.DataFrame:
    """
    Convenience loader for a single sheet.

    Returns an empty DataFrame if the sheet exists but contains no rows.
    """
    frames = load_workbook(path=path, sheets=[sheet_name], header=header, engine=engine)
    return frames.get(sheet_name, pd.DataFrame())


def list_sheets(path: Union[str, Path, None] = None) -> Iterable[str]:
    """
    List sheet names available in the workbook.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    with pd.ExcelFile(excel_path, engine="openpyxl") as xls:
        return xls.sheet_names


if __name__ == "__main__":
    # Quick diagnostic run: prints sheet names and basic shapes
    try:
        p = raw_file_path()
        print(f"Workbook: {p}")
        names = list_sheets(p)
        print(f"Sheets ({len(names)}): {', '.join(names)}")
        frames = load_workbook(p)
        for n, df in frames.items():
            print(f"- {n}: {df.shape[0]} rows, {df.shape[1]} columns")
    except Exception as exc:
        print(f"Error: {exc}")
