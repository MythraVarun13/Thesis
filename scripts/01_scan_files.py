"""
01_scan_files.py
================
Step 1: File inventory for the EnFa raw data directory.

Scans every file in the raw data folder and records name, size, extension,
and empty-file flag.  Does NOT open file contents — filesystem metadata only.

Usage
-----
    python scripts/01_scan_files.py
    python scripts/01_scan_files.py --raw-dir /path/to/data

Outputs
-------
    reports/data_inventory.csv
    context/data_inventory_context.md
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Allow running from project root without pip-installing the package
# ---------------------------------------------------------------------------
_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Pure functions
# ---------------------------------------------------------------------------

def scan_files(raw_dir: Path) -> list[dict]:
    """Walk ``raw_dir`` and collect file metadata.

    Returns a list of dicts sorted by file size (largest first).
    Does not recurse into subdirectories.
    """
    records = []
    for fpath in raw_dir.iterdir():
        if not fpath.is_file():
            continue
        try:
            stat = fpath.stat()
            size_bytes = stat.st_size
        except OSError as exc:
            logger.warning("Cannot stat %s: %s", fpath, exc)
            size_bytes = -1

        records.append({
            "file_name":     fpath.name,
            "relative_path": fpath.name,
            "extension":     fpath.suffix.lower(),
            "size_bytes":    size_bytes,
            "size_kb":       round(size_bytes / 1_024, 2) if size_bytes >= 0 else -1,
            "size_mb":       round(size_bytes / 1_024 ** 2, 4) if size_bytes >= 0 else -1,
            "is_empty":      size_bytes == 0,
            "absolute_path": str(fpath),
        })

    records.sort(key=lambda record: record["size_bytes"], reverse=True)
    return records


def print_summary(records: list[dict], top_n: int = 30) -> None:
    """Print a human-readable summary to stdout."""
    total_bytes = sum(r["size_bytes"] for r in records if r["size_bytes"] >= 0)
    empty = [r for r in records if r["is_empty"]]
    non_csv = [r for r in records if r["extension"] not in (".csv", "")]

    from collections import Counter
    ext_counts: Counter[str] = Counter(r["extension"] or "(no ext)" for r in records)
    ext_sizes: dict[str, int] = {}
    for record in records:
        ext = record["extension"] or "(no ext)"
        ext_sizes[ext] = ext_sizes.get(ext, 0) + max(record["size_bytes"], 0)

    print(f"{'='*60}")
    print(f"TOTAL FILES : {len(records)}")
    print(f"TOTAL SIZE  : {total_bytes / 1_024**3:.3f} GB  ({total_bytes:,} bytes)")
    print(f"EMPTY FILES : {len(empty)}")

    print(f"\nExtension breakdown:")
    for ext, count in ext_counts.most_common():
        mb = ext_sizes[ext] / 1_024**2
        print(f"  {ext:15s}  {count:5d} files   {mb:10.2f} MB")

    print(f"\nTop {top_n} largest files:")
    for record in records[:top_n]:
        print(f"  {record['size_mb']:10.4f} MB  {record['relative_path']}")

    if empty:
        print(f"\nEmpty files ({len(empty)}):")
        for record in empty:
            print(f"  {record['relative_path']}")

    if non_csv:
        print(f"\nNon-CSV files ({len(non_csv)}):")
        for record in non_csv:
            print(f"  {record['extension']:10s}  {record['relative_path']}")


def write_inventory_csv(records: list[dict], output_path: Path) -> None:
    """Save inventory to CSV."""
    fields = ["file_name", "relative_path", "extension", "size_bytes",
              "size_kb", "size_mb", "is_empty", "absolute_path"]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)
    logger.info("Saved inventory CSV: %s", output_path)


def write_inventory_context(records: list[dict], output_path: Path) -> None:
    """Save markdown context file."""
    total_bytes = sum(r["size_bytes"] for r in records if r["size_bytes"] >= 0)
    empty = [r for r in records if r["is_empty"]]
    non_csv = [r for r in records if r["extension"] not in (".csv", "")]

    from collections import Counter
    ext_counts: Counter[str] = Counter(r["extension"] or "(no ext)" for r in records)
    ext_sizes: dict[str, int] = {}
    for record in records:
        ext = record["extension"] or "(no ext)"
        ext_sizes[ext] = ext_sizes.get(ext, 0) + max(record["size_bytes"], 0)

    lines = [
        "# Data Inventory Context\n\n",
        f"_Generated: {datetime.now().isoformat()}_\n\n",
        "## Summary\n\n",
        f"- **Total files:** {len(records)}\n",
        f"- **Total size:** {total_bytes / 1_024**3:.3f} GB\n",
        f"- **Empty files:** {len(empty)}\n",
        f"- **Non-CSV files:** {len(non_csv)}\n\n",
        "## Extension Breakdown\n\n| Extension | Count | Size (MB) |\n|---|---|---|\n",
    ]
    for ext, count in ext_counts.most_common():
        mb = ext_sizes[ext] / 1_024**2
        lines.append(f"| `{ext}` | {count} | {mb:.2f} |\n")

    lines.append("\n## Top 30 Largest Files\n\n| File | Size (MB) |\n|---|---|\n")
    for record in records[:30]:
        lines.append(f"| `{record['relative_path']}` | {record['size_mb']} |\n")

    if empty:
        lines.append("\n## Empty Files\n\n")
        for record in empty:
            lines.append(f"- `{record['relative_path']}`\n")

    if non_csv:
        lines.append("\n## Non-CSV Files\n\n")
        for record in non_csv:
            lines.append(f"- `{record['extension']}` — `{record['relative_path']}`\n")

    output_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Saved context: %s", output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scan EnFa raw data files and produce an inventory report.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--raw-dir",
        default=None,
        help="Path to raw data directory. Defaults to <project_root>/data.",
    )
    parser.add_argument(
        "--project-root",
        default=None,
        help="Project root directory. Auto-detected if not provided.",
    )
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

    logger.info("Scanning: %s", paths.raw_data)
    records = scan_files(paths.raw_data)

    if not records:
        logger.error("No files found in %s", paths.raw_data)
        return

    print_summary(records)
    write_inventory_csv(records, paths.reports / "data_inventory.csv")
    write_inventory_context(records, paths.context / "data_inventory_context.md")
    logger.info("File inventory complete.")


if __name__ == "__main__":
    main()
