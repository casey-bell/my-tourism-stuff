"""
Data loading utilities for the tourism project.

Functions to read worksheets from the ONS Excel workbook, including the
specific 'Table 1' sheet with known header positioning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

import pandas as pd

# Project-relative locations
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_FILENAME = "overseas-visitors-to-britain-2024.xlsx"

__all__ = [
    "raw_file_path",
    "load_excel",
    "load_table_1",
    "verify_table_1_loaded",
]


def raw_file_path(filename: Optional[str] = None) -> Path:
    """
    Resolve the path to the raw Excel workbook.

    If filename is not provided, uses the default expected file name
    within data/raw.
    """
    name = filename or DEFAULT_FILENAME
    path = RAW_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    return path


def load_excel(
    path: Union[str, Path, None] = None,
    *,
    sheet_name: Union[str, int] = 0,
    header: Optional[int] = 0,
    engine: Optional[str] = "openpyxl",
    dtype: Optional[dict] = None,
) -> pd.DataFrame:
    """
    Generic Excel worksheet loader.

    Parameters:
    - path: Path to the workbook. If None, resolves to the default raw
            file path.
    - sheet_name: Worksheet name or index to read.
    - header: Row index to use for column names.
    - engine: Excel engine to use (e.g., 'openpyxl').
    - dtype: Optional column dtypes mapping.

    Returns:
    - DataFrame containing the requested worksheet. Returns an empty DataFrame
      if the sheet cannot be read.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {excel_path}")

    try:
        df = pd.read_excel(
            excel_path,
            sheet_name=sheet_name,
            header=header,
            engine=engine,
            dtype=dtype,
        )
        # Normalise column names
        df.columns = [str(col).strip() for col in df.columns]
        return df
    except ValueError as e:
        # Common failure when a named sheet is missing
        if isinstance(sheet_name, str) and (
            f"Worksheet named '{sheet_name}' not found" in str(e)
        ):
            return pd.DataFrame()
        raise ValueError(
            f"Failed to read worksheet '{sheet_name}' from workbook: {e}"
        ) from e
    except Exception:
        return pd.DataFrame()


def load_table_1(
    path: Union[str, Path, None] = None,
    engine: Optional[str] = "openpyxl",
) -> pd.DataFrame:
    """
    Load the specific 'Table 1' worksheet from the ONS workbook.

    Reads worksheet '1' where column headers begin at row index 9.
    Returns an empty DataFrame if loading fails.
    """
    return load_excel(path=path, sheet_name="1", header=9, engine=engine)


def verify_table_1_loaded() -> bool:
    """
    Verify that worksheet '1' can be loaded successfully and contains data.

    Returns True if data is loaded and has at least one row, otherwise False.
    """
    try:
        df = load_table_1()
        return df is not None and not df.empty and df.shape[0] > 0
    except Exception:
        return False
