import pandas as pd
import numpy as np
import pytest

from src.data.transform import (
    aggregate_visits_by_quarter,
    aggregate_expenditure_by_purpose,
    normalise_period,
)


def test_normalise_period_parses_quarter_strings():
    periods = ["2019 Q1", "2020 Q4", "2024 Q2", "2023 Q3"]
    expected = ["2019Q1", "2020Q4", "2024Q2", "2023Q3"]

    result = [normalise_period(p) for p in periods]
    assert result == expected


def test_normalise_period_handles_whitespace_and_case():
    periods = [" 2019 q1 ", "2020   Q2", "\t2021 q3"]
    expected = ["2019Q1", "2020Q2", "2021Q3"]

    result = [normalise_period(p) for p in periods]
    assert result == expected


def test_aggregate_visits_by_quarter_sums_correctly():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q1", "2019 Q2", "2024 Q1"],
            "geography_group": ["Europe", "Europe", "North America", "Other Countries"],
            "visits_thousands": [10.0, 5.0, 3.0, 2.0],
        }
    )

    agg = aggregate_visits_by_quarter(df)

    # Expect periods normalised and grouped sums
    expected = pd.DataFrame(
        {
            "period": ["2019Q1", "2019Q2", "2024Q1"],
            "geography_group": ["Europe", "North America", "Other Countries"],
            "visits_thousands": [15.0, 3.0, 2.0],
        }
    )

    # Sort for deterministic comparison
    agg_sorted = agg.sort_values(["period", "geography_group"]).reset_index(drop=True)
    expected_sorted = expected.sort_values(["period", "geography_group"]).reset_index(drop=True)

    pd.testing.assert_frame_equal(agg_sorted, expected_sorted)


def test_aggregate_visits_by_quarter_ignores_non_numeric_and_nans():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q1", "2019 Q1", "2019 Q2"],
            "geography_group": ["Europe", "Europe", "Europe", "Europe"],
            "visits_thousands": [10.0, np.nan, "not a number", 4.0],
        }
    )

    agg = aggregate_visits_by_quarter(df)

    # "not a number" should be coerced/ignored; NaN should be treated as missing
    expected = pd.DataFrame(
        {
            "period": ["2019Q1", "2019Q2"],
            "geography_group": ["Europe", "Europe"],
            "visits_thousands": [10.0, 4.0],
        }
    ).sort_values(["period"]).reset_index(drop=True)

    agg_sorted = agg.sort_values(["period"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(agg_sorted, expected)


def test_aggregate_expenditure_by_purpose_sums_correctly():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q1", "2019 Q2", "2024 Q4"],
            "purpose": ["Holiday", "Business", "Holiday", "VFR"],
            "expenditure_millions": [100.0, 50.0, 20.0, 5.0],
        }
    )

    agg = aggregate_expenditure_by_purpose(df)

    expected = pd.DataFrame(
        {
            "period": ["2019Q1", "2019Q1", "2019Q2", "2024Q4"],
            "purpose": ["Business", "Holiday", "Holiday", "VFR"],
            "expenditure_millions": [50.0, 100.0, 20.0, 5.0],
        }
    )

    agg_sorted = agg.sort_values(["period", "purpose"]).reset_index(drop=True)
    expected_sorted = expected.sort_values(["period", "purpose"]).reset_index(drop=True)

    pd.testing.assert_frame_equal(agg_sorted, expected_sorted)


def test_expenditure_aggregation_ignores_invalid_values():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q1", "2019 Q2"],
            "purpose": ["Holiday", "Holiday", "Business"],
            "expenditure_millions": ["NaN", 30.0, None],
        }
    )

    agg = aggregate_expenditure_by_purpose(df)

    expected = pd.DataFrame(
        {
            "period": ["2019Q1"],
            "purpose": ["Holiday"],
            "expenditure_millions": [30.0],
        }
    ).sort_values(["period", "purpose"]).reset_index(drop=True)

    agg_sorted = agg.sort_values(["period", "purpose"]).reset_index(drop=True)
    pd.testing.assert_frame_equal(agg_sorted, expected)


def test_period_sort_order_is_chronological_in_outputs():
    df = pd.DataFrame(
        {
            "period": ["2020 Q4", "2019 Q1", "2019 Q3", "2024 Q1", "2019 Q2"],
            "geography_group": ["Europe"] * 5,
            "visits_thousands": [2, 5, 7, 1, 6],
        }
    )

    agg = aggregate_visits_by_quarter(df)

    # Expected chronological order after normalisation: 2019Q1, 2019Q2, 2019Q3, 2020Q4, 2024Q1
    expected_period_order = ["2019Q1", "2019Q2", "2019Q3", "2020Q4", "2024Q1"]
    assert list(agg["period"]) == expected_period_order


def test_group_columns_and_dtypes_are_preserved():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q1"],
            "geography_group": ["Europe", "Europe"],
            "visits_thousands": [1.5, 2.5],
        }
    )

    agg = aggregate_visits_by_quarter(df)

    assert list(agg.columns) == ["period", "geography_group", "visits_thousands"]
    assert agg["period"].dtype == object
    assert agg["geography_group"].dtype == object
    assert np.issubdtype(agg["visits_thousands"].dtype, np.number)


def test_outputs_exclude_empty_groups_after_aggregation():
    df = pd.DataFrame(
        {
            "period": ["2019 Q1", "2019 Q2"],
            "geography_group": ["Europe", "North America"],
            "visits_thousands": [0.0, 0.0],
        }
    )

    agg = aggregate_visits_by_quarter(df)

    # If all values are zero, groups should still exist; if rows are missing after cleaning, they should not.
    # Here, zeros are legitimate values, so both rows should be present.
    assert len(agg) == 2
    assert set(agg["geography_group"]) == {"Europe", "North America"}


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2019 Q1", "2019Q1"),
        ("2019Q1", "2019Q1"),
        ("2019 - Q1", "2019Q1"),
        (" Q3 2020 ", "2020Q3"),
    ],
)
def test_normalise_period_accepts_varied_input_formats(raw, expected):
    assert normalise_period(raw) == expected
