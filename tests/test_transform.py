import pandas as pd
import numpy as np
import pytest

from src.data.transform import (
    harmonise_columns,
    normalise_quarter_label,
    annotate_coverage,
    to_tidy,
    aggregate,
    VALUE_COLS_DEFAULT
)


def test_normalise_quarter_label_parses_quarter_strings():
    periods = ["2019 Q1", "2020 Q4", "2024 Q2", "2023 Q3"]
    expected = ["2019Q1", "2020Q4", "2024Q2", "2023Q3"]

    result = [normalise_quarter_label(p) for p in periods]
    assert result == expected


def test_normalise_quarter_label_handles_whitespace_and_case():
    periods = [" 2019 q1 ", "2020   Q2", "\t2021 q3"]
    expected = ["2019Q1", "2020Q2", "2021Q3"]

    result = [normalise_quarter_label(p) for p in periods]
    assert result == expected


def test_harmonise_columns_standardises_column_names():
    df = pd.DataFrame({
        "Quarter": ["2019Q1", "2019Q2"],
        "GEOGRAPHY": ["Europe", "North America"],
        "Visit Count": [100, 200],
        "Expenditure_Millions": [50.0, 75.0]
    })
    
    result = harmonise_columns(df)
    
    expected_columns = ["quarter", "geography", "visit_count", "expenditure_millions"]
    assert all(col in result.columns for col in expected_columns)


def test_annotate_coverage_labels_correctly():
    df = pd.DataFrame({
        "quarter": ["2019Q1", "2023Q4", "2024Q1", "2024Q2"]
    })
    
    result = annotate_coverage(df)
    
    expected_coverage = ["United Kingdom", "United Kingdom", "Great Britain", "Great Britain"]
    expected_break = [False, False, True, True]
    
    assert list(result["coverage"]) == expected_coverage
    assert list(result["method_break"]) == expected_break


def test_to_tidy_converts_wide_to_long_format():
    wide_df = pd.DataFrame({
        "quarter": ["2019Q1", "2019Q2"],
        "geography": ["Europe", "North America"],
        "purpose": ["Holiday", "Business"],
        "transport": ["Air", "Air"],
        "visits": [100.0, 200.0],
        "expenditure_millions": [50.0, 75.0],
        "nights": [500.0, 300.0],
        "coverage": ["United Kingdom", "United Kingdom"],
        "method_break": [False, False]
    })
    
    tidy_df = to_tidy(wide_df)
    
    assert "metric" in tidy_df.columns
    assert "value" in tidy_df.columns
    assert len(tidy_df) == len(wide_df) * len(VALUE_COLS_DEFAULT)


def test_aggregate_produces_correct_views():
    tidy_df = pd.DataFrame({
        "quarter": ["2019Q1", "2019Q1", "2019Q2", "2019Q2"],
        "geography": ["Europe", "Europe", "North America", "North America"],
        "purpose": ["Holiday", "Business", "Holiday", "Business"],
        "transport": ["Air", "Air", "Air", "Air"],
        "coverage": ["United Kingdom", "United Kingdom", "United Kingdom", "United Kingdom"],
        "method_break": [False, False, False, False],
        "metric": ["visits", "visits", "visits", "visits"],
        "value": [100.0, 50.0, 200.0, 75.0]
    })
    
    result = aggregate(tidy_df)
    
    assert "region" in result
    assert "purpose" in result
    assert "transport" in result
    assert len(result["region"]) > 0
    assert len(result["purpose"]) > 0
    assert len(result["transport"]) > 0


def test_aggregate_sums_values_correctly():
    tidy_df = pd.DataFrame({
        "quarter": ["2019Q1", "2019Q1", "2019Q1"],
        "geography": ["Europe", "Europe", "Europe"],
        "purpose": ["Holiday", "Business", "Holiday"],
        "transport": ["Air", "Air", "Air"],
        "coverage": ["United Kingdom", "United Kingdom", "United Kingdom"],
        "method_break": [False, False, False],
        "metric": ["visits", "visits", "visits"],
        "value": [100.0, 50.0, 25.0]
    })
    
    result = aggregate(tidy_df)
    
    europe_visits = result["region"][
        (result["region"]["geography"] == "Europe") & 
        (result["region"]["metric"] == "visits")
    ]["value"].iloc[0]
    
    assert europe_visits == 175.0


def test_value_column_numeric_coercion():
    df = pd.DataFrame({
        "quarter": ["2019Q1", "2019Q2"],
        "geography": ["Europe", "North America"],
        "purpose": ["Holiday", "Business"],
        "transport": ["Air", "Air"],
        "visits": ["100.0", "not_a_number"],
        "expenditure_millions": [50.0, 75.0],
        "nights": [500.0, 300.0]
    })
    
    df = harmonise_columns(df)
    df["quarter"] = df["quarter"].map(normalise_quarter_label)
    df = annotate_coverage(df)
    
    for col in VALUE_COLS_DEFAULT:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    
    assert pd.isna(df["visits"].iloc[1])
    assert df["expenditure_millions"].dtype == float


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("2019 Q1", "2019Q1"),
        ("2019Q1", "2019Q1"),
        ("2019 - Q1", "2019Q1"),
        (" Q3 2020 ", "2020Q3"),
        ("2024-01", "2024Q1"),
        ("2023-12-15", "2023Q4"),
    ],
)
def test_normalise_quarter_label_accepts_varied_input_formats(raw, expected):
    assert normalise_quarter_label(raw) == expected


def test_output_structure_and_columns_preserved():
    wide_df = pd.DataFrame({
        "quarter": ["2019Q1", "2019Q2"],
        "geography": ["Europe", "North America"],
        "purpose": ["Holiday", "Business"],
        "transport": ["Air", "Air"],
        "visits": [100.0, 200.0],
        "expenditure_millions": [50.0, 75.0],
        "nights": [500.0, 300.0]
    })
    
    wide_df = harmonise_columns(wide_df)
    wide_df["quarter"] = wide_df["quarter"].map(normalise_quarter_label)
    wide_df = annotate_coverage(wide_df)
    tidy_df = to_tidy(wide_df)
    
    expected_columns = ["quarter", "geography", "purpose", "transport", "coverage", "method_break", "metric", "value"]
    assert all(col in tidy_df.columns for col in expected_columns)
    assert tidy_df["quarter"].dtype == object
    assert tidy_df["value"].dtype == float
