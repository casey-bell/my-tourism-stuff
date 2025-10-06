"""
Validation utilities for tourism data.

This module enforces schema, type, range, and coverage checks to ensure
analysis-ready datasets are consistent and trustworthy across quarters
and breakdown dimensions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Iterable, List, Optional, Sequence, Set, Dict

import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---- Reference values and expected domains ----

VALID_GEOGRAPHY_GROUPS: Set[str] = {"North America", "Europe", "Other Countries"}
VALID_PURPOSES: Set[str] = {"Holiday", "Business", "VFR", "Miscellaneous"}
VALID_TRANSPORT_MODES: Set[str] = {"Air", "Sea", "Tunnel"}

NON_NEGATIVE_COLUMNS: Set[str] = {
    "visits_thousands",
    "expenditure_millions",
    "nights_thousands",
}

# Quarters: Q1 2019 to Q4 2024 inclusive
VALID_QUARTERS: List[str] = [
    f"Q{q} {y}" for y in range(2019, 2025) for q in range(1, 5)
]


@dataclass
class ValidationIssue:
    """Represents a single validation finding."""
    level: str  # "error" or "warning"
    message: str
    context: Optional[Dict[str, str]] = None


@dataclass
class ValidationResult:
    """Collects validation issues and provides summary helpers."""
    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not any(i.level == "error" for i in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def warnings(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.level == "warning"]

    def raise_for_errors(self) -> None:
        if self.errors:
            messages = "; ".join(i.message for i in self.errors)
            raise ValidationError(messages)

    def log(self) -> None:
        for issue in self.issues:
            if issue.level == "error":
                logger.error(issue.message)
            else:
                logger.warning(issue.message)


class ValidationError(Exception):
    """Raised when validation fails with one or more errors."""
    pass


# ---- Core validation functions ----

def validate_required_columns(
    df: pd.DataFrame,
    required: Sequence[str],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    res = result or ValidationResult()
    missing = [c for c in required if c not in df.columns]
    if missing:
        res.issues.append(
            ValidationIssue(
                level="error",
                message=f"Missing required columns: {', '.join(missing)}",
            )
        )
    return res


def validate_no_extra_columns(
    df: pd.DataFrame,
    allowed: Sequence[str],
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    res = result or ValidationResult()
    extras = [c for c in df.columns if c not in allowed]
    if extras:
        res.issues.append(
            ValidationIssue(
                level="warning",
                message=f"Unexpected columns present: {', '.join(extras)}",
            )
        )
    return res


def validate_quarters(
    df: pd.DataFrame,
    quarter_column: str = "quarter",
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    res = result or ValidationResult()
    if quarter_column not in df.columns:
        res.issues.append(
            ValidationIssue(level="error", message=f"Column '{quarter_column}' not found")
        )
        return res

    # Check domain membership
    invalid = sorted(set(df[quarter_column]) - set(VALID_QUARTERS))
    if invalid:
        res.issues.append(
            ValidationIssue(
                level="error",
                message=f"Invalid quarter values: {', '.join(map(str, invalid))}",
            )
        )

    # Check continuity coverage if quarters are expected to be complete
    # Only warn: some breakdown tables may not cover all quarters.
    present = sorted(set(df[quarter_column]), key=lambda s: (int(s.split()[1]), int(s[1])))
    missing = [q for q in VALID_QUARTERS if q not in present]
    if missing:
        res.issues.append(
            ValidationIssue(
                level="warning",
                message=f"Missing quarters in dataset: {', '.join(missing)}",
            )
        )
    return res


def validate_domains(
    df: pd.DataFrame,
    column: str,
    allowed_values: Iterable[str],
    strict: bool = True,
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    res = result or ValidationResult()
    if column not in df.columns:
        res.issues.append(
            ValidationIssue(level="warning", message=f"Column '{column}' not found")
        )
        return res

    allowed = set(allowed_values)
    values = set(df[column].dropna().astype(str))
    unexpected = sorted(values - allowed)
    if unexpected:
        level = "error" if strict else "warning"
        res.issues.append(
            ValidationIssue(
                level=level,
                message=f"Unexpected values in '{column}': {', '.join(unexpected)}",
            )
        )
    return res


def validate_non_negative(
    df: pd.DataFrame,
    columns: Iterable[str] = NON_NEGATIVE_COLUMNS,
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    res = result or ValidationResult()
    for col in columns:
        if col not in df.columns:
            res.issues.append(
                ValidationIssue(level="error", message=f"Column '{col}' not found")
            )
            continue
        negatives = df[df[col] < 0]
        if not negatives.empty:
            count = int(negatives.shape[0])
            res.issues.append(
                ValidationIssue(
                    level="error",
                    message=f"Negative values found in '{col}' (rows: {count})",
                )
            )
    return res


def validate_coverage_break(
    df: pd.DataFrame,
    year_break: int = 2024,
    geography_column: str = "geography",
    quarter_column: str = "quarter",
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Flags rows at or after the coverage break year that include Northern Ireland,
    reflecting the methodological change to Great Britain-only coverage from 2024.
    """
    res = result or ValidationResult()

    missing_cols = [c for c in (geography_column, quarter_column) if c not in df.columns]
    if missing_cols:
        res.issues.append(
            ValidationIssue(
                level="warning",
                message=f"Coverage check skipped; columns missing: {', '.join(missing_cols)}",
            )
        )
        return res

    # Extract year from quarter labels like "Q1 2024"
    def _year(q: str) -> Optional[int]:
        try:
            return int(q.split()[-1])
        except Exception:
            return None

    mask_break = df[quarter_column].apply(_year).fillna(0) >= year_break
    mask_ni = df[geography_column].astype(str).str.contains("Northern Ireland", case=False, na=False)
    offending = df[mask_break & mask_ni]

    if not offending.empty:
        res.issues.append(
            ValidationIssue(
                level="error",
                message=(
                    "Rows at or after 2024 include Northern Ireland despite Great Britain-only coverage. "
                    f"Affected rows: {offending.shape[0]}"
                ),
            )
        )
    return res


def validate_schema_and_types(
    df: pd.DataFrame,
    required_columns: Sequence[str],
    numeric_columns: Sequence[str] = (),
    result: Optional[ValidationResult] = None,
) -> ValidationResult:
    """
    Composite check: required columns present and numeric columns coercible to numbers.
    """
    res = result or ValidationResult()
    res = validate_required_columns(df, required_columns, res)

    for col in numeric_columns:
        if col not in df.columns:
            res.issues.append(ValidationIssue(level="error", message=f"Column '{col}' not found"))
            continue
        # Attempt coercion to numeric; report rows that fail
        coerced = pd.to_numeric(df[col], errors="coerce")
        bad = coerced.isna() & df[col].notna()
        if bad.any():
            count = int(bad.sum())
            res.issues.append(
                ValidationIssue(
                    level="error",
                    message=f"Non-numeric values found in '{col}' (rows: {count})",
                )
            )
    return res


# ---- Convenience: end-to-end validation ----

def validate_all(
    df: pd.DataFrame,
    expected_columns: Sequence[str],
    strict_domains: bool = True,
    raise_on_error: bool = True,
) -> ValidationResult:
    """
    Runs a suite of validations suitable for the main tidy datasets.

    Parameters:
        df: Input DataFrame.
        expected_columns: Columns expected to exist in df.
        strict_domains: If True, domain violations are errors; otherwise warnings.
        raise_on_error: If True, raises ValidationError on any error.

    Returns:
        ValidationResult containing all issues.
    """
    res = ValidationResult()

    # Schema and types
    res = validate_schema_and_types(
        df=df,
        required_columns=expected_columns,
        numeric_columns=[c for c in NON_NEGATIVE_COLUMNS if c in expected_columns],
        result=res,
    )

    # Quarters
    res = validate_quarters(df, quarter_column="quarter", result=res)

    # Domains (best-effort; only if present)
    res = validate_domains(
        df, "geography", VALID_GEOGRAPHY_GROUPS, strict=strict_domains, result=res
    )
    res = validate_domains(
        df, "purpose", VALID_PURPOSES, strict=strict_domains, result=res
    )
    res = validate_domains(
        df, "transport", VALID_TRANSPORT_MODES, strict=strict_domains, result=res
    )

    # Ranges and coverage
    res = validate_non_negative(df, columns=NON_NEGATIVE_COLUMNS, result=res)
    res = validate_coverage_break(
        df, year_break=2024, geography_column="geography", quarter_column="quarter", result=res
    )

    if raise_on_error:
        res.raise_for_errors()
    return res
