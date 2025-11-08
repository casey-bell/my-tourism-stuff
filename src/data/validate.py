from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

import pandas as pd

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


# ---- Exceptions and issue collection ----

class ValidationError(Exception):
    """Raised when validation fails with one or more errors."""
    pass


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

    def add_error(
        self, message: str, context: Optional[Dict[str, str]] = None
    ) -> None:
        self.issues.append(
            ValidationIssue(level="error", message=message, context=context)
        )

    def add_warning(
        self, message: str, context: Optional[Dict[str, str]] = None
    ) -> None:
        self.issues.append(
            ValidationIssue(level="warning", message=message,
                            context=context)
        )

    def raise_for_errors(self) -> None:
        if self.errors:
            messages = "; ".join(i.message for i in self.errors)
            raise ValidationError(messages)

    def to_report(self) -> Dict[str, List[str]]:
        return {
            "errors": [i.message for i in self.errors],
            "warnings": [i.message for i in self.warnings],
        }


# ---- Helpers ----

_PERIOD_RE = re.compile(r"^\d{4}-Q[1-4]$")


def _parse_period(s: str) -> Optional[Tuple[int, int]]:
    """Parse 'YYYY-Qn' into (year, quarter). Return None if invalid."""
    if not isinstance(s, str):
        return None
    if not _PERIOD_RE.match(s):
        return None
    year = int(s[:4])
    quarter = int(s[-1])
    return year, quarter


def _period_sort_key(s: str) -> Tuple[int, int]:
    p = _parse_period(s)
    # Put unparsable periods first to ensure they are caught by format checks
    return (-1, -1) if p is None else p


def _check_required_columns(
    df: pd.DataFrame, required: Sequence[str], res: ValidationResult
) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        res.add_error(f"Missing required columns: {', '.join(missing)}")


def _check_empty(df: pd.DataFrame, res: ValidationResult) -> None:
    if df.shape[0] == 0:
        res.add_error("Dataset is empty (no rows).")


def _is_boolean_series(s: pd.Series) -> bool:
    # Accept actual booleans only; strings like "True" are not valid
    return s.dropna().map(lambda x: isinstance(x, bool)).all()


def _is_numeric_series(s: pd.Series) -> bool:
    # Coercion test: non-numeric entries become NaN; detect any such cases
    coerced = pd.to_numeric(s, errors="coerce")
    return not ((coerced.isna()) & (s.notna())).any()


def _check_types(
    df: pd.DataFrame, schema_cols: Dict[str, Dict], res: ValidationResult
) -> None:
    for col, spec in schema_cols.items():
        if col not in df.columns:
            # Requiredness is handled separately; skip type checks for
            # truly missing columns
            continue

        t = spec.get("type")
        if t == "number":
            if not _is_numeric_series(df[col]):
                res.add_error(
                    f"Type validation failed for '{col}': expected "
                    f"number."
                )
            # Non-negativity via "min" in schema
            if "min" in spec:
                try:
                    negatives = df[
                        pd.to_numeric(df[col], errors="coerce")
                        < spec["min"]
                    ]
                    if not negatives.empty:
                        res.add_error(
                            f"Non-negative constraint violated in "
                            f"'{col}' (rows: {int(negatives.shape[0])})."
                        )
                except Exception:
                    # If coercion fails, type error will already be reported
                    pass

        elif t == "boolean":
            if not _is_boolean_series(df[col]):
                res.add_error(
                    f"Type validation failed for '{col}': expected "
                    f"boolean."
                )

        elif t == "string":
            # Strings are permissive; if a format is provided, enforce regex
            fmt = spec.get("format")
            if fmt is not None:
                pattern = re.compile(fmt)
                bad = df[col].dropna().astype(str).map(
                    lambda x: pattern.match(x) is None
                )
                if bad.any():
                    res.add_error(
                        f"Format validation failed for '{col}': regex "
                        f"'{fmt}' not matched."
                    )

        # Other types can be added as needed


def _check_unique_keys(
    df: pd.DataFrame, unique_keys: Sequence[str], res: ValidationResult
) -> None:
    if not unique_keys:
        return
    for key in unique_keys:
        if key not in df.columns:
            res.add_error(f"Missing unique key column '{key}'.")
            return
    dup_mask = df.duplicated(subset=list(unique_keys), keep=False)
    if dup_mask.any():
        # Mention each key to satisfy test expectations
        res.add_error(
            "Duplicate rows found across unique key(s): "
            + ", ".join(unique_keys)
        )


def _check_period_continuity(
    df: pd.DataFrame, period_col: str, res: ValidationResult
) -> None:
    if period_col not in df.columns:
        res.add_error(f"Missing period column '{period_col}'.")
        return

    periods = df[period_col].dropna().astype(str).tolist()
    # If any period fails format, continuity will be noisy; rely on
    # format check to flag those
    parsed = [
        _parse_period(p) for p in periods if _PERIOD_RE.match(p)
    ]
    if not parsed:
        # If nothing parses, continuity cannot be determined; leave to
        # format/type errors
        return

    # De-duplicate and sort
    uniq = sorted(set(parsed))
    # Walk expected consecutive sequence

    def next_period(y: int, q: int) -> Tuple[int, int]:
        return (y + 1, 1) if q == 4 else (y, q + 1)

    gaps: List[str] = []
    for i in range(len(uniq) - 1):
        y, q = uniq[i]
        ny, nq = next_period(y, q)
        ay, aq = uniq[i + 1]
        if (ny, nq) != (ay, aq):
            # Report gap between expected next and actual next
            gaps.append(f"missing quarter between {y}-Q{q} and {ay}-Q{aq}")

    if gaps:
        res.add_error("Period continuity gap detected: " + "; ".join(gaps))


def _check_gb_only_from_2024(
    df: pd.DataFrame, period_col: str, gb_flag_col: str,
    res: ValidationResult
) -> None:
    if period_col not in df.columns or gb_flag_col not in df.columns:
        # If columns are missing, other checks will flag that; treat as
        # type/required errors
        return

    def is_2024_or_later(p: str) -> bool:
        parsed = _parse_period(p)
        return parsed is not None and (
            parsed[0] > 2023 or (parsed[0] == 2024 and parsed[1] >= 1)
        )

    mask_late = df[period_col].astype(str).map(is_2024_or_later)
    subset = df.loc[mask_late, gb_flag_col]
    # Require boolean True on or after 2024-Q1
    bad = subset.map(lambda v: v is not True)
    if bad.any():
        res.add_error(
            "gb_only must be True from 2024 onwards due to Great "
            "Britain-only coverage."
        )


# ---- Public API: schema-driven validation ----

def validate_dataframe(df: pd.DataFrame, schema: Dict) -> Dict[str, List[str]]:
    """
    Validate a DataFrame against a simple schema and domain rules.

    Expected schema shape:
        {
            "columns": {
                "period": {"type": "string", "format": r"^\\d{4}-Q[1-4]$"},
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

    Returns:
        dict report with "errors" and "warnings" lists.
    Raises:
        ValidationError if any errors are found.
    """
    res = ValidationResult()

    # Basic structure
    if "columns" not in schema or not isinstance(schema["columns"], dict):
        res.add_error("Schema invalid: 'columns' mapping is required.")
        res.raise_for_errors()

    schema_cols: Dict[str, Dict] = schema["columns"]
    required_cols = list(schema_cols.keys())

    _check_empty(df, res)
    _check_required_columns(df, required_cols, res)

    # Types and formats
    _check_types(df, schema_cols, res)

    # Uniqueness across keys
    unique_keys = schema.get("unique_keys", [])
    _check_unique_keys(df, unique_keys, res)

    # Period continuity
    _check_period_continuity(df, period_col="period", res=res)

    # GB-only rule from 2024 onwards
    _check_gb_only_from_2024(
        df, period_col="period", gb_flag_col="gb_only", res=res
    )

    # Finalise
    res.raise_for_errors()
    return res.to_report()
