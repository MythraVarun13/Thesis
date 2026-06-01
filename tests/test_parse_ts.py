"""
tests/test_parse_ts.py
======================
Unit tests for zoro_eda.csv_io.parse_timestamp.

These cover the timestamp formats that appear in the EnFa InfluxDB export.
No file I/O — pure function tests that run in milliseconds.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from zoro_eda.csv_io import parse_timestamp


def test_z_suffix_utc():
    """Standard InfluxDB format: ISO 8601 with Z suffix."""
    result = parse_timestamp("2022-12-07T14:11:41Z")
    assert result is not None
    assert result.year == 2022
    assert result.month == 12
    assert result.day == 7
    assert result.hour == 14
    assert result.minute == 11
    assert result.second == 41
    assert result.tzinfo is not None


def test_fractional_seconds_milliseconds():
    """InfluxDB sometimes emits millisecond precision."""
    result = parse_timestamp("2022-12-22T12:24:22.777Z")
    assert result is not None
    assert result.year == 2022
    assert result.second == 22


def test_fractional_seconds_microseconds():
    """Some signals use microsecond precision."""
    result = parse_timestamp("2026-05-27T07:03:18.429000+00:00")
    assert result is not None
    assert result.year == 2026
    assert result.month == 5


def test_plus_offset_format():
    """Timestamps may appear with explicit +00:00 offset instead of Z."""
    result = parse_timestamp("2024-02-27T09:12:41+00:00")
    assert result is not None
    assert result.year == 2024


def test_empty_string_returns_none():
    result = parse_timestamp("")
    assert result is None


def test_whitespace_only_returns_none():
    result = parse_timestamp("   ")
    assert result is None


def test_bad_value_returns_none():
    """Garbage input must return None, not raise."""
    result = parse_timestamp("not-a-timestamp")
    assert result is None


def test_none_like_input_returns_none():
    """Ensure None-ish strings don't raise."""
    result = parse_timestamp("null")
    assert result is None


def test_utc_timezone_attached():
    """Parsed timestamp must be timezone-aware."""
    result = parse_timestamp("2023-06-15T10:30:00Z")
    assert result is not None
    assert result.tzinfo is not None
    assert result.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
