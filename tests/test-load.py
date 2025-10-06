import io
from pathlib import Path

import pandas as pd
import pytest

from src.data.load import load_excel


def _make_sample_frame(period_prefix: str, rows: int = 3) -> pd.DataFrame:
    """Create a minimal frame using the expected raw ONS column names."""
    return pd.DataFrame(
        {
            "Period": [f"{period_prefix} Q{i+1}" for i in range(rows)],
            "Geography": ["Europe", "North America", "Other Countries"],
            "Purpose": ["Holiday", "Business", "VFR"],
            "Transport": ["Air", "Sea", "Tunnel"],
            "Visits (000s)": [100, 150, 200],
            "Nights (000s)": [400, 500, 600],
            "Spend (£m)": [250, 300, 450],
        }
    )


def _write_excel_with_sheets(path: Path, sheets: dict[str, pd.DataFrame]) -> None:
    """Write a multi-sheet Excel file in memory-safe manner."""
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            # Intentionally include an extra header row to mimic real-world quirks
            header_row = pd.DataFrame([["Header row"] + [""] * (df.shape[1] - 1)], columns=df.columns)
            combined = pd.concat([header_row, df], ignore_index=True)
            combined.to_excel(writer, sheet_name=name, index=False)


@pytest.fixture
def sample_excel(tmp_path: Path) -> Path:
    """Create a realistic multi-sheet workbook including the GB break in 2024."""
    path = tmp_path / "overseas-visitors-to-britain-2024.xlsx"
    sheets = {
        "2019": _make_sample_frame("2019"),
        "2020": _make_sample_frame("2020"),
        "2021": _make_sample_frame("2021"),
        "2022": _make_sample_frame("2022"),
        "2023": _make_sample_frame("2023"),
        # 2024 onwards is Great Britain only; same schema at load stage
        "2024": _make_sample_frame("2024"),
    }
    _write_excel_with_sheets(path, sheets)
    return path


def test_load_concatenates_all_sheets_and_preserves_columns(sample_excel: Path):
    """Loading with sheet_name=None should concatenate all sheets and retain expected columns."""
    df = load_excel(sample_excel, {"sheet_name": None})
    # Expected columns present
    expected = [
        "Period",
        "Geography",
        "Purpose",
        "Transport",
        "Visits (000s)",
        "Nights (000s)",
        "Spend (£m)",
    ]
    assert list(df.columns) == expected
    # Row count equals sum across sheets minus any artificial header rows handled in loader
    # We wrote 6 sheets with 3 rows each; total 18 records expected after header handling.
    assert len(df) == 6 * 3
    # Basic type expectations (Excel numeric -> numeric dtypes)
    assert pd.api.types.is_numeric_dtype(df["Visits (000s)"])
    assert pd.api.types.is_numeric_dtype(df["Nights (000s)"])
    assert pd.api.types.is_numeric_dtype(df["Spend (£m)"])
    # Period and categoricals are read as object at this stage
    assert df["Period"].dtype == object
    assert df["Geography"].dtype == object
    assert df["Purpose"].dtype == object
    assert df["Transport"].dtype == object


def test_load_respects_explicit_sheet_selection(sample_excel: Path):
    """Loading a specific sheet should return only that period’s data."""
    df_2024 = load_excel(sample_excel, {"sheet_name": "2024"})
    assert df_2024["Period"].str.startswith("2024").all()
    assert len(df_2024) == 3

    df_2021 = load_excel(sample_excel, {"sheet_name": "2021"})
    assert df_2021["Period"].str.startswith("2021").all()
    assert len(df_2021) == 3


def test_load_handles_header_rows(sample_excel: Path):
    """Loader should skip non-data header rows and return clean records only."""
    df = load_excel(sample_excel, {"sheet_name": "2019"})
    # Ensure none of the artificial header markers remain
    assert not (df["Period"] == "Header row").any()
    # All numeric columns should remain numeric after header removal
    for col in ["Visits (000s)", "Nights (000s)", "Spend (£m)"]:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_load_raises_on_missing_file(tmp_path: Path):
    """Attempting to load a non-existent file should raise a clear exception."""
    missing = tmp_path / "does-not-exist.xlsx"
    with pytest.raises((FileNotFoundError, OSError)):
        load_excel(missing, {"sheet_name": None})
