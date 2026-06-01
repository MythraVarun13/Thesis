"""
05_classify_signals.py
======================
Step 4: Signal classification for all EnFa CSV files.

Maps each signal name to a physical category, English meaning, unit
hypothesis, confidence level, and ZORO JSON v1 pipeline fields
(device_id_suffix, metric, unit).

Classification uses three layers in order:
  1. DIRECT_MAP  — exact stem match (handles underscores, umlaut variants)
  2. PATTERN_RULES — case-insensitive substring matching
  3. Fallback  — category="unknown", confidence="low"

All rules live in src/zoro_eda/signal_rules.py.

Usage
-----
    python scripts/05_classify_signals.py
    python scripts/05_classify_signals.py --raw-dir /path/to/data

Outputs
-------
    reports/signal_classification.csv   — all signals
    reports/sensor_catalog.csv          — active (non-excluded) signals
    reports/zoro_pipeline_mapping.csv   — pipeline-ready signals with JSON v1 fields
    context/signal_dictionary.md
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from dataclasses import asdict, dataclass, fields as dc_fields
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths
from zoro_eda.signal_rules import DIRECT_MAP, PATTERN_RULES, ClassificationTuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class SignalClassification:
    """One classified signal row.  Mirrors the output CSV schema."""

    file_name:            str
    signal_name:          str
    category:             str
    english_meaning:      str
    unit_hypothesis:      str
    confidence:           str
    sample_val_min:       str
    sample_val_max:       str
    exclude:              bool
    zoro_device_id_suffix: str
    zoro_metric:          str
    zoro_unit:            str
    use_energy:           bool
    use_hvac:             bool
    use_heatpump:         bool
    use_pv:               bool
    use_battery:          bool
    use_weather:          bool
    use_fdd:              bool
    use_mpc:              bool

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in dc_fields(cls)]

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def _build_from_tuple(
    signal_name: str,
    filename: str,
    tup: ClassificationTuple,
    sample_min: str = "",
    sample_max: str = "",
) -> SignalClassification:
    """Convert a classification tuple into a ``SignalClassification``."""
    (category, english, unit, confidence,
     device_suffix, metric, zoro_unit,
     exclude, use_cases) = tup

    return SignalClassification(
        file_name=filename,
        signal_name=signal_name,
        category=category,
        english_meaning=english,
        unit_hypothesis=unit,
        confidence=confidence,
        sample_val_min=sample_min,
        sample_val_max=sample_max,
        exclude=exclude,
        zoro_device_id_suffix=device_suffix or "",
        zoro_metric=metric or "",
        zoro_unit=zoro_unit or "",
        use_energy="energy"   in use_cases,
        use_hvac="hvac"       in use_cases,
        use_heatpump="heatpump" in use_cases,
        use_pv="pv"           in use_cases,
        use_battery="battery" in use_cases,
        use_weather="weather" in use_cases,
        use_fdd="fdd"         in use_cases,
        use_mpc="mpc"         in use_cases,
    )


_UNKNOWN_TUPLE: ClassificationTuple = (
    "unknown", "No rule matched — manual review needed", "", "low",
    None, None, None, False, [],
)


def classify_signal(filename: str) -> SignalClassification:
    """Return a ``SignalClassification`` for one CSV file.

    Tries DIRECT_MAP first, then PATTERN_RULES, then falls back to unknown.
    """
    stem = filename.removesuffix(".csv")

    # Layer 1: exact stem match
    if stem in DIRECT_MAP:
        return _build_from_tuple(stem, filename, DIRECT_MAP[stem])

    # Layer 2: pattern matching (all substrings present, case-insensitive)
    stem_lower = stem.lower()
    for substrings, classification_tuple in PATTERN_RULES:
        if all(pattern.lower() in stem_lower for pattern in substrings):
            return _build_from_tuple(stem, filename, classification_tuple)

    # Layer 3: unknown fallback
    return _build_from_tuple(stem, filename, _UNKNOWN_TUPLE)


# ---------------------------------------------------------------------------
# Sample value extraction
# ---------------------------------------------------------------------------

def read_sample_value_range(sample_dir: Path, filename: str) -> tuple[str, str]:
    """Read the sample CSV for ``filename`` and return (min, max) as strings."""
    stem = filename.removesuffix(".csv").replace(" ", "_")
    sample_path = sample_dir / f"{stem}_sample.csv"
    if not sample_path.exists():
        return "", ""

    numeric_values: list[float] = []
    try:
        with open(sample_path, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh, delimiter=";")
            value_key = next(
                (key for key in (reader.fieldnames or []) if "_value" in key.lower()),
                None,
            )
            if value_key is None:
                return "", ""
            for row in reader:
                try:
                    numeric_values.append(float(row[value_key]))
                except (ValueError, KeyError):
                    pass
    except OSError as exc:
        logger.debug("Cannot read sample for %s: %s", filename, exc)
        return "", ""

    if not numeric_values:
        return "", ""
    return str(round(min(numeric_values), 3)), str(round(max(numeric_values), 3))


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_classification_csv(rows: list[SignalClassification], output_path: Path) -> None:
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=SignalClassification.field_names())
        writer.writeheader()
        writer.writerows(row.to_dict() for row in rows)
    logger.info("Saved: %s", output_path)


def write_pipeline_mapping_csv(rows: list[SignalClassification], output_path: Path) -> None:
    """Write only pipeline-ready signals (non-excluded, with metric and unit)."""
    pipeline_fields = [
        "signal_name", "zoro_device_id_suffix", "zoro_metric", "zoro_unit",
        "category", "english_meaning", "confidence",
        "use_energy", "use_hvac", "use_heatpump", "use_pv",
        "use_battery", "use_fdd", "use_mpc",
    ]
    pipeline_rows = [
        row for row in rows
        if not row.exclude and row.zoro_metric and row.zoro_unit
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=pipeline_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(row.to_dict() for row in pipeline_rows)
    logger.info("Saved: %s (%d pipeline-ready signals)", output_path, len(pipeline_rows))


def write_signal_dictionary(rows: list[SignalClassification], output_path: Path) -> None:
    """Write a markdown signal dictionary to the context folder."""
    from collections import Counter

    use_case_counts = {
        key: sum(1 for row in rows if getattr(row, f"use_{key}"))
        for key in ["energy", "hvac", "heatpump", "pv", "battery", "weather", "fdd", "mpc"]
    }
    pipeline_count = sum(1 for row in rows if not row.exclude and row.zoro_metric and row.zoro_unit)
    excluded_count = sum(1 for row in rows if row.exclude)
    unknown_count  = sum(1 for row in rows if row.category == "unknown")

    def md_row(*cells: str) -> str:
        return "| " + " | ".join(cells) + " |\n"

    lines = [
        "# Signal Dictionary\n\n",
        f"_Generated: {datetime.now().isoformat()}_\n\n",
        f"**{len(rows)} signals | {pipeline_count} pipeline-ready"
        f" | {excluded_count} excluded | {unknown_count} unknown**\n\n",
        "## ZORO Use-Case Signal Counts\n\n| Use Case | Signals |\n|---|---|\n",
    ]
    for use_case, count in sorted(use_case_counts.items(), key=lambda x: -x[1]):
        lines.append(md_row(use_case, str(count)))

    lines.append(
        "\n## Full Signal Table\n\n"
        "| Signal | Category | English Meaning | Unit | Confidence | ZORO Metric | ZORO Unit |\n"
        "|---|---|---|---|---|---|---|\n"
    )
    for row in sorted(rows, key=lambda r: (r.category, r.signal_name)):
        exclude_marker = " EXCLUDE" if row.exclude else ""
        lines.append(md_row(
            f"`{row.signal_name}`",
            row.category + exclude_marker,
            row.english_meaning,
            row.unit_hypothesis,
            row.confidence,
            f"`{row.zoro_metric}`",
            row.zoro_unit,
        ))

    output_path.write_text("".join(lines), encoding="utf-8")
    logger.info("Saved: %s", output_path)


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Classify all EnFa signal CSV files.",
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

    csv_files = sorted(
        f for f in paths.raw_data.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
    )
    logger.info("Classifying %d signals...", len(csv_files))

    classified_rows: list[SignalClassification] = []
    for fpath in csv_files:
        row = classify_signal(fpath.name)
        val_min, val_max = read_sample_value_range(paths.sample_rows, fpath.name)
        row.sample_val_min = val_min
        row.sample_val_max = val_max
        classified_rows.append(row)

    # Write all outputs
    active_rows   = [r for r in classified_rows if not r.exclude and r.category != "EXCLUDE"]
    write_classification_csv(classified_rows, paths.reports / "signal_classification.csv")
    write_classification_csv(active_rows,     paths.reports / "sensor_catalog.csv")
    write_pipeline_mapping_csv(classified_rows, paths.reports / "zoro_pipeline_mapping.csv")
    write_signal_dictionary(classified_rows, paths.context / "signal_dictionary.md")

    # Console summary
    from collections import Counter
    category_counts = Counter(row.category for row in classified_rows)
    confidence_counts = Counter(row.confidence for row in classified_rows)
    excluded_count = sum(1 for row in classified_rows if row.exclude)
    unknown_count  = sum(1 for row in classified_rows if row.category == "unknown")
    pipeline_count = sum(1 for row in classified_rows if not row.exclude and row.zoro_metric and row.zoro_unit)

    print(f"\n{'='*60}")
    print(f"Total: {len(classified_rows)}  |  Excluded: {excluded_count}  |  Unknown: {unknown_count}  |  Pipeline-ready: {pipeline_count}")
    print(f"Confidence: {dict(confidence_counts)}")
    print("\nTop 10 categories:")
    for category, count in category_counts.most_common(10):
        print(f"  {category:<35}  {count}")
    logger.info("Signal classification complete.")


if __name__ == "__main__":
    main()
