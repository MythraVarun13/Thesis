"""
01_scan_files.py
File inventory scan for the EnFa dataset.

Usage:
    python scripts/01_scan_files.py --raw-dir "C:\\Users\\dellg\\OneDrive\\Documents\\ZE\\data"

Outputs:
    reports/data_inventory.csv
    context/data_inventory_context.md
"""

import argparse
import csv
import os
from datetime import datetime
from pathlib import Path


def scan_files(raw_dir: Path) -> list[dict]:
    """Walk raw_dir and collect file metadata."""
    records = []
    for root, _dirs, files in os.walk(raw_dir):
        for fname in files:
            fpath = Path(root) / fname
            try:
                stat = fpath.stat()
                size_bytes = stat.st_size
                mtime = datetime.fromtimestamp(stat.st_mtime).isoformat()
            except OSError:
                size_bytes = -1
                mtime = "error"

            records.append({
                "file_name": fname,
                "relative_path": str(fpath.relative_to(raw_dir)),
                "extension": fpath.suffix.lower(),
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2) if size_bytes >= 0 else -1,
                "size_mb": round(size_bytes / (1024 ** 2), 4) if size_bytes >= 0 else -1,
                "is_empty": size_bytes == 0,
                "modified": mtime,
                "absolute_path": str(fpath),
            })
    return records


def main():
    parser = argparse.ArgumentParser(description="Scan EnFa raw data files.")
    parser.add_argument(
        "--raw-dir",
        default=r"C:\Users\dellg\OneDrive\Documents\ZE\data",
        help="Path to the raw data folder.",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    project_root = raw_dir.parent
    reports_dir = project_root / "reports"
    context_dir = project_root / "context"
    reports_dir.mkdir(parents=True, exist_ok=True)
    context_dir.mkdir(parents=True, exist_ok=True)

    print(f"Scanning: {raw_dir}")
    records = scan_files(raw_dir)

    if not records:
        print("No files found.")
        return

    # Sort by size descending
    records.sort(key=lambda r: r["size_bytes"], reverse=True)

    # Write CSV inventory
    inventory_path = reports_dir / "data_inventory.csv"
    fieldnames = ["file_name", "relative_path", "extension", "size_bytes",
                  "size_kb", "size_mb", "is_empty", "modified", "absolute_path"]
    with open(inventory_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    print(f"Saved: {inventory_path}")

    # Compute summary statistics
    total_files = len(records)
    total_bytes = sum(r["size_bytes"] for r in records if r["size_bytes"] >= 0)
    total_gb = total_bytes / (1024 ** 3)
    empty_files = [r for r in records if r["is_empty"]]
    ext_counts: dict[str, int] = {}
    ext_sizes: dict[str, int] = {}
    for r in records:
        ext = r["extension"] or "(no ext)"
        ext_counts[ext] = ext_counts.get(ext, 0) + 1
        ext_sizes[ext] = ext_sizes.get(ext, 0) + max(r["size_bytes"], 0)

    # Print top 30 largest
    print(f"\n{'='*60}")
    print(f"TOTAL FILES : {total_files}")
    print(f"TOTAL SIZE  : {total_gb:.3f} GB ({total_bytes:,} bytes)")
    print(f"EMPTY FILES : {len(empty_files)}")
    print(f"\nExtension breakdown:")
    for ext, cnt in sorted(ext_counts.items(), key=lambda x: -x[1]):
        mb = ext_sizes[ext] / (1024 ** 2)
        print(f"  {ext:15s} {cnt:5d} files   {mb:10.2f} MB")

    print(f"\nTop 30 largest files:")
    for r in records[:30]:
        print(f"  {r['size_mb']:10.4f} MB  {r['relative_path']}")

    if empty_files:
        print(f"\nEmpty files ({len(empty_files)}):")
        for r in empty_files:
            print(f"  {r['relative_path']}")

    # Check for suspicious non-CSV files
    non_csv = [r for r in records if r["extension"] not in (".csv", "")]
    if non_csv:
        print(f"\nSuspicious non-CSV files ({len(non_csv)}):")
        for r in non_csv:
            print(f"  {r['extension']}  {r['relative_path']}")

    # Write context/data_inventory_context.md
    context_path = context_dir / "data_inventory_context.md"
    with open(context_path, "w", encoding="utf-8") as f:
        f.write("# Data Inventory Context\n\n")
        f.write(f"_Generated: {datetime.now().isoformat()}_\n\n")
        f.write("## Summary\n\n")
        f.write(f"- **Total files:** {total_files}\n")
        f.write(f"- **Total size:** {total_gb:.3f} GB\n")
        f.write(f"- **Empty files:** {len(empty_files)}\n")
        f.write(f"- **Non-CSV files:** {len(non_csv)}\n\n")
        f.write("## Extension Breakdown\n\n")
        f.write("| Extension | Count | Size (MB) |\n|---|---|---|\n")
        for ext, cnt in sorted(ext_counts.items(), key=lambda x: -x[1]):
            mb = ext_sizes[ext] / (1024 ** 2)
            f.write(f"| `{ext}` | {cnt} | {mb:.2f} |\n")
        f.write("\n## Top 30 Largest Files\n\n")
        f.write("| File | Size (MB) |\n|---|---|\n")
        for r in records[:30]:
            f.write(f"| `{r['relative_path']}` | {r['size_mb']} |\n")
        if empty_files:
            f.write("\n## Empty Files\n\n")
            for r in empty_files:
                f.write(f"- `{r['relative_path']}`\n")
        if non_csv:
            f.write("\n## Non-CSV Files (Suspicious)\n\n")
            for r in non_csv:
                f.write(f"- `{r['extension']}` — `{r['relative_path']}`\n")

    print(f"\nSaved: {context_path}")
    print("File inventory complete.")


if __name__ == "__main__":
    main()
