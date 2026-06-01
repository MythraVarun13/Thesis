"""
tests/test_delimiter_detection.py
==================================
Unit tests for zoro_eda.csv_io.detect_delimiter.

Uses synthetic byte buffers — no file I/O required.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from zoro_eda.csv_io import detect_delimiter, detect_encoding


# ---------------------------------------------------------------------------
# Delimiter detection
# ---------------------------------------------------------------------------

def _make_csv_bytes(delimiter: str, rows: int = 5) -> bytes:
    """Build a minimal synthetic CSV with the given delimiter."""
    header = delimiter.join(["Unnamed: 0", "_time", "_value", "_field", "_measurement"])
    data_row = delimiter.join(["", "2022-12-07T14:11:41Z", "42.0", "value", "test_signal"])
    lines = [header] + [data_row] * rows
    return "\n".join(lines).encode("utf-8")


def test_detects_semicolon():
    """EnFa InfluxDB export uses semicolons."""
    raw = _make_csv_bytes(";")
    delim, columns = detect_delimiter(raw)
    assert delim == ";"
    assert len(columns) == 5


def test_detects_comma():
    raw = _make_csv_bytes(",")
    delim, columns = detect_delimiter(raw)
    assert delim == ","
    assert len(columns) == 5


def test_detects_tab():
    raw = _make_csv_bytes("\t")
    delim, columns = detect_delimiter(raw)
    assert delim == "\t"
    assert len(columns) == 5


def test_returns_most_columns():
    """When ambiguous, should pick the delimiter giving most columns."""
    # Semicolons with 5 columns beats comma interpretation (1 column)
    raw = _make_csv_bytes(";")
    delim, columns = detect_delimiter(raw)
    assert len(columns) >= 5  # semicolon gives more columns than comma here


def test_column_names_preserved():
    """Column names from the header should be returned as-is."""
    raw = _make_csv_bytes(";")
    _, columns = detect_delimiter(raw)
    assert "Unnamed: 0" in columns
    assert "_time" in columns
    assert "_value" in columns
    assert "_measurement" in columns


def test_empty_bytes_returns_default():
    """Empty input should not raise — return default semicolon."""
    delim, columns = detect_delimiter(b"")
    assert delim == ";"
    assert columns == [] or isinstance(columns, list)


# ---------------------------------------------------------------------------
# Encoding detection
# ---------------------------------------------------------------------------

def test_utf8_detected():
    raw = "test content".encode("utf-8")
    assert detect_encoding(raw) == "utf-8"


def test_utf8_with_bom_detected():
    raw = "﻿test".encode("utf-8-sig")
    assert detect_encoding(raw) in ("utf-8", "utf-8-sig")


def test_latin1_fallback():
    """Bytes with invalid UTF-8 sequences should fall through to latin-1."""
    raw = b"\xff\xfe some bytes that are not valid utf-8 \x80\x81"
    encoding = detect_encoding(raw)
    assert encoding == "latin-1"
