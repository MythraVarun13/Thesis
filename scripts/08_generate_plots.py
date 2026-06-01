"""
08_generate_plots.py
====================
Step 5: Exploratory visualisations for key EnFa signals.

Reads signal CSV files using the same head/tail pattern as the other scripts
(no full-file loads). All paths resolved via config.yaml / ProjectPaths.

Usage
-----
    python scripts/08_generate_plots.py
    python scripts/08_generate_plots.py --raw-dir /path/to/data

Outputs (reports/plots/)
------------------------
    01_sampling_interval_histogram.png
    02_signal_category_counts.png
    03_battery_soc_full_history.png
    04_battery_power_recent.png
    05_pv_power_recent.png
    06_building_power_recent.png
    07_hp_defrost_all_units.png
    08_outdoor_temp_full_history.png
    09_dhw_warm_water_profile.png
    10_energy_balance_recent.png
    11_value_distributions_boxplot.png
    12_battery_cluster_voltages.png
"""

from __future__ import annotations

import argparse
import csv
import logging
import sys
from datetime import datetime
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPTS_DIR.parent / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths, ProjectPaths

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Signal reading helpers (no full-file loads)
# ---------------------------------------------------------------------------

def read_signal_head(
    raw_data_dir: Path,
    filename: str,
    max_rows: int = 5_000,
    delimiter: str = ";",
    encoding: str = "utf-8",
) -> tuple[list[datetime], list[float]]:
    """Read up to ``max_rows`` rows from the start of a signal file."""
    fpath = raw_data_dir / filename
    if not fpath.exists():
        logger.warning("Signal file not found: %s", filename)
        return [], []

    timestamps: list[datetime] = []
    values: list[float] = []

    try:
        with open(fpath, "r", encoding=encoding, errors="replace") as fh:
            reader = csv.reader(fh, delimiter=delimiter)
            header = next(reader, [])
            time_idx  = next((i for i, h in enumerate(header) if "_time"  in h.lower()), 1)
            value_idx = next((i for i, h in enumerate(header) if "_value" in h.lower()), 2)
            for row in reader:
                if len(timestamps) >= max_rows:
                    break
                try:
                    ts_str = row[time_idx].strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts_str)
                    timestamps.append(dt)
                    values.append(float(row[value_idx]))
                except (ValueError, IndexError):
                    pass
    except OSError as exc:
        logger.warning("Cannot read %s: %s", fpath, exc)

    return timestamps, values


def read_signal_tail(
    raw_data_dir: Path,
    filename: str,
    tail_bytes: int = 2_000_000,
    max_rows: int = 8_000,
    delimiter: str = ";",
    encoding: str = "utf-8",
) -> tuple[list[datetime], list[float]]:
    """Read up to ``max_rows`` rows from the end of a signal file."""
    fpath = raw_data_dir / filename
    if not fpath.exists():
        logger.warning("Signal file not found: %s", filename)
        return [], []

    file_size = fpath.stat().st_size
    seek_pos = max(0, file_size - tail_bytes)

    timestamps: list[datetime] = []
    values: list[float] = []

    try:
        with open(fpath, "rb") as fh:
            fh.seek(seek_pos)
            raw = fh.read()
        text = raw.decode(encoding, errors="replace")
        for line in text.splitlines()[1:]:  # skip first (possibly partial) line
            parts = line.split(delimiter)
            if len(parts) < 3:
                continue
            try:
                ts_str = parts[1].strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts_str)
                timestamps.append(dt)
                values.append(float(parts[2]))
                if len(timestamps) >= max_rows:
                    break
            except (ValueError, IndexError):
                pass
    except OSError as exc:
        logger.warning("Cannot read tail of %s: %s", fpath, exc)

    return timestamps, values


# ---------------------------------------------------------------------------
# Individual plot functions — one job each
# ---------------------------------------------------------------------------

def plot_sampling_histogram(paths: ProjectPaths, ax_module) -> None:
    """Bar chart: number of signals per sampling interval group."""
    import matplotlib.pyplot as plt

    samp_path = paths.reports / "sampling_interval_report.csv"
    interval_groups: dict[str, int] = {}
    try:
        with open(samp_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                label = row.get("interval_label", "unknown")
                interval_groups[label] = interval_groups.get(label, 0) + 1
    except OSError as exc:
        logger.warning("Cannot read sampling report: %s", exc)
        return

    labels = sorted(interval_groups.keys(), key=lambda x: (x == "unknown", x))
    counts = [interval_groups[label] for label in labels]
    colours = ["#2196F3", "#4CAF50", "#FF9800", "#9C27B0", "#F44336", "#00BCD4", "#795548"]

    fig, ax = plt.subplots(figsize=(8, 4))
    bars = ax.bar(labels, counts, color=colours[:len(labels)])
    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3, str(count),
                ha="center", va="bottom", fontsize=9)
    ax.set_title("EnFa Signal Sampling Interval Distribution (233 signals)")
    ax.set_xlabel("Interval Group")
    ax.set_ylabel("Number of Signals")
    plt.tight_layout()
    _save(fig, paths.plots / "01_sampling_interval_histogram.png")


def plot_category_counts(paths: ProjectPaths, _) -> None:
    """Horizontal bar chart: signal category distribution."""
    import matplotlib.pyplot as plt
    import numpy as np

    class_path = paths.reports / "signal_classification.csv"
    category_counts: dict[str, int] = {}
    try:
        with open(class_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                cat = row.get("category", "unknown")
                category_counts[cat] = category_counts.get(cat, 0) + 1
    except OSError as exc:
        logger.warning("Cannot read classification report: %s", exc)
        return

    top = sorted(category_counts.items(), key=lambda x: -x[1])[:18]
    categories, counts = zip(*top)
    colours = plt.cm.tab20(np.linspace(0, 1, len(categories)))  # type: ignore[attr-defined]

    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(list(reversed(categories)), list(reversed(counts)), color=list(reversed(colours)))
    for bar, count in zip(bars, list(reversed(counts))):
        ax.text(count + 0.1, bar.get_y() + bar.get_height() / 2, str(count), va="center", fontsize=8)
    ax.set_title("EnFa Signal Categories (top 18)")
    ax.set_xlabel("Number of Signals")
    plt.tight_layout()
    _save(fig, paths.plots / "02_signal_category_counts.png")


def plot_battery_soc_history(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times, vals = read_signal_head(paths.raw_data, "greal_BatterieLadeZustand.csv", max_rows=20_000)
    if not times:
        return
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.4, color="#1976D2", alpha=0.8)
    ax.set_title("Battery State of Charge — Full History (greal_BatterieLadeZustand)")
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 105)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "03_battery_soc_full_history.png")


def plot_battery_power_recent(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times, vals = read_signal_tail(paths.raw_data, "real_BatterieLeistung.csv")
    if not times:
        return
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.5, color="#E53935")
    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.set_title("Battery Power — Recent Data (real_BatterieLeistung)\n+ve = charging, -ve = discharging")
    ax.set_ylabel("Power (kW)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "04_battery_power_recent.png")


def plot_pv_power_recent(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times, vals = read_signal_tail(paths.raw_data, "real_PV_Gesamt.csv")
    if not times:
        return
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.fill_between(times, 0, vals, alpha=0.6, color="#FBC02D")
    ax.plot(times, vals, lw=0.5, color="#F57F17")
    ax.set_title("PV Total Power — Recent Data (real_PV_Gesamt)")
    ax.set_ylabel("Power (kW)")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "05_pv_power_recent.png")


def plot_building_power_recent(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times, vals = read_signal_tail(paths.raw_data, "greal_LeistungGebaeude.csv")
    if not times:
        return
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.5, color="#388E3C")
    ax.set_title("Building Electrical Power Demand — Recent (greal_LeistungGebaeude)")
    ax.set_ylabel("Power (kW)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "06_building_power_recent.png")


def plot_hp_defrost_history(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    hp_units = [("WP1", "#1565C0"), ("WP2", "#6A1B9A"), ("WP3", "#B71C1C")]
    fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
    fig.suptitle("Heat Pump Defrost Duration — All 3 Units")
    for ax, (unit, colour) in zip(axes, hp_units):
        times, vals = read_signal_head(paths.raw_data, f"greal_{unit}AbtauSek.csv", max_rows=15_000)
        if times:
            ax.plot(times, vals, lw=0.4, color=colour, alpha=0.8)
        ax.set_ylabel(f"{unit} (s)", fontsize=9)
        ax.set_ylim(bottom=0)
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "07_hp_defrost_all_units.png")


def plot_outdoor_temp_history(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    times, vals = read_signal_head(paths.raw_data, "grealTempAussenGefiltert.csv", max_rows=20_000)
    if not times:
        return
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.4, color="#0288D1", alpha=0.8)
    ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
    ax.set_title("Outdoor Temperature — Full History (grealTempAussenGefiltert)")
    ax.set_ylabel("Temperature (°C)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "08_outdoor_temp_full_history.png")


def plot_dhw_temperature_profile(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    sensors = [
        ("realIstTempWarmWasOben.csv",     "Top",         "#D32F2F"),
        ("realIstTempWarmWasObenMitte.csv", "Upper-middle","#E64A19"),
        ("realIstTempWarmWasUntMitte.csv",  "Lower-middle","#F57C00"),
        ("realIstTempWarmWasUnt.csv",       "Bottom",      "#FBC02D"),
    ]
    fig, ax = plt.subplots(figsize=(14, 5))
    for filename, label, colour in sensors:
        times, vals = read_signal_head(paths.raw_data, filename, max_rows=3_000)
        if times:
            ax.plot(times, vals, lw=0.8, label=label, color=colour, alpha=0.85)
    ax.set_title("DHW Warm Water Storage Temperature Profile — 4 Height Sensors")
    ax.set_ylabel("Temperature (°C)")
    ax.legend(loc="upper right", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "09_dhw_warm_water_profile.png")


def plot_energy_balance_recent(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    signals = [
        ("real_PV_Gesamt.csv",         "PV Power",        "#FBC02D"),
        ("greal_LeistungGebaeude.csv",  "Building Demand", "#388E3C"),
        ("real_BatterieLeistung.csv",   "Battery Power",   "#1976D2"),
        ("real_P_BHKW.csv",             "BHKW Power",      "#E53935"),
    ]
    fig, ax = plt.subplots(figsize=(14, 5))
    for filename, label, colour in signals:
        times, vals = read_signal_tail(paths.raw_data, filename, tail_bytes=1_500_000, max_rows=3_000)
        if times:
            ax.plot(times, vals, lw=0.7, label=label, color=colour, alpha=0.85)
    ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.4)
    ax.set_title("Energy Balance — Recent Data (PV, Building Demand, Battery, BHKW)")
    ax.set_ylabel("Power (kW)")
    ax.legend(loc="upper right", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "10_energy_balance_recent.png")


def plot_value_distributions(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    box_signals = [
        ("greal_BatterieLadeZustand.csv", "Battery SOC (%)"),
        ("real_BatterieLeistung.csv",     "Battery Power (kW)"),
        ("real_PV_Gesamt.csv",            "PV Power (kW)"),
        ("greal_LeistungGebaeude.csv",    "Building Power (kW)"),
        ("real_P_BHKW.csv",               "BHKW Power (kW)"),
        ("grealTempAussenGefiltert.csv",  "Outdoor Temp (°C)"),
        ("grealIstWaermepumpVorlauf.csv", "HP Supply Temp (°C)"),
        ("greal_W_WMZ_P_WP.csv",          "HP Thermal Power (kW)"),
        ("realIstTempWarmWasOben.csv",     "DHW Top Temp (°C)"),
    ]
    data_by_signal: list[list[float]] = []
    signal_labels: list[str] = []

    for filename, label in box_signals:
        _, vals = read_signal_head(paths.raw_data, filename, max_rows=5_000)
        if vals:
            data_by_signal.append(vals)
            signal_labels.append(label)

    if not data_by_signal:
        return

    fig, ax = plt.subplots(figsize=(12, 6))
    bp = ax.boxplot(data_by_signal, vert=True, patch_artist=True,
                    medianprops={"color": "black", "lw": 2})
    colours = plt.cm.Set3(np.linspace(0, 1, len(data_by_signal)))  # type: ignore[attr-defined]
    for patch, colour in zip(bp["boxes"], colours):
        patch.set_facecolor(colour)
    ax.set_xticklabels(signal_labels, rotation=30, ha="right", fontsize=9)
    ax.set_title("Value Distributions — Key EnFa Signals (sample of first 5,000 rows)")
    ax.set_ylabel("Value")
    plt.tight_layout()
    _save(fig, paths.plots / "11_value_distributions_boxplot.png")


def plot_cluster_voltages(paths: ProjectPaths, _) -> None:
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    cluster_colours = ["#1565C0", "#6A1B9A", "#2E7D32", "#BF360C"]
    fig, ax = plt.subplots(figsize=(14, 5))
    for cluster_num, colour in enumerate(cluster_colours, start=1):
        times, vals = read_signal_head(paths.raw_data, f"grealCluster_{cluster_num}_Spannung.csv", max_rows=3_000)
        if times:
            ax.plot(times, vals, lw=0.5, label=f"Cluster {cluster_num}", color=colour, alpha=0.8)
    ax.set_title("Battery Cluster Voltage — All 4 Clusters (grealCluster_1-4_Spannung)")
    ax.set_ylabel("Voltage (V)")
    ax.legend(loc="upper right", fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    plt.xticks(rotation=30)
    plt.tight_layout()
    _save(fig, paths.plots / "12_battery_cluster_voltages.png")


# ---------------------------------------------------------------------------
# Shared save helper
# ---------------------------------------------------------------------------

def _save(fig, output_path: Path) -> None:
    fig.savefig(output_path, dpi=120, bbox_inches="tight")
    fig.clf()
    import matplotlib.pyplot as plt
    plt.close(fig)
    logger.info("Saved: %s", output_path.name)


# ---------------------------------------------------------------------------
# Plot registry — add new plots here without touching main()
# ---------------------------------------------------------------------------

ALL_PLOTS = [
    plot_sampling_histogram,
    plot_category_counts,
    plot_battery_soc_history,
    plot_battery_power_recent,
    plot_pv_power_recent,
    plot_building_power_recent,
    plot_hp_defrost_history,
    plot_outdoor_temp_history,
    plot_dhw_temperature_profile,
    plot_energy_balance_recent,
    plot_value_distributions,
    plot_cluster_voltages,
]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate exploratory plots for key EnFa signals.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--raw-dir",      default=None)
    parser.add_argument("--project-root", default=None)
    return parser


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")  # non-interactive backend — must be set before pyplot import
    import matplotlib.pyplot as plt

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    args = build_arg_parser().parse_args()
    cfg = load_config()
    paths: ProjectPaths = resolve_paths(
        raw_dir=Path(args.raw_dir) if args.raw_dir else None,
        project_root=Path(args.project_root) if args.project_root else None,
        cfg=cfg,
    )
    paths.ensure_output_dirs()

    plt.rcParams.update({
        "figure.facecolor": "white",
        "axes.facecolor":   "#f8f8f8",
        "axes.grid":        True,
        "grid.alpha":       0.4,
        "font.size":        10,
        "axes.titlesize":   12,
        "axes.labelsize":   10,
    })

    logger.info("Generating %d plots into %s", len(ALL_PLOTS), paths.plots)
    for plot_fn in ALL_PLOTS:
        try:
            plot_fn(paths, None)
        except Exception as exc:
            logger.error("Plot %s failed: %s", plot_fn.__name__, exc)

    logger.info("All plots complete.")


if __name__ == "__main__":
    main()
