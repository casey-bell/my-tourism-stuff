# src/config.py
from pathlib import Path
from typing import Dict, List, Tuple

# Project paths
PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = PROJECT_ROOT / "data"
RAW_DIR: Path = DATA_DIR / "raw"
INTERIM_DIR: Path = DATA_DIR / "interim"
NOTEBOOKS_DIR: Path = PROJECT_ROOT / "notebooks"
REPORTS_DIR: Path = PROJECT_ROOT / "reports"

# Raw data files
RAW_EXCEL_FILENAME: str = "overseas-visitors-to-britain-2024.xlsx"
RAW_EXCEL_PATH: Path = RAW_DIR / RAW_EXCEL_FILENAME

# Interim output files
VISITS_BY_QUARTER_FILENAME: str = "visits_by_quarter.csv"
EXPENDITURE_BY_PURPOSE_FILENAME: str = "expenditure_by_purpose.csv"
NIGHTS_BY_GEOGRAPHY_FILENAME: str = "nights_by_geography.csv"
DATA_DICTIONARY_FILENAME: str = "data_dictionary.json"

VISITS_BY_QUARTER_PATH: Path = INTERIM_DIR / VISITS_BY_QUARTER_FILENAME
EXPENDITURE_BY_PURPOSE_PATH: Path = INTERIM_DIR / EXPENDITURE_BY_PURPOSE_FILENAME
NIGHTS_BY_GEOGRAPHY_PATH: Path = INTERIM_DIR / NIGHTS_BY_GEOGRAPHY_FILENAME
DATA_DICTIONARY_PATH: Path = INTERIM_DIR / DATA_DICTIONARY_FILENAME

# Core column names used across datasets
COL_QUARTER: str = "quarter"
COL_COVERAGE: str = "coverage"  # "UK" for 2019–2023, "Great Britain" for 2024 onwards
COL_GEOGRAPHY: str = "geography"  # e.g., "Europe", "North America", "Other Countries"
COL_COUNTRY: str = "country"  # e.g., "France", "United States"
COL_PURPOSE: str = "purpose"  # e.g., "Holiday", "Business", "VFR", "Miscellaneous"
COL_TRANSPORT: str = "transport"  # e.g., "Air", "Sea", "Tunnel"

COL_VISITS_K: str = "visits_thousands"
COL_EXPENDITURE_M: str = "expenditure_millions"
COL_NIGHTS_K: str = "nights_thousands"

# Normalised categorical values
GEOGRAPHY_GROUPS: List[str] = ["Europe", "North America", "Other Countries"]

PURPOSE_GROUPS: Dict[str, str] = {
    "Holiday": "Holiday",
    "Business": "Business",
    "Visiting Friends & Relatives": "VFR",
    "Visiting friends and relatives": "VFR",
    "VFR": "VFR",
    "Miscellaneous": "Miscellaneous",
    "Other": "Miscellaneous",
}

TRANSPORT_MODES: Dict[str, str] = {
    "Air": "Air",
    "Sea": "Sea",
    "Tunnel": "Tunnel",
    "Rail": "Tunnel",  # Eurostar often reported under tunnel
}

# Coverage rules (methodological break in 2024)
COVERAGE_BY_YEAR: Dict[int, str] = {
    2019: "UK",
    2020: "UK",
    2021: "UK",
    2022: "UK",
    2023: "UK",
    2024: "Great Britain",
}

DEFAULT_COVERAGE_PRE_2024: str = "UK"
DEFAULT_COVERAGE_2024_ONWARDS: str = "Great Britain"

# Expected schemas for interim outputs (column order and basic types)
SCHEMA_VISITS_BY_QUARTER: List[Tuple[str, str]] = [
    (COL_QUARTER, "string"),
    (COL_COVERAGE, "string"),
    (COL_GEOGRAPHY, "string"),
    (COL_VISITS_K, "number"),
]

SCHEMA_EXPENDITURE_BY_PURPOSE: List[Tuple[str, str]] = [
    (COL_QUARTER, "string"),
    (COL_COVERAGE, "string"),
    (COL_PURPOSE, "string"),
    (COL_EXPENDITURE_M, "number"),
]

SCHEMA_NIGHTS_BY_GEOGRAPHY: List[Tuple[str, str]] = [
    (COL_QUARTER, "string"),
    (COL_COVERAGE, "string"),
    (COL_GEOGRAPHY, "string"),
    (COL_NIGHTS_K, "number"),
]

# Quarter parsing
# Accepts formats like "2019 Q1", "Q1 2019", or ISO-like "2019Q1"
QUARTER_PATTERNS: List[str] = [
    r"^(?P<year>\d{4})\s*[Qq]\s*(?P<q>[1-4])$",
    r"^[Qq]\s*(?P<q>[1-4])\s*(?P<year>\d{4})$",
    r"^(?P<year>\d{4})[Qq](?P<q>[1-4])$",
]

# Numeric validity thresholds (basic sanity checks)
MIN_VISITS_THOUSANDS: float = 0.0
MIN_EXPENDITURE_MILLIONS: float = 0.0
MIN_NIGHTS_THOUSANDS: float = 0.0

# Display and plotting defaults
FIGURES_DIR: Path = REPORTS_DIR / "figures"
DEFAULT_FIG_SIZE: Tuple[int, int] = (10, 6)
DEFAULT_PALETTE: str = "deep"

# Data dictionary entries (keys used when generating JSON)
DATA_DICTIONARY_ENTRIES: Dict[str, Dict[str, str]] = {
    COL_QUARTER: {
        "description": "Calendar quarter identifier, e.g., '2019 Q1'.",
        "type": "string",
        "example": "2021 Q3",
    },
    COL_COVERAGE: {
        "description": "Geographical coverage of the estimates.",
        "type": "string",
        "allowed": "UK (2019–2023), Great Britain (2024 onwards)",
    },
    COL_GEOGRAPHY: {
        "description": "Broad geography grouping of country of residence.",
        "type": "string",
        "allowed": ", ".join(GEOGRAPHY_GROUPS),
    },
    COL_COUNTRY: {
        "description": "Country of residence when provided at country level.",
        "type": "string",
        "example": "United States",
    },
    COL_PURPOSE: {
        "description": "Main purpose of visit.",
        "type": "string",
        "allowed": ", ".join(sorted(set(PURPOSE_GROUPS.values()))),
    },
    COL_TRANSPORT: {
        "description": "Mode of transport used to enter/leave Great Britain.",
        "type": "string",
        "allowed": ", ".join(sorted(set(TRANSPORT_MODES.values()))),
    },
    COL_VISITS_K: {
        "description": "Number of visits, expressed in thousands.",
        "type": "number",
        "unit": "thousands",
    },
    COL_EXPENDITURE_M: {
        "description": "Visitor expenditure, expressed in millions of pounds.",
        "type": "number",
        "unit": "£ millions",
    },
    COL_NIGHTS_K: {
        "description": "Number of nights stayed, expressed in thousands.",
        "type": "number",
        "unit": "thousands",
    },
}

# Helper functions
def coverage_for_year(year: int) -> str:
    """
    Return the coverage label for a given year.
    """
    if year >= 2024:
        return DEFAULT_COVERAGE_2024_ONWARDS
    return COVERAGE_BY_YEAR.get(year, DEFAULT_COVERAGE_PRE_2024)


def ensure_directories() -> None:
    """
    Create required output directories if they do not already exist.
    """
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
