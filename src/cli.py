"""
Command-line interface for the my-tourism-stuff pipeline.
"""

from __future__ import annotations

import argparse
import importlib
import logging
import sys
from pathlib import Path
from typing import Optional

# Explicitly import and use these as requested
from src.data.transform import harmonise_columns
from src.data.validate import ValidationResult

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO


def setup_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT)


def run_pipeline() -> int:
    """Run the project's pipeline."""
    try:
        from src.pipeline import make_visitors_by_quarter

        make_visitors_by_quarter()
        return 0
    except Exception:
        logging.exception("Pipeline execution failed")
        return 1


def process_data() -> int:
    """Load and process data."""
    try:
        from src.data.load import load_table_1

        load_table_1()
        return 0
    except Exception:
        logging.exception("Data loading failed")
        return 1


def validate_data() -> int:
    """Run data validation.

    Uses ValidationResult if the validation function returns it.
    Looks for a callable named `run_validations` or `validate`
    in src.data.validate.
    """
    try:
        validate_mod = importlib.import_module("src.data.validate")
        validate_fn = (
            getattr(validate_mod, "run_validations", None)
            or getattr(validate_mod, "validate", None)
        )

        if callable(validate_fn):
            result = validate_fn()
            # Use ValidationResult explicitly as requested
            if isinstance(result, ValidationResult):
                # Try common success indicators
                success = False
                if hasattr(result, "success"):
                    success = bool(getattr(result, "success"))
                elif hasattr(result, "ok"):
                    success = bool(getattr(result, "ok"))
                else:
                    # Fallback to truthiness if no clear flag is present
                    success = bool(result)

                if success:
                    logging.info("Validation completed successfully")
                    return 0
                else:
                    # Try to surface some detail if available
                    errors = getattr(result, "errors", None)
                    if errors:
                        logging.error(
                            "Validation failed with %d errors", len(errors)
                        )
                    else:
                        logging.error("Validation failed")
                    return 1
            else:
                # If not a ValidationResult, still consider completion a
                # success
                logging.info("Validation function completed")
                return 0
        else:
            logging.warning(
                "No validation function found in src.data.validate "
                "(expected run_validations() or validate()). Skipping."
            )
            return 0
    except Exception:
        logging.exception("Data validation failed")
        return 1


def transform_data() -> int:
    """Run data transformation.

    Loads the primary table and applies harmonise_columns to it.
    """
    try:
        from src.data.load import load_table_1

        df = load_table_1()
        # Use harmonise_columns explicitly as requested
        transformed = harmonise_columns(df)
        # Best-effort informative logging without assuming DataFrame
        # specifics
        n_cols = None
        try:
            n_cols = transformed.shape[1]  # type: ignore[attr-defined]
        except Exception:
            pass
        if n_cols is not None:
            logging.info(
                "Transformation completed successfully with %d columns",
                n_cols,
            )
        else:
            logging.info("Transformation completed successfully")
        return 0
    except Exception:
        logging.exception("Data transformation failed")
        return 1


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="my-tourism-cli",
        description=(
            "Run the my-tourism-stuff data pipeline and related tasks"
        ),
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub_run = sub.add_parser("run", help="Execute the full pipeline")
    sub_run.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    sub_process = sub.add_parser(
        "process-data",
        help="Run data loading and processing step",
    )
    sub_process.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    sub_validate = sub.add_parser(
        "validate",
        help="Run data validation",
    )
    sub_validate.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    sub_transform = sub.add_parser(
        "transform",
        help="Run data transformation",
    )
    sub_transform.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging",
    )

    sub_ls = sub.add_parser(
        "ls-data",
        help="List files under data/ and their sizes",
    )
    sub_ls.add_argument(
        "--path",
        default="data",
        help="Path to data directory",
    )

    return parser.parse_args(argv)


def list_data(path: str) -> int:
    p = Path(path)
    if not p.exists():
        logging.error("Path does not exist: %s", path)
        return 2

    for fp in sorted(p.rglob("*")):
        if fp.is_file():
            try:
                size_kb = fp.stat().st_size / 1024
                rel = fp.relative_to(Path.cwd())
                print(f"{rel} - {size_kb:.1f} KB")
            except Exception:
                rel = fp.relative_to(Path.cwd())
                print(f"{rel} - size unavailable")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    args = parse_args(argv)

    level = (
        logging.DEBUG
        if getattr(args, "debug", False)
        else DEFAULT_LOG_LEVEL
    )
    setup_logging(level)

    if args.command == "run":
        return run_pipeline()
    if args.command == "process-data":
        return process_data()
    if args.command == "validate":
        return validate_data()
    if args.command == "transform":
        return transform_data()
    if args.command == "ls-data":
        return list_data(args.path)

    logging.error("Unknown command: %s", args.command)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
