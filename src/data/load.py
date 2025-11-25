"""
Data loading utilities for the tourism project.

Functions to read worksheets from the ONS Excel workbook, including the
specific 'Table 1' sheet with known header positioning.

Performance: Includes LRU caching to avoid re-reading Excel files.
"""

from __future__ import annotations

from functools import lru_cache
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
    "clear_cache",
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


@lru_cache(maxsize=8)
def _load_excel_cached(
    path_str: str,
    sheet_name: Union[str, int],
    header: Optional[int],
    engine: str,
) -> pd.DataFrame:
    """
    Internal cached Excel loader. Uses string path for hashability.
    
    Performance: Caches up to 8 different (path, sheet, header, engine)
    combinations to avoid re-reading the same Excel file multiple times.
    """
    excel_path = Path(path_str)
    if not excel_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {excel_path}")

    try:
        df = pd.read_excel(
            excel_path,
            sheet_name=sheet_name,
            header=header,
            engine=engine,
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


def load_excel(
    path: Union[str, Path, None] = None,
    *,
    sheet_name: Union[str, int] = 0,
    header: Optional[int] = 0,
    engine: Optional[str] = "openpyxl",
    dtype: Optional[dict] = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Generic Excel worksheet loader with optional caching.

    Parameters:
    - path: Path to the workbook. If None, resolves to the default raw
            file path.
    - sheet_name: Worksheet name or index to read.
    - header: Row index to use for column names.
    - engine: Excel engine to use (e.g., 'openpyxl').
    - dtype: Optional column dtypes mapping.
    - use_cache: If True (default), uses LRU cache to avoid re-reading
                 the same file. Set to False for dynamic/changing files.

    Returns:
    - DataFrame containing the requested worksheet. Returns an empty DataFrame
      if the sheet cannot be read.
      
    Performance: With caching enabled (default), repeated calls with the same
    parameters return instantly. First call pays full Excel parsing cost.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    engine_str = engine or "openpyxl"
    
    if use_cache:
        df = _load_excel_cached(
            str(excel_path),
            sheet_name,
            header,
            engine_str,
        )
    else:
        if not excel_path.exists():
            raise FileNotFoundError(f"Workbook does not exist: {excel_path}")
        try:
            df = pd.read_excel(
                excel_path,
                sheet_name=sheet_name,
                header=header,
                engine=engine_str,
            )
            df.columns = [str(col).strip() for col in df.columns]
        except ValueError as e:
            if isinstance(sheet_name, str) and (
                f"Worksheet named '{sheet_name}' not found" in str(e)
            ):
                return pd.DataFrame()
            raise ValueError(
                f"Failed to read worksheet '{sheet_name}' from workbook: {e}"
            ) from e
        except Exception:
            return pd.DataFrame()
    
    # Apply dtype conversions if requested (not cached)
    if dtype:
        for col, dt in dtype.items():
            if col in df.columns:
                df[col] = df[col].astype(dt)
    
    return df


def load_table_1(
    path: Union[str, Path, None] = None,
    engine: Optional[str] = "openpyxl",
    use_cache: bool = True,
) -> pd.DataFrame:
    """
    Load the specific 'Table 1' worksheet from the ONS workbook.

    Reads worksheet '1' where column headers begin at row index 9.
    Returns an empty DataFrame if loading fails.
    
    Performance: With caching enabled (default), this function returns
    instantly on repeated calls with the same parameters.
    """
    return load_excel(
        path=path,
        sheet_name="1",
        header=9,
        engine=engine,
        use_cache=use_cache,
    )


def clear_cache() -> None:
    """
    Clear the Excel loading cache.
    
    Call this when the source Excel file has been modified and you need
    to reload fresh data.
    """
    _load_excel_cached.cache_clear()


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
