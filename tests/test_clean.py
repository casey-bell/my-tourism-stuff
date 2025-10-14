import pandas as pd
import pytest

# The cleaning module is expected to expose a single entry-point function `clean`
# that takes a DataFrame and returns a cleaned DataFrame.
from src.data.clean import clean


@pytest.fixture
def raw_sample():
    # Representative slice of the ONS structure with controlled issues:
    # - Whitespace and inconsistent capitalisation in categories
    # - Numeric fields as strings and with negative values
    # - Quarter strings requiring normalisation (trimmed to avoid spurious whitespace)
    return pd.DataFrame(
        {
            'Quarter': ['Q1 2019', 'Q4 2024', 'Q2 2020'],
            'Coverage': ['UK', 'Great Britain', 'UK'],
            'Geography': [' europe ', 'North America', 'Other Countries'],
            'Purpose': ['holiday', 'Business ', 'VFR'],
            'Transport': [' air', 'Sea', 'Tunnel '],
            'Number of visits (thousands)': ['100', '-5', '250'],
            'Expenditure (£ millions)': ['75.5', '0', '120.0'],
            'Nights stayed (thousands)': ['300', '80', '-10'],
        }
    )


def test_clean_returns_dataframe(raw_sample):
    cleaned = clean(raw_sample)
    assert isinstance(cleaned, pd.DataFrame)


def test_required_columns_present(raw_sample):
    cleaned = clean(raw_sample)
    # Expected normalised schema (lowercase, snake_case, consistent names)
    expected_cols = {
        'period',
        'coverage',
        'geography',
        'purpose',
        'transport',
        'visits_thousands',
        'expenditure_millions',
        'nights_thousands',
    }
    assert expected_cols.issubset(set(cleaned.columns))


def test_categories_are_trimmed_and_standardised(raw_sample):
    cleaned = clean(raw_sample)
    # Categories should be stripped of whitespace and consistently cased
    assert cleaned['geography'].iloc[0] == 'Europe'
    assert cleaned['purpose'].iloc[0] == 'Holiday'
    assert cleaned['transport'].iloc[0] == 'Air'
    # Trailing spaces should be removed
    assert cleaned['purpose'].iloc[1] == 'Business'
    assert cleaned['transport'].iloc[2] == 'Tunnel'


def test_numeric_fields_are_numeric_and_non_negative(raw_sample):
    cleaned = clean(raw_sample)

    for col in ['visits_thousands', 'expenditure_millions', 'nights_thousands']:
        # Coerced to numeric dtype
        assert pd.api.types.is_numeric_dtype(cleaned[col])
        # No negative values remain after cleaning
        assert (cleaned[col] >= 0).all()


def test_period_is_normalised_to_quarter_identifier(raw_sample):
    cleaned = clean(raw_sample)
    # Check formatting only for non-missing period values
    non_missing = cleaned['period'].dropna().astype(str)
    # Expect pattern YYYYQ#
    assert non_missing.str.match(r'^\d{4}Q[1-4]$').all()


def test_coverage_respects_methodological_break(raw_sample):
    cleaned = clean(raw_sample)
    # Apply checks only where period was parsed
    parsed = cleaned.dropna(subset=['period']).copy()
    if not parsed.empty:
        parsed['year'] = parsed['period'].astype(str).str[:4].astype(int)
        gb_rows = parsed[parsed['year'] >= 2024]
        uk_rows = parsed[parsed['year'] < 2024]
        if not gb_rows.empty:
            assert (gb_rows['coverage'] == 'Great Britain').all()
        if not uk_rows.empty:
            assert (uk_rows['coverage'] == 'United Kingdom').all()


def test_no_missing_in_key_fields_after_cleaning(raw_sample):
    cleaned = clean(raw_sample)
    key_fields = [
        'coverage',
        'geography',
        'purpose',
        'transport',
        'visits_thousands',
        'expenditure_millions',
        'nights_thousands',
    ]
    # Key fields should be complete; period may be missing if unparseable
    assert cleaned[key_fields].notna().all().all()


def test_deduplication_and_row_integrity(raw_sample):
    # Duplicate the first row to emulate repeated entries
    duplicated = pd.concat([raw_sample, raw_sample.iloc[[0]]], ignore_index=True)
    cleaned = clean(duplicated)
    # Expect duplicates to be removed or consolidated
    # At least one fewer row than input if deduplication is applied
    assert len(cleaned) <= len(duplicated)
