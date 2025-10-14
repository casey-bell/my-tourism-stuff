"""
Command-line interface for the my-tourism-stuff pipeline.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Callable, Optional

LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
DEFAULT_LOG_LEVEL = logging.INFO


def setup_logging(level: int = DEFAULT_LOG_LEVEL) -> None:
    logging.basicConfig(level=level, format=LOG_FORMAT)


def resolve_callable(module_path: str, attr_names: tuple[str, ...]) -> Optional[Callable]:
    """
    Try to import a callable from the given module path using several attribute names.
    Returns the first callable found, or None.
    """
    try:
        module = __import__(module_path, fromlist=["*"])
    except Exception as exc:
        logging.debug("Failed to import %s: %s", module_path, exc)
        return None

    for name in attr_names:
        candidate = getattr(module, name, None)
        if callable(candidate):
            logging.debug("Resolved %s.%s", module_path, name)
            return candidate

    logging.debug("No callable found in %s for names %s", module_path, attr_names)
    return None


def run_pipeline() -> int:
    """
    Run the project's pipeline. This function attempts to locate a sensible entry point
    in src.pipeline (common names: run, main, run_pipeline) and invoke it.
    """
    entry = resolve_callable("src.pipeline", ("run_pipeline", "run", "main"))
    if entry is None:
        logging.error("Could not locate a pipeline entry point in src.pipeline")
        return 2

    try:
        result = entry()
        if isinstance(result, int):
            return result
        return 0
    except SystemExit as se:
        logging.debug("Pipeline called SystemExit(%s)", se.code)
        return int(se.code or 0)
    except Exception:
        logging.exception("Pipeline execution failed")
        return 3


def process_data() -> int:
    """
    Call the process/data specific function if present.
    """
    entry = resolve_callable("src.data.load", ("main", "load"))
    if entry:
        try:
            entry()
            return 0
        except Exception:
            logging.exception("Data loading failed")
            return 4

    logging.error("No data loading entry point found in src.data.load")
    return 2


def validate_data() -> int:
    entry = resolve_callable("src.data.validate", ("main", "validate"))
    if entry:
        try:
            entry()
            return 0
        except Exception:
            logging.exception("Data validation failed")
            return 5

    logging.error("No validation entry point found in src.data.validate")
    return 2


def transform_data() -> int:
    entry = resolve_callable("src.data.transform", ("main", "transform"))
    if entry:
        try:
            entry()
            return 0
        except Exception:
            logging.exception("Data transformation failed")
            return 6

    logging.error("No transformation entry point found in src.data.transform")
    return 2


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="my-tourism-cli",
        description="Run the my-tourism-stuff data pipeline and related tasks",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub_run = sub.add_parser("run", help="Execute the full pipeline")
    sub_run.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub_process = sub.add_parser("process-data", help="Run data loading and processing step")
    sub_process.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub_validate = sub.add_parser("validate", help="Run data validation")
    sub_validate.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub_transform = sub.add_parser("transform", help="Run data transformation")
    sub_transform.add_argument("--debug", action="store_true", help="Enable debug logging")

    sub_ls = sub.add_parser("ls-data", help="List files under data/ and their sizes")
    sub_ls.add_argument("--path", default="data", help="Path to data directory")

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
                print(f"{fp.relative_to(Path.cwd())} - {size_kb:.1f} KB")
            except Exception:
                print(f"{fp.relative_to(Path.cwd())} - size unavailable")

    return 0


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(argv or sys.argv[1:])
    args = parse_args(argv)

    level = logging.DEBUG if getattr(args, "debug", False) else DEFAULT_LOG_LEVEL
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
