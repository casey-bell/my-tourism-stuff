from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional, Union

import pandas as pd


PathLike = Union[str, Path]


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Search upward for project root.

    Looks for 'pyproject.toml' or a '.git' directory. If none is
    found the starting directory is returned.
    """
    current = (start or Path(__file__).resolve()).parent
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").is_dir():
            return parent
    return current


def as_path(path: PathLike, base: Optional[Path] = None) -> Path:
    """
    Convert a path-like to a resolved Path.

    Relative paths are resolved against the provided base or the
    detected project root.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    root = base or find_project_root()
    return (root / p).resolve()


def ensure_parent_dir(path: PathLike) -> Path:
    """
    Ensure the parent directory for `path` exists.

    Returns the resolved Path for the target.
    """
    p = as_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _check_overwrite(path: Path, overwrite: bool) -> None:
    """
    Raise FileExistsError if path exists and overwrite is False.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(
            f"File exists and overwrite is disabled: {path}"
        )


def read_parquet(
    path: PathLike,
    columns: Optional[Iterable[str]] = None,
    engine: str = "pyarrow",
) -> pd.DataFrame:
    """Read a Parquet file into a DataFrame."""
    p = as_path(path)
    return pd.read_parquet(p, columns=columns, engine=engine)


def write_parquet(
    df: pd.DataFrame,
    path: PathLike,
    compression: Optional[str] = "snappy",
    index: bool = False,
    overwrite: bool = True,
    engine: str = "pyarrow",
) -> Path:
    """Write a DataFrame to Parquet and return the written path."""
    p = ensure_parent_dir(path)
    _check_overwrite(p, overwrite)
    df.to_parquet(p, compression=compression, index=index, engine=engine)
    return p


def read_csv(
    path: PathLike,
    dtype: Optional[dict] = None,
    parse_dates: Optional[Union[list, dict]] = None,
) -> pd.DataFrame:
    """Read a CSV file into a DataFrame."""
    p = as_path(path)
    return pd.read_csv(p, dtype=dtype, parse_dates=parse_dates)


def write_csv(
    df: pd.DataFrame,
    path: PathLike,
    index: bool = False,
    overwrite: bool = True,
    **kwargs: Any,
) -> Path:
    """Write a DataFrame to CSV and return the written path."""
    p = ensure_parent_dir(path)
    _check_overwrite(p, overwrite)
    df.to_csv(p, index=index, **kwargs)
    return p


def read_excel(
    path: PathLike,
    sheet_name: Optional[Union[str, int]] = None,
    dtype: Optional[dict] = None,
    header: Union[int, list[int]] = 0,
    engine: Optional[str] = None,
) -> pd.DataFrame:
    """Read an Excel sheet into a DataFrame."""
    p = as_path(path)
    return pd.read_excel(
        p, sheet_name=sheet_name, dtype=dtype, header=header, engine=engine
    )


def read_json(path: PathLike, encoding: str = "utf-8") -> Any:
    """Read and parse a JSON file."""
    p = as_path(path)
    with p.open("r", encoding=encoding) as f:
        return json.load(f)


def write_json(
    obj: Any,
    path: PathLike,
    encoding: str = "utf-8",
    overwrite: bool = True,
    indent: int = 2,
) -> Path:
    """Write an object to JSON and return the written path."""
    p = ensure_parent_dir(path)
    _check_overwrite(p, overwrite)
    with p.open("w", encoding=encoding) as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)
    return p


def exists(path: PathLike) -> bool:
    """Return True if path exists."""
    return as_path(path).exists()


def ensure_dir(path: PathLike) -> Path:
    """Ensure a directory exists and return it."""
    p = as_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
