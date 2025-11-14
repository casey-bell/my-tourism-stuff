"""
Tests for utility functions.
"""

import logging
import time

import pandas as pd
import pytest

from src.utils import (
    format_bytes,
    get_dataframe_memory_usage,
    log_dataframe_info,
    timed,
    timer,
)


def test_timer_measures_elapsed_time(caplog):
    """Test that timer context manager measures time."""
    caplog.set_level(logging.INFO)
    with timer("Test operation"):
        time.sleep(0.1)
    
    assert "Test operation completed in" in caplog.text


def test_timed_decorator_measures_function_time(caplog):
    """Test that timed decorator measures function execution time."""
    caplog.set_level(logging.INFO)
    
    @timed("Slow function")
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    result = slow_function()
    
    assert result == "done"
    assert "Slow function completed in" in caplog.text


def test_format_bytes_converts_correctly():
    """Test byte formatting."""
    assert format_bytes(0) == "0.00 B"
    assert format_bytes(1024) == "1.00 KB"
    assert format_bytes(1024 * 1024) == "1.00 MB"
    assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"


def test_get_dataframe_memory_usage():
    """Test DataFrame memory usage calculation."""
    df = pd.DataFrame({"a": range(100), "b": range(100)})
    memory_str = get_dataframe_memory_usage(df)
    
    assert "B" in memory_str or "KB" in memory_str
    assert memory_str != "Unknown"


def test_log_dataframe_info(caplog):
    """Test DataFrame info logging."""
    caplog.set_level(logging.INFO)
    df = pd.DataFrame({"x": range(10), "y": range(10)})
    log_dataframe_info(df, "Test DF")
    
    assert "Test DF" in caplog.text
    assert "10 rows" in caplog.text
    assert "2 columns" in caplog.text
