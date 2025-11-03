import pandas as pd
import pytest

# Assumed validation API. Adapt imports if your module exposes different names.
from src.data.validate import (
    validate_dataframe,
    ValidationError,
)


def make_sample_schema():
    """
    Minimal schema describing expected columns and types, along with basic constraints.
    - 'period': string in YYYY-Qn format
    - 'geography': categorical/str
    - 'purpose': categorical/str
    - 'transport': categorical/str
    - 'visits_thousands': non-negative numeric
    - 'expenditure_millions': non-negative numeric
    - 'nights_thousands': non-negative numeric
    - 'gb_only': boolean flag to distinguish the 2024 methodological break
    """
    return {
        "columns": {
            "period": {"type": "string", "format": r"^\d{4}-Q[1-4]$"},
            "geography": {"type": "string"},
            "purpose": {"type": "string"},
            "transport": {"type": "string"},
            "visits_thousands": {"type": "number", "min": 0},
            "expenditure_millions": {"type": "number", "min": 0},
            "nights_thousands": {"type": "number", "min": 0},
            "gb_only": {"type": "boolean"},
        },
        "unique_keys": ["period", "geography", "purpose", "transport"],
    }


def make_valid_frame():
    """Create a small, valid dataset spanning the UK→GB methodological change."""
    return pd.DataFrame(
        {
            "period": ["2023-Q4", "2024-Q1"],
            "geography": ["Europe", "Europe"],
            "purpose": ["Holiday", "Holiday"],
            "transport": ["Air", "Air"],
            "visits_thousands": [250.0, 275.0],
            "expenditure_millions": [320.0, 350.0],
            "nights_thousands": [900.0, 950.0],
            # 2023 data: UK coverage (gb_only False), 2024 data: GB coverage only (gb_only True)
            "gb_only": [False, True],
        }
    )


def test_valid_dataset_passes_validation():
    schema = make_sample_schema()
    df = make_valid_frame()
    # Should not raise; returns a report dict with zero errors/warnings if implemented
    report = validate_dataframe(df, schema)
    assert isinstance(report, dict)
    assert report.get("errors", []) == []


def test_negative_values_are_rejected():
    schema = make_sample_schema()
    df = make_valid_frame().copy()
    df.loc[0, "expenditure_millions"] = -1.0

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    assert "expenditure_millions" in msg
    assert "non-negative" in msg or "min" in msg


def test_unique_key_violations_are_rejected():
    schema = make_sample_schema()
    df = make_valid_frame().copy()
    # Duplicate the first row to violate uniqueness across the key set
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    for key in schema["unique_keys"]:
        assert key in msg


@pytest.mark.parametrize(
    "bad_period",
    ["2024Q1", "24-Q1", "2024-Q5", "2024-Q0", "2024-Quarter1", "Q1-2024"],
)
def test_period_format_is_enforced(bad_period):
    schema = make_sample_schema()
    df = make_valid_frame().copy()
    df.loc[1, "period"] = bad_period

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    assert "period" in msg
    assert "format" in msg or "regex" in msg


def test_period_continuity_is_checked():
    """
    Expect continuity over quarters within the observed range.
    Here we skip 2023-Q3; validation should complain if continuity is required.
    """
    schema = make_sample_schema()
    df = pd.DataFrame(
        {
            "period": ["2023-Q2", "2023-Q4"],  # gap (missing 2023-Q3)
            "geography": ["Europe", "Europe"],
            "purpose": ["Holiday", "Holiday"],
            "transport": ["Air", "Air"],
            "visits_thousands": [240.0, 250.0],
            "expenditure_millions": [300.0, 310.0],
            "nights_thousands": [850.0, 870.0],
            "gb_only": [False, False],
        }
    )

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    assert "continuity" in msg or "missing quarter" in msg or "gap" in msg


def test_gb_only_flag_required_from_2024_onwards():
    """
    From 2024 onwards, data covers Great Britain only; expect gb_only=True on or after 2024-Q1.
    """
    schema = make_sample_schema()
    df = make_valid_frame().copy()
    # Break the rule: set 2024-Q1 record to gb_only False
    df.loc[df["period"] == "2024-Q1", "gb_only"] = False

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    assert "gb_only" in msg
    assert "2024" in msg or "great britain" in msg


def test_types_are_enforced():
    """
    Enforce declared types: numeric metrics must be numbers, gb_only must be boolean.

    To avoid triggering pandas' setting-with-incompatible-dtype warning or future error,
    promote the target columns to object dtype first, then insert deliberately invalid values.
    This keeps the test intent (the validator should reject incorrect types) while avoiding
    assignment-time dtype incompatibility from pandas.
    """
    schema = make_sample_schema()
    df = make_valid_frame().copy()

    # Promote these columns to object so that assigning strings does not raise at assignment time.
    df["visits_thousands"] = df["visits_thousands"].astype(object)
    df["gb_only"] = df["gb_only"].astype(object)

    df.loc[0, "visits_thousands"] = "two hundred and fifty"
    df.loc[1, "gb_only"] = "True"  # string instead of boolean

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    # The validator should indicate a type problem and mention the relevant fields.
    assert "type" in msg
    assert "visits_thousands" in msg or "gb_only" in msg


def test_empty_frame_is_rejected_with_clear_message():
    schema = make_sample_schema()
    # Build an empty DataFrame with the correct columns. Using pd.NA as the dtype initializer
    # would produce different dtypes; empty lists are sufficient for presence-of-columns checks.
    df = pd.DataFrame({col: [] for col in schema["columns"].keys()})

    with pytest.raises(ValidationError) as exc:
        validate_dataframe(df, schema)

    msg = str(exc.value).lower()
    assert "empty" in msg or "no rows" in msg
