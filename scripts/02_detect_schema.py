"""
02_detect_schema.py  —  single-pass schema detection (fast version)
Reads only first 6 KB per file. No full-file reads.

Usage:
    python scripts/02_detect_schema.py --raw-dir "C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data"
"""

import argparse
import csv
import io
import os
from datetime import datetime
from pathlib import Path

HEAD_BYTES = 6144   # 6 KB per file — enough for header + ~20 rows
CANDIDATES = [";", ",", "\t", "|"]


def analyze_file_fast(fpath: Path) -> dict:
    size = fpath.stat().st_size

    # Single read
    raw = b""
    encoding = "utf-8"
    try:
        with open(fpath, "rb") as f:
            raw = f.read(HEAD_BYTES)
    except Exception:
        pass

    # Detect encoding
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            text = raw.decode(enc)
            encoding = enc
            break
        except Exception:
            continue
    else:
        text = raw.decode("latin-1", errors="replace")
        encoding = "latin-1"

    # Detect delimiter — pick one giving most columns on first line
    best_delim = ";"
    best_cols: list[str] = []
    for delim in CANDIDATES:
        try:
            reader = csv.reader(io.StringIO(text), delimiter=delim)
            row = next(reader, [])
            if len(row) > len(best_cols):
                best_cols = row
                best_delim = delim
        except Exception:
            continue

    # Parse sample rows (up to 21 including header)
    sample_rows: list[list[str]] = []
    try:
        reader = csv.reader(io.StringIO(text), delimiter=best_delim)
        for i, row in enumerate(reader):
            sample_rows.append(row)
            if i >= 21:
                break
    except Exception:
        pass

    col_lower = [c.strip().lower() for c in best_cols]
    has_time = any("_time" in c for c in col_lower)
    has_value = any("_value" in c for c in col_lower)
    has_field = any("_field" in c for c in col_lower)
    has_measurement = any("_measurement" in c for c in col_lower)
    schema_type = "standard" if (has_time and has_value and has_measurement) else "non-standard"

    # Estimate rows from newline density
    newlines = raw.count(b"\n")
    rows_est = -1
    if newlines > 1:
        avg = len(raw) / newlines
        rows_est = max(int(size / avg) - 1, 0)

    # Extract measurement values from sample
    m_vals: set[str] = set()
    v_min = v_max = None
    if has_measurement and len(sample_rows) > 1:
        try:
            hdr = sample_rows[0]
            mi = next(i for i, h in enumerate(hdr) if "_measurement" in h.lower())
            vi = next((i for i, h in enumerate(hdr) if "_value" in h.lower()), None)
            nums = []
            for row in sample_rows[1:]:
                if mi < len(row) and row[mi].strip():
                    m_vals.add(row[mi].strip())
                if vi is not None and vi < len(row):
                    try:
                        nums.append(float(row[vi]))
                    except Exception:
                        pass
            if nums:
                v_min, v_max = min(nums), max(nums)
        except Exception:
            pass

    return {
        "file_name": fpath.name,
        "encoding": encoding,
        "delimiter": best_delim,
        "num_columns": len(best_cols),
        "column_names": "|".join(best_cols),
        "single_column": len(best_cols) <= 1,
        "has_time": has_time,
        "has_value": has_value,
        "has_field": has_field,
        "has_measurement": has_measurement,
        "schema_type": schema_type,
        "data_rows_estimated": rows_est,
        "sample_val_min": round(v_min, 4) if v_min is not None else "",
        "sample_val_max": round(v_max, 4) if v_max is not None else "",
        "measurement_values": "|".join(sorted(m_vals)),
        "_sample_rows": sample_rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", default=r"C:\Users\dellg\OneDrive\Documents\ZE\data")
    parser.add_argument("--skip-samples", action="store_true", help="Skip writing sample CSV files")
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    project_root = raw_dir.parent
    reports_dir = project_root / "reports"
    sample_dir = reports_dir / "sample_rows"
    context_dir = project_root / "context"
    if not args.skip_samples:
        sample_dir.mkdir(parents=True, exist_ok=True)

    csv_files = sorted([f for f in raw_dir.iterdir() if f.is_file() and f.suffix.lower() == ".csv"])
    total = len(csv_files)
    print(f"Analyzing {total} files (6 KB head per file)...")

    results = []
    encoding_counts: dict[str, int] = {}
    delimiter_counts: dict[str, int] = {}
    non_standard = []

    for i, fpath in enumerate(csv_files, 1):
        rec = analyze_file_fast(fpath)
        results.append(rec)
        encoding_counts[rec["encoding"]] = encoding_counts.get(rec["encoding"], 0) + 1
        delimiter_counts[rec["delimiter"]] = delimiter_counts.get(rec["delimiter"], 0) + 1
        if rec["schema_type"] == "non-standard":
            non_standard.append(rec)

        if not args.skip_samples and rec["_sample_rows"]:
            sp = sample_dir / (fpath.stem.replace(" ", "_") + "_sample.csv")
            try:
                with open(sp, "w", newline="", encoding="utf-8") as sf:
                    csv.writer(sf).writerows(rec["_sample_rows"])
            except Exception:
                pass

        if i % 50 == 0 or i == total:
            print(f"  {i}/{total} done")

    # Write file_format_report.csv
    fmt_fields = ["file_name", "encoding", "delimiter", "num_columns", "column_names",
                  "single_column", "has_time", "has_value", "has_field", "has_measurement",
                  "schema_type", "data_rows_estimated", "sample_val_min", "sample_val_max",
                  "measurement_values"]
    fmt_path = reports_dir / "file_format_report.csv"
    with open(fmt_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fmt_fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(results)
    print(f"Saved: {fmt_path}")

    # Write schema_summary.csv
    standard = [r for r in results if r["schema_type"] == "standard"]
    summ_path = reports_dir / "schema_summary.csv"
    with open(summ_path, "w", newline="", encoding="utf-8") as f:
        w2 = csv.writer(f)
        w2.writerow(["schema_type", "count", "example_files"])
        w2.writerow(["standard", len(standard), "|".join(r["file_name"] for r in standard[:5])])
        w2.writerow(["non-standard", len(non_standard), "|".join(r["file_name"] for r in non_standard[:5])])
    print(f"Saved: {summ_path}")

    # Console summary
    print(f"\n{'='*60}")
    print(f"Standard schema : {len(standard)} / {total}")
    print(f"Non-standard    : {len(non_standard)} / {total}")
    print(f"Encoding  : {encoding_counts}")
    print(f"Delimiter : {delimiter_counts}")
    if non_standard:
        print("\nNon-standard files:")
        for r in non_standard:
            print(f"  {r['file_name']}  cols={r['num_columns']}  {r['column_names'][:80]}")

    print("\nTop 10 by estimated rows:")
    for r in sorted(results, key=lambda x: x["data_rows_estimated"] or 0, reverse=True)[:10]:
        print(f"  ~{r['data_rows_estimated']:>13,}  {r['file_name']}")

    # Write context/schema_context.md
    ctx_path = context_dir / "schema_context.md"
    lines = [
        "# Schema Context\n",
        f"\n_Generated: {datetime.now().isoformat()}_\n",
        "\n## Summary\n",
        f"\n- **Total files:** {total}\n",
        f"- **Standard schema:** {len(standard)}\n",
        f"- **Non-standard schema:** {len(non_standard)}\n",
        "\n## Encoding\n\n| Encoding | Count |\n|---|---|\n",
    ]
    for enc, cnt in sorted(encoding_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{enc}` | {cnt} |\n")
    lines.append("\n## Delimiter\n\n| Delimiter | Count |\n|---|---|\n")
    for d, cnt in sorted(delimiter_counts.items(), key=lambda x: -x[1]):
        lines.append(f"| `{repr(d)}` | {cnt} |\n")
    lines.append("\n## Standard Schema Pattern\n\n")
    lines.append("```\nUnnamed: 0 ; _time ; _value ; _field ; _measurement\n```\n\n")
    lines.append("- `Unnamed: 0` — empty index (InfluxDB export artifact)\n")
    lines.append("- `_time` — UTC ISO 8601 timestamp (e.g. `2022-12-07T14:11:41Z`)\n")
    lines.append("- `_value` — float measurement\n")
    lines.append("- `_field` — always `value`\n")
    lines.append("- `_measurement` — BMS signal name\n")
    lines.append("\n## Non-Standard Files\n\n")
    if non_standard:
        lines.append("| File | Columns | Column Names |\n|---|---|---|\n")
        for r in non_standard:
            lines.append("| `" + r["file_name"] + "` | " + str(r["num_columns"]) + " | `" + r["column_names"][:100] + "` |\n")
    else:
        lines.append("None — all files follow the standard schema.\n")
    lines.append("\n## Top 20 Files by Estimated Rows\n\n| File | Est. Rows |\n|---|---|\n")
    for r in sorted(results, key=lambda x: x["data_rows_estimated"] or 0, reverse=True)[:20]:
        lines.append("| `" + r["file_name"] + "` | " + str(r["data_rows_estimated"]) + " |\n")

    with open(ctx_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
    print(f"Saved: {ctx_path}")
    print("Done.")


if __name__ == "__main__":
    main()
