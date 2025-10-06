"""
Schemas for tourism data processing.

Defines explicit, testable schemas for cleaned and transformed datasets,
along with lightweight validators. The aim is to establish a data
contract so each pipeline stage can rely on consistent column names,
types, categories, and simple constraints.

This module uses only the standard library to avoid coupling to specific
dataframe implementations. Optional helper functions are provided for
validating rows (dict-like) and, if desired, dataframes when passed in
manually.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union
import re


# ---------------------------
# Enumerations and constants
# ---------------------------

GEOGRAPHY_GROUPS: Tuple[str, ...] = ("North America", "Europe", "Other Countries")

PURPOSES: Tuple[str, ...] = ("Holiday", "Business", "VFR", "Miscellaneous")

TRANSPORT_MODES: Tuple[str, ...] = ("Air", "Sea", "Tunnel")

COVERAGE_VALUES: Tuple[str, ...] = ("UK", "Great Britain")

# Regions are indicative; adjust to match the dataset as required.
UK_REGIONS: Tuple[str, ...] = (
    "North East",
    "North West",
    "Yorkshire and The Humber",
    "East Midlands",
    "West Midlands",
    "East of England",
    "London",
    "South East",
    "South West",
    "Wales",
    "Scotland",
    "Northern Ireland",
)

# Period string pattern, e.g., "2019Q1"
PERIOD_PATTERN = re.compile(r"^(20\d{2})Q([1-4])$")


# ---------------------------
# Schema model
# ---------------------------

@dataclass(frozen=True)
class FieldSpec:
    """Specification for a single column/field in a dataset."""
    name: str
    py_type: Union[type, Tuple[type, ...]]
    required: bool = True
    allowed_values: Optional[Iterable[Any]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    regex: Optional[re.Pattern] = None
    validator: Optional[Callable[[Any], bool]] = None
    description: str = ""


@dataclass(frozen=True)
class Schema:
    """Schema comprising ordered field specifications."""
    name: str
    fields: Tuple[FieldSpec, ...] = field(default_factory=tuple)
    description: str = ""

    def as_dict(self) -> Dict[str, FieldSpec]:
        return {f.name: f for f in self.fields}


# ---------------------------
# Core schemas
# ---------------------------

def cleaned_visitors_schema() -> Schema:
    """
    Schema for cleaned, row-level observations post-ingest/clean.

    Columns:
    - year: calendar year (int), e.g., 2019
    - quarter: quarter number (int 1–4)
    - period: canonical period label 'YYYYQn'
    - coverage: 'UK' for 2019–2023, 'Great Britain' from 2024 onwards
    - geography_group: 'North America' | 'Europe' | 'Other Countries'
    - purpose: 'Holiday' | 'Business' | 'VFR' | 'Miscellaneous'
    - transport: 'Air' | 'Sea' | 'Tunnel'
    - region: UK region visited (string; NI excluded from GB coverage)
    - country: country of residence (string)
    - visits_k: number of visits (thousands; non-negative)
    - expenditure_m_gbp: expenditure (£ millions; non-negative)
    - nights_k: nights stayed (thousands; non-negative)
    """
    def _quarter_ok(x: Any) -> bool:
        return isinstance(x, int) and 1 <= x <= 4

    def _period_ok(x: Any) -> bool:
        return isinstance(x, str) and PERIOD_PATTERN.match(x) is not None

    fields = (
        FieldSpec(
            name="year",
            py_type=int,
            min_value=2019,
            description="Calendar year."
        ),
        FieldSpec(
            name="quarter",
            py_type=int,
            validator=_quarter_ok,
            description="Quarter number (1–4)."
        ),
        FieldSpec(
            name="period",
            py_type=str,
            regex=PERIOD_PATTERN,
            validator=_period_ok,
            description="Period label in 'YYYYQn' format."
        ),
        FieldSpec(
            name="coverage",
            py_type=str,
            allowed_values=COVERAGE_VALUES,
            description="Geographical coverage."
        ),
        FieldSpec(
            name="geography_group",
            py_type=str,
            allowed_values=GEOGRAPHY_GROUPS,
            description="Geographical grouping."
        ),
        FieldSpec(
            name="purpose",
            py_type=str,
            allowed_values=PURPOSES,
            description="Purpose of visit."
        ),
        FieldSpec(
            name="transport",
            py_type=str,
            allowed_values=TRANSPORT_MODES,
            description="Transport mode used."
        ),
        FieldSpec(
            name="region",
            py_type=str,
            description="UK region visited."
        ),
        FieldSpec(
            name="country",
            py_type=str,
            description="Country of residence."
        ),
        FieldSpec(
            name="visits_k",
            py_type=(int, float),
            min_value=0.0,
            description="Visits in thousands; non-negative."
        ),
        FieldSpec(
            name="expenditure_m_gbp",
            py_type=(int, float),
            min_value=0.0,
            description="Expenditure in £ millions; non-negative."
        ),
        FieldSpec(
            name="nights_k",
            py_type=(int, float),
            min_value=0.0,
            description="Nights in thousands; non-negative."
        ),
    )
    return Schema(
        name="cleaned_visitors",
        fields=fields,
        description="Cleaned, normalised visitors dataset."
    )


def quarterly_visitors_schema() -> Schema:
    """
    Schema for quarterly, analysis-ready aggregates.

    Columns:
    - year, quarter, period, coverage (as above)
    - visits_k, expenditure_m_gbp, nights_k (aggregated)
    - visits_per_night: visits_k / nights_k (float; non-negative, may be NaN if nights_k=0)
    - spend_per_visit: expenditure_m_gbp / visits_k (float; non-negative, may be NaN if visits_k=0)
    """
    fields = (
        FieldSpec(name="year", py_type=int, min_value=2019, description="Calendar year."),
        FieldSpec(name="quarter", py_type=int, validator=lambda x: isinstance(x, int) and 1 <= x <= 4,
                  description="Quarter number (1–4)."),
        FieldSpec(name="period", py_type=str, regex=PERIOD_PATTERN, description="Period label 'YYYYQn'."),
        FieldSpec(name="coverage", py_type=str, allowed_values=COVERAGE_VALUES, description="Geographical coverage."),
        FieldSpec(name="visits_k", py_type=(int, float), min_value=0.0, description="Visits (thousands)."),
        FieldSpec(name="expenditure_m_gbp", py_type=(int, float), min_value=0.0, description="Expenditure (£ millions)."),
        FieldSpec(name="nights_k", py_type=(int, float), min_value=0.0, description="Nights (thousands)."),
        FieldSpec(name="visits_per_night", py_type=(int, float), min_value=0.0,
                  description="Visits per night (derived)."),
        FieldSpec(name="spend_per_visit", py_type=(int, float), min_value=0.0,
                  description="Spend per visit (derived)."),
    )
    return Schema(
        name="quarterly_visitors",
        fields=fields,
        description="Quarterly aggregates with derived ratios."
    )


def validation_report_schema() -> Schema:
    """
    Schema for validation report artefact (JSON-friendly).

    Columns:
    - dataset: name of the dataset validated
    - timestamp: ISO 8601 string of validation run
    - status: 'pass' | 'fail'
    - checks_run: integer count of checks executed
    - failures: integer count of failed checks
    - messages: list of
