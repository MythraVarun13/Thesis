"""
zoro_eda.csv_io
===============
Shared I/O helpers for InfluxDB-style semicolon-delimited CSV files.

All functions are designed to work on large files (40+ GB) without loading
the full file into memory. They read only the head or tail as needed.

Key facts about the EnFa dataset format
----------------------------------------
- Delimiter  : semicolon (;)
- Encoding   : UTF-8
- Columns    : Unnamed:0 | _time | _value | _field | _measurement
- Timestamps : ISO 8601 UTC  (e.g. "2022-12-07T14:11:41Z")
- _field     : always "value" — single-field measurements
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Sampling constants (override via config.yaml)
DEFAULT_HEAD_BYTES  = 6_144   # 6 KB — enough for header + ~20 rows
DEFAULT_TAIL_BYTES  = 4_096   # 4 KB — enough for last few timestamps
DEFAULT_HEAD_ROWS   = 30
CANDIDATE_DELIMITERS = [";", ",", "\t", "|"]

# Seconds in a day — used to filter out cross-day gaps in head samples
SECONDS_PER_DAY = 86_400


# ---------------------------------------------------------------------------
# Timestamp parsing
# ---------------------------------------------------------------------------

def parse_timestamp(raw: str) -> datetime | None:
    """Parse an ISO 8601 UTC timestamp string to a timezone-aware datetime.

    Handles both ``Z`` suffix and ``+00:00`` offset.
    Returns ``None`` on any parse failure rather than raising.

    Examples
    --------
    >>> parse_timestamp("2022-12-07T14:11:41Z")
    datetime.datetime(2022, 12, 7, 14, 11, 41, tzinfo=datetime.timezone.utc)
    >>> parse_timestamp("bad-value") is None
    True
    """
    if not raw or not raw.strip():
        return None
    try:
        normalised = raw.strip().replace("Z", "+00:00")
        return datetime.fromisoformat(normalised)
    except ValueError:
        pass
    try:
        # Fallback: strip sub-seconds and try again
        base = raw.strip().split(".")[0].rstrip("Z")
        return datetime.fromisoformat(base).replace(tzinfo=timezone.utc)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# Delimiter / encoding detection
# ---------------------------------------------------------------------------

def detect_encoding(raw_bytes: bytes) -> str:
    """Return the most likely text encoding for a byte sample.

    Tries UTF-8 first (BOM-aware), then Latin-1 as a universal fallback.
    """
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            raw_bytes.decode(enc)
            return enc
        except UnicodeDecodeError:
            continue
    return "latin-1"


def detect_delimiter(raw_bytes: bytes, candidates: list[str] | None = None) -> tuple[str, list[str]]:
    """Detect the field delimiter and return (delimiter, header_columns).

    Tries each candidate delimiter on the first line and picks the one that
    produces the most columns.

    Parameters
    ----------
    raw_bytes:
        First N bytes of the file (6 KB is sufficient).
    candidates:
        Delimiters to try, in preference order. Defaults to
        ``[";", ",", "\\t", "|"]``.

    Returns
    -------
    (delimiter, column_names)
    """
    if candidates is None:
        candidates = CANDIDATE_DELIMITERS

    encoding = detect_encoding(raw_bytes)
    text = raw_bytes.decode(encoding, errors="replace")

    best_delimiter = ";"
    best_columns: list[str] = []

    for delimiter in candidates:
        try:
            reader = csv.reader(io.StringIO(text), delimiter=delimiter)
            first_row = next(reader, [])
            if len(first_row) > len(best_columns):
                best_columns = first_row
                best_delimiter = delimiter
        except Exception as exc:
            logger.debug("Delimiter %r failed: %s", delimiter, exc)

    return best_delimiter, best_columns


# ---------------------------------------------------------------------------
# Column index helpers
# ---------------------------------------------------------------------------

def find_column(header: list[str], column_name: str) -> int:
    """Return the index of the first header entry containing ``column_name``.

    Case-insensitive. Returns ``-1`` if not found.

    Examples
    --------
    >>> find_column(["Unnamed: 0", "_time", "_value"], "_time")
    1
    """
    name_lower = column_name.lower()
    for idx, col in enumerate(header):
        if name_lower in col.lower():
            return idx
    return -1


# ---------------------------------------------------------------------------
# Head / tail reads
# ---------------------------------------------------------------------------

def read_head(
    fpath: Path,
    n_rows: int = DEFAULT_HEAD_ROWS,
    head_bytes: int = DEFAULT_HEAD_BYTES,
) -> tuple[list[str], list[list[str]]]:
    """Read the first ``n_rows`` data rows (not counting the header).

    Returns ``(header, data_rows)``.  Both are empty lists on failure.
    Reads at most ``head_bytes`` to avoid loading large files.
    """
    header: list[str] = []
    data_rows: list[list[str]] = []

    try:
        with open(fpath, "rb") as fh:
            raw = fh.read(head_bytes)
    except OSError as exc:
        logger.warning("Cannot read %s: %s", fpath, exc)
        return header, data_rows

    encoding = detect_encoding(raw)
    delimiter, _ = detect_delimiter(raw)
    text = raw.decode(encoding, errors="replace")

    try:
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        for row_idx, row in enumerate(reader):
            if row_idx == 0:
                header = row
            else:
                data_rows.append(row)
                if len(data_rows) >= n_rows:
                    break
    except csv.Error as exc:
        logger.warning("CSV parse error in %s: %s", fpath, exc)

    return header, data_rows


def read_tail_lines(fpath: Path, tail_bytes: int = DEFAULT_TAIL_BYTES) -> list[str]:
    """Return the non-empty lines from the last ``tail_bytes`` of the file.

    Used to extract the final timestamp without reading the whole file.
    The first line is discarded because it may be a partial line.
    """
    try:
        file_size = fpath.stat().st_size
        seek_position = max(0, file_size - tail_bytes)
        with open(fpath, "rb") as fh:
            fh.seek(seek_position)
            raw = fh.read()
        encoding = detect_encoding(raw)
        text = raw.decode(encoding, errors="replace")
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return lines[1:]  # skip first (possibly partial) line
    except OSError as exc:
        logger.warning("Cannot read tail of %s: %s", fpath, exc)
        return []


def get_last_timestamp(fpath: Path, delimiter: str = ";", tail_bytes: int = DEFAULT_TAIL_BYTES) -> datetime | None:
    """Return the last valid timestamp from a file's tail without a full read.

    Finds the timestamp column by reading the file header first, then
    applies the same column index to tail lines — robust to column reordering.
    """
    # Get time column index from head
    header, _ = read_head(fpath, n_rows=1)
    time_idx = find_column(header, "_time")
    if time_idx == -1:
        time_idx = 1  # safe default for standard InfluxDB format

    for line in reversed(read_tail_lines(fpath, tail_bytes)):
        parts = line.split(delimiter)
        if time_idx < len(parts):
            dt = parse_timestamp(parts[time_idx])
            if dt is not None:
                return dt
    return None


def estimate_row_count(fpath: Path, head_bytes: int = 65_536) -> int:
    """Estimate total row count from file size and average row byte length.

    Reads the first ``head_bytes`` to compute average row size, then
    extrapolates to the full file size.  Returns ``-1`` on failure.
    """
    try:
        file_size = fpath.stat().st_size
        with open(fpath, "rb") as fh:
            sample = fh.read(head_bytes)
        newlines = sample.count(b"\n")
        if newlines < 2:
            return -1
        avg_row_bytes = len(sample) / newlines
        # Subtract 1 for the header row
        return max(int(file_size / avg_row_bytes) - 1, 0)
    except OSError as exc:
        logger.warning("Cannot estimate rows for %s: %s", fpath, exc)
        return -1
