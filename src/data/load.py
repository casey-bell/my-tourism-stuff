"""
Data loading utilities for the tourism project.

Provides functions to read the specific 'Table 1' worksheet from the ONS Excel workbook.
Handles the specific structure of the ONS data with appropriate header positioning.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

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


def load_table_1(
    path: Union[str, Path, None] = None,
    engine: str = "openpyxl",
) -> pd.DataFrame:
    """
    Load the specific 'Table 1' worksheet from the ONS workbook.
    
    This function is tailored to read worksheet "1" which contains the number of visits 
    by overseas residents, with the header starting at row 9 (0-indexed).
    
    Returns an empty DataFrame if the sheet cannot be loaded.
    """
    excel_path = raw_file_path() if path is None else Path(path)
    if not excel_path.exists():
        raise FileNotFoundError(f"Workbook does not exist: {excel_path}")

    try:
        # Read only worksheet "1" with header at row 9
        df = pd.read_excel(
            excel_path, 
            sheet_name="1",
            header=9,  # Header row for Table 1 data
            engine=engine
        )
        
        # Trim leading/trailing whitespace from column names
        df.columns = [str(col).strip() for col in df.columns]
        
        return df
        
    except ValueError as e:
        if "Worksheet named '1' not found" in str(e):
            print(f"Warning: Worksheet '1' not found in {excel_path}")
            return pd.DataFrame()
        raise ValueError(f"Failed to read worksheet '1' from workbook: {e}") from e
    except Exception as e:
        print(f"Error loading worksheet '1': {e}")
        return pd.DataFrame()


def verify_table_1_loaded() -> bool:
    """
    Verify that worksheet "1" can be loaded successfully and contains data.
    
    Returns True if data is loaded successfully and contains rows, False otherwise.
    """
    try:
        df = load_table_1()
        return df is not None and not df.empty and df.shape[0] > 0
    except Exception:
        return False


if __name__ == "__main__":
    # Diagnostic function specifically for Table 1
    try:
        file_path = raw_file_path()
        print(f"Workbook: {file_path}")
        
        df = load_table_1()
        if df.empty:
            print("Worksheet '1' is empty or could not be loaded")
        else:
            print(f"Worksheet '1' loaded successfully:")
            print(f"- Shape: {df.shape[0]} rows, {df.shape[1]} columns")
            print(f"- Columns: {list(df.columns)}")
            print(f"- First few periods: {df['Period'].head().tolist() if 'Period' in df.columns else 'N/A'}")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
