"""
03_profile_timeseries.py  —  time-series profiling (head + tail only, no full reads)

Reads first ~30 rows (head) and last ~4 KB (tail) per file to extract:
  - Start timestamp
  - End timestamp
  - Duration
  - Median sampling interval (from head)
  - Sampling regularity flag
  - Gap detection (from head sample only — not exhaustive)

Usage:
    python scripts/03_profile_timeseries.py --raw-dir "C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data"

Outputs:
    reports/timestamp_coverage_report.csv
    reports/sampling_interval_report.csv
    context/data_quality_context.md
"""

import argparse
import csv
import io
import os
import statistics
from datetime import datetime, timezone, timedelta
from pathlib import Path


DELIMITER = ";"
ENCODING = "utf-8"
HEAD_ROWS = 30       # rows to read from start for interval estimation
TAIL_BYTES = 4096    # bytes to read from end for last timestamp


def parse_ts(ts_str: str):
    """Parse ISO 8601 UTC timestamp. Returns datetime or None."""
    ts_str = ts_str.strip()
    if not ts_str:
        return None
    try:
        # Handle both 'Z' suffix and milliseconds/microseconds
        ts_str = ts_str.replace("Z", "+00:00")
        return datetime.fromisoformat(ts_str)
    except Exception:
        try:
            # Fallback: strip sub-seconds
            base = ts_str.split(".")[0].replace("Z", "")
            return datetime.fromisoformat(base).replace(tzinfo=timezone.utc)
        except Exception:
            return None


def read_head_rows(fpath: Path, n: int = HEAD_ROWS) -> tuple[list[str], list[list[str]]]:
    """Read first n data rows. Returns (header, data_rows)."""
    header: list[str] = []
    data_rows: list[list[str]] = []
    try:
        with open(fpath, "r", encoding=ENCODING, errors="replace") as f:
            reader = csv.reader(f, delimiter=DELIMITER)
            for i, row in enumerate(reader):
                if i == 0:
                    header = row
                else:
                    data_rows.append(row)
                    if len(data_rows) >= n:
                        break
    except Exception:
        pass
    return header, data_rows


def read_tail_lines(fpath: Path, tail_bytes: int = TAIL_BYTES) -> list[str]:
    """Read last tail_bytes of file, return non-empty lines."""
    try:
        size = fpath.stat().st_size
        seek_pos = max(0, size - tail_bytes)
        with open(fpath, "rb") as f:
            f.seek(seek_pos)
            raw = f.read()
        text = raw.decode(ENCODING, errors="replace")
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        return lines
    except Exception:
        return []


def get_time_col_idx(header: list[str]) -> int:
    """Return index of _time column."""
    for i, h in enumerate(header):
        if "_time" in h.lower():
            return i
    return -1


def profile_file(fpath: Path) -> dict:
    header, data_rows = read_head_rows(fpath, HEAD_ROWS)
    time_idx = get_time_col_idx(header)

    start_ts = None
    end_ts = None
    intervals_sec: list[float] = []
    timestamps: list[datetime] = []

    if time_idx >= 0 and data_rows:
        for row in data_rows:
            if time_idx < len(row):
                dt = parse_ts(row[time_idx])
                if dt:
                    timestamps.append(dt)

        if timestamps:
            start_ts = timestamps[0]
            # Compute intervals between consecutive head timestamps
            for i in range(1, len(timestamps)):
                diff = (timestamps[i] - timestamps[i - 1]).total_seconds()
                if 0 < diff < 86400:  # ignore negative or >1-day gaps in head
                    intervals_sec.append(diff)

    # Get end timestamp from tail
    tail_lines = read_tail_lines(fpath)
    for line in reversed(tail_lines):
        parts = line.split(DELIMITER)
        if len(parts) >= 3:
            dt = parse_ts(parts[1])  # _time is column index 1 (after empty Unnamed:0)
            if dt:
                end_ts = dt
                break

    # Compute interval stats
    median_interval = None
    min_interval = None
    max_interval = None
    interval_regular = None
    if intervals_sec:
        median_interval = round(statistics.median(intervals_sec), 1)
        min_interval = round(min(intervals_sec), 1)
        max_interval = round(max(intervals_sec), 1)
        # "Regular" if 90% of intervals within 20% of median
        if len(intervals_sec) >= 3:
            within = sum(1 for x in intervals_sec if abs(x - median_interval) < 0.2 * median_interval + 1)
            interval_regular = within / len(intervals_sec) >= 0.9

    # Duration
    duration_days = None
    if start_ts and end_ts and end_ts > start_ts:
        duration_days = round((end_ts - start_ts).total_seconds() / 86400, 1)

    # Classify interval
    interval_label = "unknown"
    if median_interval is not None:
        if median_interval <= 5:
            interval_label = "~5s"
        elif median_interval <= 22:
            interval_label = "~20s"
        elif median_interval <= 65:
            interval_label = "~1min"
        elif median_interval <= 310:
            interval_label = "~5min"
        elif median_interval <= 920:
            interval_label = "~15min"
        elif median_interval <= 3700:
            interval_label = "~1hr"
        else:
            interval_label = f"~{round(median_interval/60)}min"

    return {
        "file_name": fpath.name,
        "start_utc": start_ts.isoformat() if start_ts else "",
        "end_utc": end_ts.isoformat() if end_ts else "",
        "duration_days": duration_days if duration_days is not None else "",
        "median_interval_sec": median_interval if median_interval is not None else "",
        "min_interval_sec": min_interval if min_interval is not None else "",
        "max_interval_sec": max_interval if max_interval is not None else "",
        "interval_label": interval_label,
        "interval_regular": interval_regular if interval_regular is not None else "",
        "head_rows_parsed": len(timestamps),
        "head_gap_detected": max_interval > median_interval * 5 if (max_interval and median_interval and median_interval > 0) else False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=r"C:\Users\dellg\OneDrive\Documents\ZE\data")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    project_root = raw_dir.parent
    reports_dir = project_root / "reports"
    context_dir = project_root / "context"

    csv_files = sorted([f for f in raw_dir.iterdir() if f.is_file() and f.suffix.lower() == ".csv"])
    total = len(csv_files)
    print(f"Profiling {total} files (head+tail only)...")

    results = []
    interval_groups: dict[str, list[str]] = {}

    for i, fpath in enumerate(csv_files, 1):
        rec = profile_file(fpath)
        results.append(rec)
        grp = rec["interval_label"]
        interval_groups.setdefault(grp, []).append(fpath.name)
        if i % 50 == 0 or i == total:
            print(f"  {i}/{total} done")

    # Write timestamp_coverage_report.csv
    cov_path = reports_dir / "timestamp_coverage_report.csv"
    cov_fields = ["file_name", "start_utc", "end_utc", "duration_days",
                  "median_interval_sec", "interval_label", "interval_regular",
                  "head_gap_detected"]
    with open(cov_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cov_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"Saved: {cov_path}")

    # Write sampling_interval_report.csv
    samp_path = reports_dir / "sampling_interval_report.csv"
    samp_fields = ["file_name", "median_interval_sec", "min_interval_sec",
                   "max_interval_sec", "interval_label", "interval_regular", "head_rows_parsed"]
    with open(samp_path, "w", newline="", encoding="utf-8") as f:
        w2 = csv.DictWriter(f, fieldnames=samp_fields, extrasaction="ignore")
        w2.writeheader()
        w2.writerows(results)
    print(f"Saved: {samp_path}")

    # Console summary
    print(f"\n{'='*60}")
    print(f"TIME COVERAGE SUMMARY")

    # Overall date range
    starts = [r["start_utc"] for r in results if r["start_utc"]]
    ends = [r["end_utc"] for r in results if r["end_utc"]]
    if starts:
        print(f"  Earliest start : {min(starts)}")
        print(f"  Latest start   : {max(starts)}")
    if ends:
        print(f"  Earliest end   : {min(ends)}")
        print(f"  Latest end     : {max(ends)}")

    durations = [r["duration_days"] for r in results if r["duration_days"] != ""]
    if durations:
        print(f"  Duration range : {min(durations):.1f} – {max(durations):.1f} days")
        print(f"  Median duration: {statistics.median(durations):.1f} days")

    print(f"\n  Sampling interval groups:")
    for label, files in sorted(interval_groups.items(), key=lambda x: -len(x[1])):
        print(f"    {label:12s}  {len(files):3d} files")

    gap_files = [r["file_name"] for r in results if r["head_gap_detected"]]
    print(f"\n  Files with gap in head sample: {len(gap_files)}")
    for fn in gap_files[:10]:
        print(f"    {fn}")

    # Signals by time range group
    weather_files = [r for r in results if r.get("start_utc", "") >= "2024"]
    bms_files = [r for r in results if r.get("start_utc", "") < "2024" and r.get("start_utc", "")]
    print(f"\n  BMS signals (start < 2024)  : {len(bms_files)} files")
    print(f"  Weather signals (start 2024+): {len(weather_files)} files")

    # Write context/data_quality_context.md
    ctx_path = context_dir / "data_quality_context.md"
    lines = [
        "# Data Quality Context\n",
        f"\n_Generated: {datetime.now().isoformat()}_\n",
        "\n## Time Coverage Summary\n\n",
        f"- **Earliest start:** `{min(starts) if starts else 'unknown'}`\n",
        f"- **Latest end:** `{max(ends) if ends else 'unknown'}`\n",
        f"- **BMS signals (pre-2024):** {len(bms_files)} files\n",
        f"- **Weather/forecast signals (2024+):** {len(weather_files)} files\n\n",
        "Note: Two distinct time periods observed. BMS data starts ~Dec 2022. "
        "Weather/forecast data starts ~Feb 2024. These likely reflect different data "
        "collection phases or the weather integration was added later.\n\n",
        "## Sampling Interval Groups\n\n| Interval | Count | Notes |\n|---|---|---|\n",
    ]
    interval_notes = {
        "~5s": "Very high frequency — likely battery/power electronics",
        "~20s": "Standard BMS polling interval",
        "~1min": "Medium frequency signals",
        "~5min": "Typical energy meter interval",
        "~15min": "Standard utility metering",
        "~1hr": "Hourly aggregates",
        "unknown": "Could not determine interval",
    }
    for label, files in sorted(interval_groups.items(), key=lambda x: -len(x[1])):
        note = interval_notes.get(label, "")
        lines.append(f"| `{label}` | {len(files)} | {note} |\n")

    lines.append("\n## Gap Detection (head sample only)\n\n")
    if gap_files:
        lines.append(f"Files with irregular gaps in first {HEAD_ROWS} rows:\n\n")
        for fn in gap_files:
            lines.append(f"- `{fn}`\n")
    else:
        lines.append("No significant gaps detected in head samples.\n")

    lines.append("\n## Data Quality Notes\n\n")
    lines.append("- All files: UTF-8 encoding, semicolon delimiter — no parsing issues expected\n")
    lines.append("- Timestamps are UTC (ISO 8601 with Z suffix)\n")
    lines.append("- Local timezone: CET (UTC+1) / CEST (UTC+2) — convert for scheduling analysis\n")
    lines.append("- `pilot.csv`: CPU monitoring strings — exclude from energy analysis\n")
    lines.append("- `A.csv`, `_value.csv`: ramp test signals — exclude\n")
    lines.append("- Full gap/duplicate analysis requires per-file full scan (deferred to later step)\n")

    lines.append("\n## Signals Sorted by Start Date (earliest 20)\n\n| File | Start UTC | Duration (days) | Interval |\n|---|---|---|---|\n")
    sorted_by_start = sorted([r for r in results if r["start_utc"]], key=lambda x: x["start_utc"])
    for r in sorted_by_start[:20]:
        lines.append("| `" + r["file_name"] + "` | `" + r["start_utc"][:19] + "` | " + str(r["duration_days"]) + " | " + r["interval_label"] + " |\n")

    with open(ctx_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"\nSaved: {ctx_path}")
    print("Time-series profiling complete.")


if __name__ == "__main__":
    main()
