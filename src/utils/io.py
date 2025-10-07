from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable, Optional, Union

import pandas as pd


PathLike = Union[str, Path]


def find_project_root(start: Optional[Path] = None) -> Path:
    """
    Locate the project root by searching upwards for 'pyproject.toml' or a '.git' directory.

    Parameters
    ----------
    start : Optional[Path]
        Starting directory. Defaults to the current file's directory.

    Returns
    -------
    Path
        The detected project root directory.
    """
    current = (start or Path(__file__).resolve()).parent
    for parent in [current, *current.parents]:
        if (parent / "pyproject.toml").exists() or (parent / ".git").is_dir():
            return parent
    # Fallback to the starting directory if no markers are found
    return current


def as_path(path: PathLike, base: Optional[Path] = None) -> Path:
    """
    Convert input to a Path. If the path is relative, resolve it against the project root or a provided base.

    Parameters
    ----------
    path : PathLike
        The path-like object to resolve.
    base : Optional[Path]
        Base directory to resolve relative paths against. Defaults to project root.

    Returns
    -------
    Path
        Resolved absolute path.
    """
    p = Path(path)
    if p.is_absolute():
        return p
    root = base or find_project_root()
    return (root / p).resolve()


def ensure_parent_dir(path: PathLike) -> Path:
    """
    Ensure the parent directory of the given path exists.

    Parameters
    ----------
    path : PathLike
        Target file path.

    Returns
    -------
    Path
        The resolved path.
    """
    p = as_path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _check_overwrite(path: Path, overwrite: bool) -> None:
    """
    Raise if the file exists and overwrite is False.

    Parameters
    ----------
    path : Path
        Target file path.
    overwrite : bool
        Whether to allow overwriting existing files.
    """
    if path.exists() and not overwrite:
        raise FileExistsError(f"File already exists and overwrite is disabled: {path}")


def read_parquet(
    path: PathLike,
    columns: Optional[Iterable[str]] = None,
    engine: str = "pyarrow",
) -> pd.DataFrame:
    """
    Read a Parquet file into a DataFrame.

    Parameters
    ----------
    path : PathLike
        Path to the Parquet file.
    columns : Optional[Iterable[str]]
        Subset of columns to read.
    engine : str
        Parquet engine ('pyarrow' or 'fastparquet').

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
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
    """
    Write a DataFrame to Parquet.

    Parameters
    ----------
    df : pd.DataFrame
        Data to write.
    path : PathLike
        Output path.
    compression : Optional[str]
        Compression codec (e.g., 'snappy', 'gzip', None).
    index : bool
        Whether to write the index.
    overwrite : bool
        Allow overwriting existing files.
    engine : str
        Parquet engine ('pyarrow' or 'fastparquet').

    Returns
    -------
    Path
        Path to the written file.
    """
    p = ensure_parent_dir(path)
    _check_overwrite(p, overwrite)
    df.to_parquet(p, compression=compression, index=index, engine=engine)
    return p


def read_csv(
    path: PathLike,
    dtype: Optional[dict] = None,
    parse_dates: Optional[Union[list, dict]] = None,
) -> pd.DataFrame:
    """
    Read a CSV file into a DataFrame.

    Parameters
    ----------
    path : PathLike
        Path to the CSV file.
    dtype : Optional[dict]
        Dtype mapping for columns.
    parse_dates : Optional[Union[list, dict]]
        Columns to parse as dates.

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    p = as_path(path)
    return pd.read_csv(p, dtype=dtype, parse_dates=parse_dates)


def write_csv(
    df: pd.DataFrame,
    path: PathLike,
    index: bool = False,
    overwrite: bool = True,
    **kwargs: Any,
) -> Path:
    """
    Write a DataFrame to CSV.

    Parameters
    ----------
    df : pd.DataFrame
        Data to write.
    path : PathLike
        Output path.
    index : bool
        Whether to write the index.
    overwrite : bool
        Allow overwriting existing files.
    kwargs : Any
        Additional arguments forwarded to pandas.DataFrame.to_csv.

    Returns
    -------
    Path
        Path to the written file.
    """
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
    """
    Read an Excel worksheet into a DataFrame.

    Parameters
    ----------
    path : PathLike
        Path to the Excel file.
    sheet_name : Optional[Union[str, int]]
        Sheet name or index. Defaults to the first sheet.
    dtype : Optional[dict]
        Dtype mapping for columns.
    header : Union[int, list[int]]
        Row(s) to use as the column names.
    engine : Optional[str]
        Excel engine (e.g., 'openpyxl').

    Returns
    -------
    pd.DataFrame
        Loaded DataFrame.
    """
    p = as_path(path)
    return pd.read_excel(p, sheet_name=sheet_name, dtype=dtype, header=header, engine=engine)


def read_json(path: PathLike, encoding: str = "utf-8") -> Any:
    """
    Read a JSON file.

    Parameters
    ----------
    path : PathLike
        Path to the JSON file.
    encoding : str
        File encoding.

    Returns
    -------
    Any
        Parsed JSON content.
    """
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
    """
    Write an object to JSON.

    Parameters
    ----------
    obj : Any
        Object to serialise.
    path : PathLike
        Output path.
    encoding : str
        File encoding.
    overwrite : bool
        Allow overwriting existing files.
    indent : int
        Indentation level for formatting.

    Returns
    -------
    Path
        Path to the written file.
    """
    p = ensure_parent_dir(path)
    _check_overwrite(p, overwrite)
    with p.open("w", encoding=encoding) as f:
        json.dump(obj, f, indent=indent, ensure_ascii=False)
    return p


def exists(path: PathLike) -> bool:
    """
    Check whether a path exists.

    Parameters
    ----------
    path : PathLike
        Path to check.

    Returns
    -------
    bool
        True if the path exists, otherwise False.
    """
    return as_path(path).exists()


def ensure_dir(path: PathLike) -> Path:
    """
    Ensure a directory exists.

    Parameters
    ----------
    path : PathLike
        Directory path.

    Returns
    -------
    Path
        The directory path.
    """
    p = as_path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p
