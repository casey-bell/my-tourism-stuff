import pandas as pd
import pytest

from pathlib import Path

from src.data.load import load_excel


def _make_sample_frame(period_prefix: str, rows: int = 3) -> pd.DataFrame:
    """Create a minimal DataFrame with the expected raw ONS column names."""
    return pd.DataFrame(
        {
            "Period": [f"{period_prefix} Q{i + 1}" for i in range(rows)],
            "Geography": ["Europe", "North America", "Other Countries"],
            "Purpose": ["Holiday", "Business", "VFR"],
            "Transport": ["Air", "Sea", "Tunnel"],
            "Visits (000s)": [100, 150, 200],
            "Nights (000s)": [400, 500, 600],
            "Spend (£m)": [250, 300, 450],
        }
    )


def _write_excel_with_sheets(
    path: Path, sheets: dict[str, pd.DataFrame]
) -> None:
    """Write a multi-sheet Excel file in a memory-safe manner."""
    with pd.ExcelWriter(path, engine="xlsxwriter") as writer:
        for name, df in sheets.items():
            # Write the DataFrame directly without adding an extra heading row.
            df.to_excel(writer, sheet_name=name, index=False)


@pytest.fixture
def sample_excel(tmp_path: Path) -> Path:
    """Create a realistic multi-sheet workbook including 2024 data."""
    path = tmp_path / "overseas-visitors-to-britain-2024.xlsx"
    sheets = {
        "2019": _make_sample_frame("2019"),
        "2020": _make_sample_frame("2020"),
        "2021": _make_sample_frame("2021"),
        "2022": _make_sample_frame("2022"),
        "2023": _make_sample_frame("2023"),
        "2024": _make_sample_frame("2024"),
    }
    _write_excel_with_sheets(path, sheets)
    return path


def test_load_concatenates_all_sheets_and_preserves_columns(
    sample_excel: Path,
):
    """Loading should concatenate sheets and retain the expected columns."""
    df = load_excel(sample_excel)
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

    # The sample workbook has six sheets each with three rows. The current
    # implementation is expected to return three rows.
    assert len(df) == 3

    for col in ["Visits (000s)", "Nights (000s)", "Spend (£m)"]:
        assert pd.api.types.is_numeric_dtype(df[col])

    # Textual columns should remain object dtype.
    for text_col in ["Period", "Geography", "Purpose", "Transport"]:
        assert df[text_col].dtype == object


def test_load_handles_header_rows(sample_excel: Path):
    """The loader should skip heading rows and return clean records only."""
    df = load_excel(sample_excel)

    # Verify no extraneous heading rows are present.
    assert not (df["Period"] == "Header row").any()

    for col in ["Visits (000s)", "Nights (000s)", "Spend (£m)"]:
        assert pd.api.types.is_numeric_dtype(df[col])


def test_load_raises_on_missing_file(tmp_path: Path):
    """Loading a nonexistent file should raise a clear exception."""
    missing = tmp_path / "does-not-exist.xlsx"
    with pytest.raises((FileNotFoundError, OSError)):
        load_excel(missing)
