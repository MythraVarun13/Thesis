"""
06_signal_profiles.py
=====================
Layer 1 EDA: Full-data signal quality profiling using DuckDB.

For every non-excluded CSV signal, computes over the complete raw data:
  - Row count, null count, zero-value percentage
  - Min, max, mean, std
  - 5th / 25th / 50th / 75th / 95th percentiles
  - Outlier count (values beyond mean ± 3σ)
  - Time coverage: start, end, duration days
  - Gap ratio: estimated fraction of missing readings (0 = complete, 1 = empty)

DuckDB reads each CSV directly from disk — 40 GB never loads into Python memory.
Expected runtime: 60–120 minutes over the full 233-file dataset.

Usage
-----
    python scripts/06_signal_profiles.py
    python scripts/06_signal_profiles.py --raw-dir "C:\\path\\to\\data" --threads 6

Outputs
-------
    reports/signal_quality_profiles.csv   — one row per signal
"""
from __future__ import annotations

import argparse
import csv
import logging
import sys
import time
from dataclasses import asdict, dataclass, fields as dc_fields
from pathlib import Path

import duckdb
from tqdm import tqdm

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Hard-excluded artifact files (by stem)
EXCLUDE_STEMS: frozenset[str] = frozenset({"A", "_value", "pilot"})

# Files with fewer rows than this are commissioning snapshots — skip
SNAPSHOT_ROW_THRESHOLD = 20

# Assumed dominant sampling interval in seconds (for gap estimation)
DEFAULT_INTERVAL_S = 20


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SignalProfile:
    file_name:      str
    signal_name:    str
    category:       str
    row_count:      int
    null_count:     int
    zero_pct:       float
    val_min:        float
    val_max:        float
    val_mean:       float
    val_std:        float
    p05:            float
    p25:            float
    p50:            float
    p75:            float
    p95:            float
    outlier_count:  int
    start_time:     str
    end_time:       str
    duration_days:  float
    expected_rows:  int
    gap_ratio:      float
    notes:          str   # "ok", "snapshot_skipped", or error message

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in dc_fields(cls)]

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def _empty(cls, file_name: str, signal_name: str, notes: str) -> "SignalProfile":
        return cls(
            file_name=file_name, signal_name=signal_name, category="",
            row_count=0, null_count=0, zero_pct=0.0,
            val_min=0.0, val_max=0.0, val_mean=0.0, val_std=0.0,
            p05=0.0, p25=0.0, p50=0.0, p75=0.0, p95=0.0,
            outlier_count=0, start_time="", end_time="",
            duration_days=0.0, expected_rows=0, gap_ratio=0.0,
            notes=notes,
        )


# ---------------------------------------------------------------------------
# Classification loader
# ---------------------------------------------------------------------------

def load_category_map(reports_dir: Path) -> dict[str, str]:
    """Return {signal_stem → category} from signal_classification.csv."""
    path = reports_dir / "signal_classification.csv"
    if not path.exists():
        logger.warning("signal_classification.csv not found — categories will be empty")
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
# DuckDB queries
# ---------------------------------------------------------------------------

_STATS_SQL = """
SELECT
    COUNT(*)                                                             AS row_count,
    COUNT(*) - COUNT(TRY_CAST(_value AS DOUBLE))                        AS null_count,
    ROUND(100.0 * SUM(CASE WHEN TRY_CAST(_value AS DOUBLE) = 0.0
                           THEN 1 ELSE 0 END)
          / NULLIF(COUNT(TRY_CAST(_value AS DOUBLE)), 0), 2)            AS zero_pct,
    MIN(TRY_CAST(_value AS DOUBLE))                                      AS val_min,
    MAX(TRY_CAST(_value AS DOUBLE))                                      AS val_max,
    AVG(TRY_CAST(_value AS DOUBLE))                                      AS val_mean,
    STDDEV_SAMP(TRY_CAST(_value AS DOUBLE))                              AS val_std,
    APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.05)                    AS p05,
    APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.25)                    AS p25,
    APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.50)                    AS p50,
    APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.75)                    AS p75,
    APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.95)                    AS p95,
    MIN(TRY_CAST(_time AS TIMESTAMPTZ))                                  AS start_time,
    MAX(TRY_CAST(_time AS TIMESTAMPTZ))                                  AS end_time,
FROM read_csv(
    {path!r},
    delim=';', header=true, ignore_errors=true
)
WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
"""

_OUTLIER_SQL = """
SELECT COUNT(*) AS outlier_count
FROM read_csv(
    {path!r},
    delim=';', header=true, ignore_errors=true
)
WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
  AND ABS(TRY_CAST(_value AS DOUBLE) - {mean}) > 3.0 * {std}
"""


def _f(val, default: float = 0.0) -> float:
    try:
        return float(val) if val is not None else default
    except (TypeError, ValueError):
        return default


def profile_one(
    con: duckdb.DuckDBPyConnection,
    csv_path: Path,
    category: str,
) -> SignalProfile:
    """Profile a single CSV file using DuckDB."""
    stem     = csv_path.stem
    path_str = csv_path.as_posix()

    # --- Main stats query ---
    try:
        row = con.execute(_STATS_SQL.format(path=path_str)).fetchone()
    except Exception as exc:
        return SignalProfile._empty(csv_path.name, stem, f"stats query failed: {exc}")

    if row is None:
        return SignalProfile._empty(csv_path.name, stem, "no rows returned")

    (row_count, null_count, zero_pct,
     val_min, val_max, val_mean, val_std,
     p05, p25, p50, p75, p95,
     start_time, end_time) = row

    row_count  = int(row_count  or 0)
    null_count = int(null_count or 0)

    # Skip commissioning snapshots
    if row_count < SNAPSHOT_ROW_THRESHOLD:
        return SignalProfile._empty(csv_path.name, stem,
                                    f"snapshot_skipped ({row_count} rows)")

    # --- Outlier count ---
    outlier_count = 0
    mean_f = _f(val_mean)
    std_f  = _f(val_std)
    if std_f > 0:
        try:
            out = con.execute(
                _OUTLIER_SQL.format(path=path_str, mean=mean_f, std=std_f)
            ).fetchone()
            outlier_count = int(out[0]) if out else 0
        except Exception:
            pass

    # --- Time coverage and gap estimate ---
    start_str     = str(start_time) if start_time else ""
    end_str       = str(end_time)   if end_time   else ""
    duration_days = 0.0
    expected_rows = 0
    gap_ratio     = 0.0

    if start_time and end_time:
        try:
            delta         = end_time - start_time
            duration_days = delta.total_seconds() / 86400
            expected_rows = int(duration_days * 86400 / DEFAULT_INTERVAL_S)
            if expected_rows > 0:
                gap_ratio = round(max(0.0, 1.0 - row_count / expected_rows), 4)
        except Exception:
            pass

    return SignalProfile(
        file_name=csv_path.name,
        signal_name=stem,
        category=category,
        row_count=row_count,
        null_count=null_count,
        zero_pct=_f(zero_pct),
        val_min=round(_f(val_min), 4),
        val_max=round(_f(val_max), 4),
        val_mean=round(mean_f, 6),
        val_std=round(std_f, 6),
        p05=round(_f(p05), 4),
        p25=round(_f(p25), 4),
        p50=round(_f(p50), 4),
        p75=round(_f(p75), 4),
        p95=round(_f(p95), 4),
        outlier_count=outlier_count,
        start_time=start_str,
        end_time=end_str,
        duration_days=round(duration_days, 2),
        expected_rows=expected_rows,
        gap_ratio=gap_ratio,
        notes="ok",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Full-data signal quality profiling via DuckDB.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--raw-dir",      default=None,
                   help="Path to raw CSV directory (overrides config)")
    p.add_argument("--project-root", default=None)
    p.add_argument("--threads",      type=int, default=4,
                   help="DuckDB worker threads")
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

    category_map = load_category_map(paths.reports)

    csv_files = sorted(
        f for f in paths.raw_data.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
        and f.stem not in EXCLUDE_STEMS
        and category_map.get(f.stem, "") != "EXCLUDE"
    )
    logger.info("Profiling %d CSV files  |  DuckDB threads: %d", len(csv_files), args.threads)

    con = duckdb.connect()
    con.execute(f"PRAGMA threads={args.threads}")

    profiles: list[SignalProfile] = []
    t0 = time.time()

    for csv_path in tqdm(csv_files, desc="Signal profiles", unit="file"):
        cat = category_map.get(csv_path.stem, "unknown")
        profiles.append(profile_one(con, csv_path, cat))

    con.close()

    # --- Write output ---
    out_path = paths.reports / "signal_quality_profiles.csv"
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SignalProfile.field_names())
        writer.writeheader()
        writer.writerows(p.to_dict() for p in profiles)

    elapsed   = time.time() - t0
    ok        = [p for p in profiles if p.notes == "ok"]
    snapshots = [p for p in profiles if "snapshot_skipped" in p.notes]
    errors    = [p for p in profiles if p.notes not in ("ok",) and "snapshot_skipped" not in p.notes]
    high_gap  = sorted([p for p in ok if p.gap_ratio > 0.10], key=lambda x: -x.gap_ratio)

    print(f"\n{'='*60}")
    print(f"Profiled:   {len(ok)} signals successfully")
    print(f"Snapshots:  {len(snapshots)} commissioning files skipped")
    print(f"Errors:     {len(errors)} failed")
    print(f"Elapsed:    {elapsed/60:.1f} min")
    print(f"Output:     {out_path}")

    if high_gap:
        print(f"\nSignals with >10% estimated data gap ({len(high_gap)}):")
        for p in high_gap[:15]:
            print(f"  {p.signal_name:<45}  gap={p.gap_ratio:.1%}  rows={p.row_count:,}")

    if errors:
        print(f"\nErrors ({len(errors)}):")
        for p in errors[:10]:
            print(f"  {p.file_name}: {p.notes}")

    logger.info("Done. Output: %s", out_path)


if __name__ == "__main__":
    main()
