"""
07_resample_hourly.py
=====================
Layer 2 EDA: Resample all EnFa signals from ~20-second to hourly resolution.

Reads each signal CSV directly via DuckDB (no full dataset in memory), applies
the correct aggregation per signal type, then assembles a single wide-format
Parquet file — one UTC hour per row, one column per signal.

Aggregation rules (from plan.md):
  mean   — power (kW), temperature (°C), SOC (%), voltage, current, weather
  delta  — cumulative energy/gas counters (MAX - MIN per hour)
  sum    — defrost duration in seconds (total defrost time per hour)
  last   — setpoints / control parameters (event-driven writes, then ffill)

WARNING: DO NOT use sum/mean on cumulative energy counters such as greal_E_WP.
These are ever-increasing totals. Delta (MAX - MIN) gives energy in that hour.

Usage
-----
    python scripts/07_resample_hourly.py
    python scripts/07_resample_hourly.py --raw-dir "C:\\path\\to\\data" --threads 6

Outputs
-------
    data/processed/hourly.parquet   — wide-format, UTC index, ~200 MB compressed
    reports/resample_log.csv        — per-signal aggregation type and row count
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from dataclasses import dataclass, asdict, fields as dc_fields
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from tqdm import tqdm

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Excluded stems — never resampled
# ---------------------------------------------------------------------------

EXCLUDE_STEMS: frozenset[str] = frozenset({"A", "_value", "pilot"})
SNAPSHOT_ROW_THRESHOLD = 20

# ---------------------------------------------------------------------------
# Aggregation type resolution
# ---------------------------------------------------------------------------

# Setpoint categories — these need last-value + forward-fill after resampling
_SETPOINT_CATEGORIES: frozenset[str] = frozenset({
    "hp_setpoint", "hvac_setpoint", "night_setback", "dhw_setpoint",
    "battery_setpoint", "storage_setpoint", "heating_curve",
    "control_param", "timer_schedule",
})


def resolve_aggregation(category: str, signal_name: str) -> str:
    """
    Map a signal's category to its aggregation type.

    Returns one of: 'mean' | 'delta' | 'sum' | 'last' | 'skip'
    """
    cat = category.lower().strip()

    if cat in ("exclude", "unknown") and signal_name in EXCLUDE_STEMS:
        return "skip"

    # Cumulative energy/gas/volume counters → delta
    if any(k in cat for k in ("energy", "gas", "volume", "counter", "pulse", "dint")):
        return "delta"
    if signal_name.startswith("dint"):
        return "delta"

    # Defrost duration (seconds) → sum
    if "defrost" in cat or "abtau" in cat:
        return "sum"
    if "abtau" in signal_name.lower():
        return "sum"

    # Setpoints and control parameters → last (+ ffill applied after)
    if cat in _SETPOINT_CATEGORIES:
        return "last"
    if any(k in cat for k in ("setpoint", "setback", "curve", "schedule", "timer", "param")):
        return "last"

    # Everything else: power, temperature, SOC, voltage, current, weather → mean
    return "mean"


# ---------------------------------------------------------------------------
# DuckDB aggregation SQL templates
# ---------------------------------------------------------------------------

_BASE_CSV = """
    read_csv(
        {path!r},
        delim=';', header=true, ignore_errors=true
    )
"""

_AGG_SQL: dict[str, str] = {
    "mean": """
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
            AVG(TRY_CAST(_value AS DOUBLE))                     AS value
        FROM {csv}
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """,
    "delta": """
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
            GREATEST(MAX(TRY_CAST(_value AS DOUBLE))
                     - MIN(TRY_CAST(_value AS DOUBLE)), 0.0)    AS value
        FROM {csv}
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """,
    "sum": """
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
            SUM(TRY_CAST(_value AS DOUBLE))                     AS value
        FROM {csv}
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """,
    "last": """
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ))           AS hour_utc,
            ARG_MAX(TRY_CAST(_value AS DOUBLE), TRY_CAST(_time AS TIMESTAMPTZ)) AS value
        FROM {csv}
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    """,
}


# ---------------------------------------------------------------------------
# Log model
# ---------------------------------------------------------------------------

@dataclass
class ResampleLog:
    signal_name: str
    category:    str
    agg_type:    str
    rows_in:     int
    rows_out:    int
    notes:       str

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in dc_fields(cls)]

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Classification loader
# ---------------------------------------------------------------------------

def load_signal_map(reports_dir: Path) -> dict[str, str]:
    """Return {stem → category} from signal_classification.csv."""
    path = reports_dir / "signal_classification.csv"
    if not path.exists():
        logger.warning("signal_classification.csv not found — defaulting all to 'unknown'")
        return {}
    mapping: dict[str, str] = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            stem = row.get("signal_name", "").strip()
            cat  = row.get("category", "").strip()
            excl = row.get("exclude", "").strip().lower()
            if stem:
                mapping[stem] = "EXCLUDE" if excl == "true" else cat
    return mapping


# ---------------------------------------------------------------------------
# Core resample function
# ---------------------------------------------------------------------------

def resample_signal(
    con: duckdb.DuckDBPyConnection,
    csv_path: Path,
    agg_type: str,
) -> pd.Series | None:
    """
    Resample one signal to hourly resolution.

    Returns a pd.Series with DatetimeTZDtype (UTC) index and signal name,
    or None if the file is empty / unreadable.
    """
    path_str = csv_path.as_posix()
    csv_frag = _BASE_CSV.format(path=path_str)
    sql      = _AGG_SQL[agg_type].format(csv=csv_frag)

    try:
        df = con.execute(sql).df()
    except Exception as exc:
        logger.debug("DuckDB failed for %s: %s", csv_path.name, exc)
        return None

    if df.empty:
        return None

    df["hour_utc"] = pd.to_datetime(df["hour_utc"], utc=True)
    series = df.set_index("hour_utc")["value"].rename(csv_path.stem)
    return series


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Resample all EnFa signals from ~20s to hourly Parquet.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--raw-dir",      default=None,
                   help="Path to raw CSV directory")
    p.add_argument("--project-root", default=None)
    p.add_argument("--threads",      type=int, default=4,
                   help="DuckDB worker threads")
    p.add_argument("--output",       default=None,
                   help="Output Parquet path (default: data/processed/hourly.parquet)")
    return p


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args  = build_arg_parser().parse_args()
    cfg   = load_config()
    paths = resolve_paths(
        raw_dir=Path(args.raw_dir) if args.raw_dir else None,
        project_root=Path(args.project_root) if args.project_root else None,
        cfg=cfg,
    )
    paths.ensure_output_dirs()

    out_parquet = Path(args.output) if args.output else paths.processed / "hourly.parquet"
    out_parquet.parent.mkdir(parents=True, exist_ok=True)

    category_map = load_signal_map(paths.reports)

    csv_files = sorted(
        f for f in paths.raw_data.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
        and f.stem not in EXCLUDE_STEMS
        and category_map.get(f.stem, "") != "EXCLUDE"
    )
    logger.info("Resampling %d signals → %s", len(csv_files), out_parquet)
    logger.info("DuckDB threads: %d", args.threads)

    con = duckdb.connect()
    con.execute(f"PRAGMA threads={args.threads}")

    # --- Quick row-count filter to skip commissioning snapshots ---
    _count_sql = "SELECT COUNT(*) FROM {csv}"

    series_list: list[pd.Series] = []
    log_rows:    list[ResampleLog] = []
    setpoint_cols: list[str] = []

    t0 = time.time()

    for csv_path in tqdm(csv_files, desc="Resampling", unit="file"):
        stem     = csv_path.stem
        cat      = category_map.get(stem, "unknown")
        agg_type = resolve_aggregation(cat, stem)

        if agg_type == "skip":
            log_rows.append(ResampleLog(stem, cat, "skip", 0, 0, "excluded"))
            continue

        # Skip commissioning snapshots (< threshold rows)
        try:
            csv_frag  = _BASE_CSV.format(path=csv_path.as_posix())
            count_row = con.execute(_count_sql.format(csv=csv_frag)).fetchone()
            rows_in   = int(count_row[0]) if count_row else 0
        except Exception:
            rows_in = 0

        if rows_in < SNAPSHOT_ROW_THRESHOLD:
            log_rows.append(ResampleLog(stem, cat, agg_type, rows_in, 0,
                                        f"snapshot_skipped ({rows_in} rows)"))
            continue

        series = resample_signal(con, csv_path, agg_type)

        if series is None or series.empty:
            log_rows.append(ResampleLog(stem, cat, agg_type, rows_in, 0, "no data after resample"))
            continue

        series_list.append(series)
        if agg_type == "last":
            setpoint_cols.append(stem)

        log_rows.append(ResampleLog(stem, cat, agg_type, rows_in, len(series), "ok"))

    con.close()

    if not series_list:
        logger.error("No data collected — nothing to write.")
        return

    # --- Assemble wide DataFrame ---
    logger.info("Assembling wide DataFrame from %d signals...", len(series_list))
    wide = pd.concat(series_list, axis=1)
    wide.index = pd.DatetimeIndex(wide.index, name="hour_utc")
    wide.sort_index(inplace=True)

    # Forward-fill setpoint columns (event-driven — only write on change)
    if setpoint_cols:
        cols_present = [c for c in setpoint_cols if c in wide.columns]
        wide[cols_present] = wide[cols_present].ffill()
        logger.info("Forward-filled %d setpoint columns", len(cols_present))

    # --- Save as Parquet ---
    table = pa.Table.from_pandas(wide, preserve_index=True)
    pq.write_table(table, out_parquet, compression="snappy")

    elapsed  = time.time() - t0
    ok_count = sum(1 for r in log_rows if r.notes == "ok")
    skip_count = sum(1 for r in log_rows if r.notes != "ok")

    # --- Write resample log ---
    log_path = paths.reports / "resample_log.csv"
    with open(log_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=ResampleLog.field_names())
        writer.writeheader()
        writer.writerows(r.to_dict() for r in log_rows)

    print(f"\n{'='*60}")
    print(f"Signals resampled:  {ok_count}")
    print(f"Signals skipped:    {skip_count}")
    print(f"Wide DataFrame:     {wide.shape[0]:,} rows × {wide.shape[1]} columns")
    print(f"Time range:         {wide.index.min()} -> {wide.index.max()}")
    print(f"Parquet size:       {out_parquet.stat().st_size / 1e6:.1f} MB")
    print(f"Elapsed:            {elapsed/60:.1f} min")
    print(f"Parquet output:     {out_parquet}")
    print(f"Log output:         {log_path}")

    # Aggregation type breakdown
    from collections import Counter
    agg_counts = Counter(r.agg_type for r in log_rows if r.notes == "ok")
    print("\nAggregation types used:")
    for agg, cnt in sorted(agg_counts.items()):
        print(f"  {agg:<8}  {cnt} signals")

    logger.info("Resampling complete. Output: %s", out_parquet)


if __name__ == "__main__":
    main()
