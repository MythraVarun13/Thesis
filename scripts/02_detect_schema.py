"""
02_detect_schema.py
===================
Step 2: CSV dialect and schema detection for all EnFa signal files.

Reads only the first 6 KB of each file (no full loads).  Detects delimiter,
encoding, column names, and estimates row count from file size.

Usage
-----
    python scripts/02_detect_schema.py
    python scripts/02_detect_schema.py --raw-dir /path/to/data

Outputs
-------
    reports/file_format_report.csv
    reports/schema_summary.csv
    reports/sample_rows/<signal>_sample.csv  (max 20 rows per file)
    context/schema_context.md
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths
from zoro_eda.csv_io import (
    detect_encoding,
    detect_delimiter,
    find_column,
    estimate_row_count,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants (override via config.yaml)
# ---------------------------------------------------------------------------
DEFAULT_HEAD_BYTES = 6_144   # 6 KB per file
DEFAULT_SAMPLE_ROWS = 20


def analyse_file(fpath: Path, head_bytes: int = DEFAULT_HEAD_BYTES) -> dict:
    """Read first ``head_bytes`` of one file and return schema metadata."""
    try:
        with open(fpath, "rb") as fh:
            raw = fh.read(head_bytes)
    except OSError as exc:
        logger.warning("Cannot read %s: %s", fpath, exc)
        return _empty_result(fpath)

    encoding = detect_encoding(raw)
    delimiter, columns = detect_delimiter(raw)

    col_lower = [c.strip().lower() for c in columns]
    has_time        = find_column(columns, "_time") >= 0
    has_value       = find_column(columns, "_value") >= 0
    has_field       = find_column(columns, "_field") >= 0
    has_measurement = find_column(columns, "_measurement") >= 0
    schema_type     = "standard" if (has_time and has_value and has_measurement) else "non-standard"

    rows_estimated = estimate_row_count(fpath)

    # Parse sample rows and extract value range + measurement name
    text = raw.decode(encoding, errors="replace")
    sample_rows: list[list[str]] = []
    try:
        import io
        reader = csv.reader(io.StringIO(text), delimiter=delimiter)
        for idx, row in enumerate(reader):
            sample_rows.append(row)
            if idx >= DEFAULT_SAMPLE_ROWS:
                break
    except csv.Error as exc:
        logger.debug("CSV parse error in %s: %s", fpath, exc)

    val_min = val_max = None
    measurement_values: set[str] = set()

    if len(sample_rows) > 1:
        header = sample_rows[0]
        value_idx       = find_column(header, "_value")
        measurement_idx = find_column(header, "_measurement")

        numeric_vals: list[float] = []
        for row in sample_rows[1:]:
            if value_idx >= 0 and value_idx < len(row):
                try:
                    numeric_vals.append(float(row[value_idx]))
                except ValueError:
                    pass
            if measurement_idx >= 0 and measurement_idx < len(row):
                meas = row[measurement_idx].strip()
                if meas:
                    measurement_values.add(meas)

        if numeric_vals:
            val_min = round(min(numeric_vals), 4)
            val_max = round(max(numeric_vals), 4)

    return {
        "file_name":         fpath.name,
        "encoding":          encoding,
        "delimiter":         delimiter,
        "num_columns":       len(columns),
        "column_names":      "|".join(columns),
        "single_column":     len(columns) <= 1,
        "has_time":          has_time,
        "has_value":         has_value,
        "has_field":         has_field,
        "has_measurement":   has_measurement,
        "schema_type":       schema_type,
        "data_rows_estimated": rows_estimated,
        "sample_val_min":    val_min if val_min is not None else "",
        "sample_val_max":    val_max if val_max is not None else "",
        "measurement_values": "|".join(sorted(measurement_values)),
        "_sample_rows":      sample_rows,   # internal; not written to CSV
    }


def _empty_result(fpath: Path) -> dict:
    return {
        "file_name": fpath.name, "encoding": "unknown", "delimiter": ";",
        "num_columns": 0, "column_names": "", "single_column": True,
        "has_time": False, "has_value": False, "has_field": False,
        "has_measurement": False, "schema_type": "error",
        "data_rows_estimated": -1, "sample_val_min": "", "sample_val_max": "",
        "measurement_values": "", "_sample_rows": [],
    }


def write_format_report(results: list[dict], output_path: Path) -> None:
    fields = [
        "file_name", "encoding", "delimiter", "num_columns", "column_names",
        "single_column", "has_time", "has_value", "has_field", "has_measurement",
        "schema_type", "data_rows_estimated", "sample_val_min", "sample_val_max",
        "measurement_values",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)
    logger.info("Saved: %s", output_path)


def write_schema_summary(results: list[dict], output_path: Path) -> None:
    standard    = [r for r in results if r["schema_type"] == "standard"]
    non_standard = [r for r in results if r["schema_type"] not in ("standard",)]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["schema_type", "count", "example_files"])
        writer.writerow(["standard",     len(standard),     "|".join(r["file_name"] for r in standard[:5])])
        writer.writerow(["non-standard", len(non_standard), "|".join(r["file_name"] for r in non_standard[:5])])
    logger.info("Saved: %s", output_path)


def write_sample_rows(results: list[dict], sample_dir: Path) -> None:
    for result in results:
        sample_rows = result.pop("_sample_rows", [])
        if not sample_rows:
            continue
        safe_stem = result["file_name"].replace(".csv", "").replace(" ", "_")
        sample_path = sample_dir / f"{safe_stem}_sample.csv"
        try:
            with open(sample_path, "w", newline="", encoding="utf-8") as fh:
                csv.writer(fh).writerows(sample_rows)
        except OSError as exc:
            logger.warning("Could not write sample for %s: %s", result["file_name"], exc)


def write_schema_context(
    results: list[dict],
    encoding_counts: Counter,
    delimiter_counts: Counter,
    output_path: Path,
) -> None:
    standard     = [r for r in results if r["schema_type"] == "standard"]
    non_standard = [r for r in results if r["schema_type"] not in ("standard",)]

    def md_table_row(*cells: str) -> str:
        return "| " + " | ".join(cells) + " |\n"

    lines = [
        "# Schema Context\n\n",
        f"_Generated: {datetime.now().isoformat()}_\n\n",
        "## Summary\n\n",
        f"- **Total files:** {len(results)}\n",
        f"- **Standard schema:** {len(standard)}\n",
        f"- **Non-standard schema:** {len(non_standard)}\n\n",
        "## Encoding\n\n| Encoding | Count |\n|---|---|\n",
    ]
    for enc, count in encoding_counts.most_common():
        lines.append(md_table_row(f"`{enc}`", str(count)))

    lines.append("\n## Delimiter\n\n| Delimiter | Count |\n|---|---|\n")
    for delim, count in delimiter_counts.most_common():
        lines.append(md_table_row(f"`{repr(delim)}`", str(count)))

    lines.append("\n## Standard Schema Pattern\n\n")
    lines.append("```\nUnnamed: 0 ; _time ; _value ; _field ; _measurement\n```\n\n")
    lines.append("- `Unnamed: 0` — empty index (InfluxDB export artifact)\n")
    lines.append("- `_time` — UTC ISO 8601 timestamp\n")
    lines.append("- `_value` — float measurement\n")
    lines.append("- `_field` — always `value`\n")
    lines.append("- `_measurement` — BMS signal name (same as filename stem)\n")

    lines.append("\n## Non-Standard Files\n\n")
    if non_standard:
        lines.append("| File | Columns | Column Names |\n|---|---|---|\n")
        for result in non_standard:
            lines.append(md_table_row(
                f"`{result['file_name']}`",
                str(result["num_columns"]),
                f"`{result['column_names'][:100]}`",
            ))
    else:
        lines.append("None — all files follow the standard schema.\n")

    lines.append("\n## Top 20 Files by Estimated Row Count\n\n| File | Est. Rows |\n|---|---|\n")
    top_by_rows = sorted(results, key=lambda r: r["data_rows_estimated"] or 0, reverse=True)
    for result in top_by_rows[:20]:
        lines.append(md_table_row(f"`{result['file_name']}`", f"{result['data_rows_estimated']:,}"))

    output_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Saved: %s", output_path)


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect CSV schema for all EnFa signal files.",
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

    head_bytes = cfg["sampling"].get("head_bytes", DEFAULT_HEAD_BYTES)
    csv_files = sorted([f for f in paths.raw_data.iterdir() if f.is_file() and f.suffix.lower() == ".csv"])
    total = len(csv_files)
    logger.info("Analysing %d files (%.0f KB head per file)...", total, head_bytes / 1_024)

    results = []
    for idx, fpath in enumerate(csv_files, 1):
        results.append(analyse_file(fpath, head_bytes))
        if idx % 50 == 0 or idx == total:
            logger.info("  %d / %d done", idx, total)

    # Pop internal _sample_rows before tallying, but write samples first
    write_sample_rows(results, paths.sample_rows)

    encoding_counts  = Counter(r["encoding"]   for r in results)
    delimiter_counts = Counter(r["delimiter"]  for r in results)
    standard_count   = sum(1 for r in results if r["schema_type"] == "standard")
    non_standard     = [r for r in results if r["schema_type"] != "standard"]

    write_format_report(results, paths.reports / "file_format_report.csv")
    write_schema_summary(results, paths.reports / "schema_summary.csv")
    write_schema_context(results, encoding_counts, delimiter_counts, paths.context / "schema_context.md")

    # Console summary
    print(f"\n{'='*60}")
    print(f"Standard schema : {standard_count} / {total}")
    print(f"Non-standard    : {len(non_standard)} / {total}")
    print(f"Encoding  : {dict(encoding_counts)}")
    print(f"Delimiter : {dict(delimiter_counts)}")
    if non_standard:
        print("\nNon-standard files:")
        for r in non_standard:
            print(f"  {r['file_name']}  cols={r['num_columns']}")

    top_rows = sorted(results, key=lambda r: r["data_rows_estimated"] or 0, reverse=True)
    print("\nTop 10 by estimated rows:")
    for result in top_rows[:10]:
        print(f"  ~{result['data_rows_estimated']:>12,}  {result['file_name']}")

    logger.info("Schema detection complete.")


if __name__ == "__main__":
    main()
