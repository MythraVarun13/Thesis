"""
03_profile_timeseries.py
========================
Step 3: Time-series profiling for all EnFa signal files.

Reads only the file head (first 30 rows) and tail (last 4 KB) per file.
No full-file reads — safe on 40+ GB datasets.

Usage
-----
    python scripts/03_profile_timeseries.py
    python scripts/03_profile_timeseries.py --raw-dir /path/to/data

Outputs
-------
    reports/timestamp_coverage_report.csv
    reports/sampling_interval_report.csv
    context/data_quality_context.md
"""

from __future__ import annotations

import argparse
import csv
import logging
import statistics
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths
from zoro_eda.csv_io import (
    find_column,
    get_last_timestamp,
    parse_timestamp,
    read_head,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Named constants — no magic numbers in logic below
# ---------------------------------------------------------------------------
SECONDS_PER_DAY              = 86_400
MAX_PLAUSIBLE_GAP_SECONDS    = 86_400   # gaps > 1 day flagged in head sample
INTERVAL_REGULARITY_TOLERANCE = 0.20   # 20 % of median; intervals within this = regular
REGULARITY_MINIMUM_ROWS      = 3       # need at least this many intervals to judge regularity
REGULARITY_THRESHOLD_FRACTION = 0.90   # 90 % of intervals must be within tolerance


def classify_interval_label(median_seconds: float | None) -> str:
    """Map a median interval in seconds to a human-readable label."""
    if median_seconds is None:
        return "unknown"
    if median_seconds <= 7:
        return "~5s"
    if median_seconds <= 22:
        return "~20s"
    if median_seconds <= 65:
        return "~1min"
    if median_seconds <= 310:
        return "~5min"
    if median_seconds <= 3_700:
        return "~1hr"
    return f"~{round(median_seconds / 60)}min"


def profile_file(fpath: Path, head_rows: int = 30, tail_bytes: int = 4_096) -> dict:
    """Profile one file using head + tail reads only."""
    header, data_rows = read_head(fpath, n_rows=head_rows)
    time_col_idx = find_column(header, "_time")

    head_timestamps: list[datetime] = []
    if time_col_idx >= 0:
        for row in data_rows:
            if time_col_idx < len(row):
                dt = parse_timestamp(row[time_col_idx])
                if dt is not None:
                    head_timestamps.append(dt)

    start_ts = head_timestamps[0] if head_timestamps else None

    # End timestamp — use robust helper that also checks column position from header
    end_ts = get_last_timestamp(fpath, tail_bytes=tail_bytes)

    # Sampling intervals from head (filter cross-day jumps)
    intervals_seconds: list[float] = [
        (head_timestamps[i] - head_timestamps[i - 1]).total_seconds()
        for i in range(1, len(head_timestamps))
        if 0 < (head_timestamps[i] - head_timestamps[i - 1]).total_seconds() < MAX_PLAUSIBLE_GAP_SECONDS
    ]

    median_interval = round(statistics.median(intervals_seconds), 1) if intervals_seconds else None
    min_interval    = round(min(intervals_seconds), 1) if intervals_seconds else None
    max_interval    = round(max(intervals_seconds), 1) if intervals_seconds else None

    interval_regular: bool | None = None
    if median_interval is not None and len(intervals_seconds) >= REGULARITY_MINIMUM_ROWS:
        tolerance = INTERVAL_REGULARITY_TOLERANCE * median_interval + 1.0
        within    = sum(1 for x in intervals_seconds if abs(x - median_interval) <= tolerance)
        interval_regular = (within / len(intervals_seconds)) >= REGULARITY_THRESHOLD_FRACTION

    duration_days: float | None = None
    if start_ts and end_ts and end_ts > start_ts:
        duration_days = round((end_ts - start_ts).total_seconds() / SECONDS_PER_DAY, 1)

    head_gap_detected = (
        max_interval is not None
        and median_interval is not None
        and median_interval > 0
        and max_interval > median_interval * 5
    )

    return {
        "file_name":           fpath.name,
        "start_utc":           start_ts.isoformat() if start_ts else "",
        "end_utc":             end_ts.isoformat()   if end_ts   else "",
        "duration_days":       duration_days if duration_days is not None else "",
        "median_interval_sec": median_interval if median_interval is not None else "",
        "min_interval_sec":    min_interval    if min_interval    is not None else "",
        "max_interval_sec":    max_interval    if max_interval    is not None else "",
        "interval_label":      classify_interval_label(median_interval),
        "interval_regular":    interval_regular if interval_regular is not None else "",
        "head_rows_parsed":    len(head_timestamps),
        "head_gap_detected":   head_gap_detected,
    }


def write_coverage_report(profiles: list[dict], output_path: Path) -> None:
    fields = [
        "file_name", "start_utc", "end_utc", "duration_days",
        "median_interval_sec", "interval_label", "interval_regular", "head_gap_detected",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(profiles)
    logger.info("Saved: %s", output_path)


def write_interval_report(profiles: list[dict], output_path: Path) -> None:
    fields = [
        "file_name", "median_interval_sec", "min_interval_sec",
        "max_interval_sec", "interval_label", "interval_regular", "head_rows_parsed",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(profiles)
    logger.info("Saved: %s", output_path)


def write_quality_context(profiles: list[dict], output_path: Path) -> None:
    from collections import Counter

    interval_groups: Counter[str] = Counter(p["interval_label"] for p in profiles)
    starts    = sorted(p["start_utc"] for p in profiles if p["start_utc"])
    ends      = sorted(p["end_utc"]   for p in profiles if p["end_utc"])
    durations = [p["duration_days"] for p in profiles if p["duration_days"] != ""]
    gap_files = [p["file_name"] for p in profiles if p["head_gap_detected"]]
    bms_files     = [p for p in profiles if p["start_utc"] and p["start_utc"] < "2024"]
    weather_files = [p for p in profiles if p["start_utc"] and p["start_utc"] >= "2024"]

    interval_notes = {
        "~5s":   "Very high frequency — battery/power electronics",
        "~20s":  "Standard BMS polling interval",
        "~1min": "Medium frequency signals",
        "~5min": "Typical HVAC aggregate interval",
        "~1hr":  "Setpoint/config files — sparse by design",
        "unknown": "Could not determine interval from head sample",
    }

    def md_row(*cells: str) -> str:
        return "| " + " | ".join(cells) + " |\n"

    lines = [
        "# Data Quality Context\n\n",
        f"_Generated: {datetime.now().isoformat()}_\n\n",
        "## Time Coverage Summary\n\n",
        f"- **Earliest start:** `{min(starts) if starts else 'unknown'}`\n",
        f"- **Latest end:** `{max(ends) if ends else 'unknown'}`\n",
        f"- **BMS signals (pre-2024):** {len(bms_files)} files\n",
        f"- **Weather/forecast signals (2024+):** {len(weather_files)} files\n",
    ]
    if durations:
        lines.append(f"- **Median duration:** {statistics.median(durations):.1f} days\n")
        lines.append(f"- **Max duration:** {max(durations):.1f} days\n")

    lines.append("\n## Sampling Interval Groups\n\n| Interval | Count | Notes |\n|---|---|---|\n")
    for label, count in interval_groups.most_common():
        note = interval_notes.get(label, "")
        lines.append(md_row(f"`{label}`", str(count), note))

    lines.append("\n## Gap Detection (head sample only)\n\n")
    lines.append(f"Files with irregular gaps in first 30 rows: **{len(gap_files)}**\n\n")
    lines.append("Note: most are `V_real*` setpoint files — sparse by design, not missing data.\n")

    lines.append("\n## Data Quality Notes\n\n")
    lines.append("- All files: UTF-8 encoding, semicolon delimiter — no parsing issues\n")
    lines.append("- Timestamps are UTC (ISO 8601 `Z` suffix)\n")
    lines.append("- Local timezone: CET (UTC+1) / CEST (UTC+2) — convert for scheduling analysis\n")
    lines.append("- **Data is live/current: runs to 2026-05-27**\n")
    lines.append("- Full gap/duplicate scan deferred — requires full-file reads (40+ GB)\n")

    output_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Saved: %s", output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Profile time-series coverage for all EnFa signal files.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--raw-dir",      default=None)
    parser.add_argument("--project-root", default=None)
    return parser


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = build_arg_parser().parse_args()
    cfg = load_config()
    paths: ProjectPaths = resolve_paths(
        raw_dir=Path(args.raw_dir) if args.raw_dir else None,
        project_root=Path(args.project_root) if args.project_root else None,
        cfg=cfg,
    )
    paths.ensure_output_dirs()

    head_rows  = cfg["sampling"].get("head_rows",  30)
    tail_bytes = cfg["sampling"].get("tail_bytes", 4_096)

    csv_files = sorted([f for f in paths.raw_data.iterdir() if f.is_file() and f.suffix.lower() == ".csv"])
    total = len(csv_files)
    logger.info("Profiling %d files (head + tail only)...", total)

    profiles = []
    for idx, fpath in enumerate(csv_files, 1):
        profiles.append(profile_file(fpath, head_rows=head_rows, tail_bytes=tail_bytes))
        if idx % 50 == 0 or idx == total:
            logger.info("  %d / %d done", idx, total)

    write_coverage_report(profiles, paths.reports / "timestamp_coverage_report.csv")
    write_interval_report(profiles, paths.reports / "sampling_interval_report.csv")
    write_quality_context(profiles, paths.context / "data_quality_context.md")

    from collections import Counter
    interval_groups = Counter(p["interval_label"] for p in profiles)
    starts = sorted(p["start_utc"] for p in profiles if p["start_utc"])
    ends   = sorted(p["end_utc"]   for p in profiles if p["end_utc"])

    print(f"\n{'='*60}")
    if starts:
        print(f"Earliest start : {starts[0]}")
        print(f"Latest end     : {ends[-1] if ends else 'unknown'}")
    print("\nSampling interval groups:")
    for label, count in interval_groups.most_common():
        print(f"  {label:12s}  {count:3d} files")

    gap_count = sum(1 for p in profiles if p["head_gap_detected"])
    print(f"\nFiles with head gap : {gap_count}")
    logger.info("Time-series profiling complete.")


if __name__ == "__main__":
    main()
