"""
Utility functions for the my-tourism-stuff project.

Includes performance monitoring, timing, and helper functions.
"""

from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Generator, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


@contextmanager
def timer(
    name: str = "Operation",
    log_level: int = logging.INFO,
) -> Generator[None, None, None]:
    """
    Context manager for timing code blocks.
    
    Example:
        with timer("Data loading"):
            df = load_data()
        # Output: Data loading completed in 1.23s
    """
    start = time.time()
    try:
        yield
    finally:
        elapsed = time.time() - start
        logger.log(log_level, f"{name} completed in {elapsed:.2f}s")


def timed(
    name: Optional[str] = None,
    log_level: int = logging.INFO,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for timing function execution.
    
    Example:
        @timed("Data cleaning")
        def clean_data(df):
            return df.dropna()
        
        # Output: Data cleaning completed in 0.45s
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        func_name = name or func.__name__
        
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:  # type: ignore
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start
                logger.log(
                    log_level,
                    f"{func_name} completed in {elapsed:.2f}s"
                )
        
        return wrapper
    return decorator


def format_bytes(num_bytes: int) -> str:
    """
    Format bytes as human-readable string.
    
    Example:
        >>> format_bytes(1024)
        '1.00 KB'
        >>> format_bytes(1048576)
        '1.00 MB'
    """
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(num_bytes) < 1024.0:
            return f"{num_bytes:.2f} {unit}"
        num_bytes /= 1024.0
    return f"{num_bytes:.2f} PB"


def get_dataframe_memory_usage(df) -> str:  # type: ignore
    """
    Get memory usage of a pandas DataFrame as a human-readable string.
    
    Example:
        >>> import pandas as pd
        >>> df = pd.DataFrame({'a': range(1000)})
        >>> get_dataframe_memory_usage(df)
        '7.91 KB'
    """
    try:
        memory_bytes = df.memory_usage(deep=True).sum()
        return format_bytes(memory_bytes)
    except Exception:
        return "Unknown"


def log_dataframe_info(df, name: str = "DataFrame") -> None:  # type: ignore
    """
    Log useful information about a DataFrame.
    
    Example:
        >>> log_dataframe_info(df, "Cleaned data")
        # Output: Cleaned data: 1000 rows x 5 columns, 7.91 KB
    """
    try:
        rows, cols = df.shape
        memory = get_dataframe_memory_usage(df)
        logger.info(f"{name}: {rows:,} rows x {cols} columns, {memory}")
    except Exception as e:
        logger.warning(f"Could not log info for {name}: {e}")


__all__ = [
    "timer",
    "timed",
    "format_bytes",
    "get_dataframe_memory_usage",
    "log_dataframe_info",
]
