"""
08_generate_plots.py  —  Exploratory plots for key EnFa signals

Plots produced (all saved to reports/plots/):
  1.  sampling_interval_histogram.png   — distribution of intervals per group
  2.  signal_category_counts.png        — bar chart of signal categories
  3.  battery_soc_timeseries.png        — greal_BatterieLadeZustand full history
  4.  battery_power_timeseries.png      — real_BatterieLeistung sample week
  5.  pv_power_timeseries.png           — real_PV_Gesamt sample week (summer)
  6.  building_power_timeseries.png     — greal_LeistungGebaeude sample week
  7.  hp_defrost_timeseries.png         — greal_WP1/2/3AbtauSek sample month
  8.  outdoor_temp_timeseries.png       — grealTempAussenGefiltert full history
  9.  dhw_temp_profile.png              — warm water temps (4 height sensors) sample week
  10. energy_balance_week.png           — PV + BHKW vs building load + battery (sample week)
  11. value_distribution_boxplot.png    — value ranges for top 20 signals
  12. cluster_voltage_timeseries.png    — grealCluster_1-4_Spannung sample week
"""

import csv
import os
from datetime import datetime, timezone
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

DATA_DIR = Path("/sessions/keen-upbeat-lamport/mnt/ZE/data")
PLOTS_DIR = Path("/sessions/keen-upbeat-lamport/mnt/ZE/reports/plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

DELIM = ";"
SAMPLE_ROWS = 5000   # rows to read for time-series plots


def read_signal(signal_file: str, max_rows: int = SAMPLE_ROWS, skip_rows: int = 0):
    """Read _time and _value from a signal CSV. Returns (timestamps, values)."""
    fp = DATA_DIR / signal_file
    if not fp.exists():
        return [], []
    times, vals = [], []
    try:
        with open(fp, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.reader(f, delimiter=DELIM)
            header = next(reader, [])
            ti = next((i for i, h in enumerate(header) if "_time" in h.lower()), 1)
            vi = next((i for i, h in enumerate(header) if "_value" in h.lower()), 2)
            for n, row in enumerate(reader):
                if n < skip_rows:
                    continue
                if len(times) >= max_rows:
                    break
                try:
                    ts = row[ti].strip().replace("Z", "+00:00")
                    dt = datetime.fromisoformat(ts)
                    times.append(dt)
                    vals.append(float(row[vi]))
                except Exception:
                    pass
    except Exception:
        pass
    return times, vals


def read_signal_tail(signal_file: str, tail_bytes: int = 2_000_000, max_rows: int = SAMPLE_ROWS):
    """Read last ~tail_bytes of file for recent data."""
    fp = DATA_DIR / signal_file
    if not fp.exists():
        return [], []
    size = fp.stat().st_size
    seek = max(0, size - tail_bytes)
    times, vals = [], []
    try:
        with open(fp, "rb") as f:
            f.seek(seek)
            raw = f.read()
        lines = raw.decode("utf-8", errors="replace").splitlines()
        # Skip first (possibly partial) line
        for line in lines[1:]:
            parts = line.split(DELIM)
            if len(parts) < 3:
                continue
            try:
                ts = parts[1].strip().replace("Z", "+00:00")
                dt = datetime.fromisoformat(ts)
                times.append(dt)
                vals.append(float(parts[2]))
            except Exception:
                pass
            if len(times) >= max_rows:
                break
    except Exception:
        pass
    return times, vals


def savefig(name: str):
    path = PLOTS_DIR / name
    plt.savefig(path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {path.name}")


# ─── STYLE ────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "#f8f8f8",
    "axes.grid": True, "grid.alpha": 0.4, "font.size": 10,
    "axes.titlesize": 12, "axes.labelsize": 10,
})

print("Generating plots...")

# ─── 1. Sampling interval histogram ───────────────────────────────────────────
print("1. Sampling interval histogram")
samp_path = Path("/sessions/keen-upbeat-lamport/mnt/ZE/reports/sampling_interval_report.csv")
interval_groups = {}
try:
    with open(samp_path) as f:
        for row in csv.DictReader(f):
            lbl = row.get("interval_label", "unknown")
            try:
                med = float(row["median_interval_sec"])
                interval_groups.setdefault(lbl, []).append(med)
            except Exception:
                pass
except Exception:
    pass

fig, ax = plt.subplots(figsize=(8, 4))
labels = sorted(interval_groups.keys(), key=lambda x: (x == "unknown", x))
counts = [len(interval_groups[l]) for l in labels]
bars = ax.bar(labels, counts, color=["#2196F3","#4CAF50","#FF9800","#9C27B0","#F44336","#00BCD4","#795548"][:len(labels)])
for bar, cnt in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, str(cnt),
            ha="center", va="bottom", fontsize=9)
ax.set_title("EnFa Signal Sampling Interval Distribution (233 signals)")
ax.set_xlabel("Interval Group")
ax.set_ylabel("Number of Signals")
plt.tight_layout()
savefig("01_sampling_interval_histogram.png")

# ─── 2. Signal category bar chart ─────────────────────────────────────────────
print("2. Signal category counts")
class_path = Path("/sessions/keen-upbeat-lamport/mnt/ZE/reports/signal_classification.csv")
cat_counts = {}
try:
    with open(class_path) as f:
        for row in csv.DictReader(f):
            cat = row.get("category", "unknown")
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
except Exception:
    pass

top_cats = sorted(cat_counts.items(), key=lambda x: -x[1])[:18]
fig, ax = plt.subplots(figsize=(10, 5))
cats, cnts = zip(*top_cats)
colors = plt.cm.tab20(np.linspace(0, 1, len(cats)))
bars = ax.barh(list(reversed(cats)), list(reversed(cnts)), color=list(reversed(colors)))
ax.set_title("EnFa Signal Categories (top 18)")
ax.set_xlabel("Number of Signals")
for bar, cnt in zip(bars, list(reversed(cnts))):
    ax.text(cnt + 0.1, bar.get_y() + bar.get_height()/2, str(cnt), va="center", fontsize=8)
plt.tight_layout()
savefig("02_signal_category_counts.png")

# ─── 3. Battery SOC full history ──────────────────────────────────────────────
print("3. Battery SOC full history")
times, vals = read_signal("greal_BatterieLadeZustand.csv", max_rows=20000)
if times:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.4, color="#1976D2", alpha=0.8)
    ax.set_title("Battery State of Charge — Full History (greal_BatterieLadeZustand)")
    ax.set_ylabel("SOC (%)")
    ax.set_ylim(0, 105)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    savefig("03_battery_soc_full_history.png")

# ─── 4. Battery power — recent 2 weeks ────────────────────────────────────────
print("4. Battery power recent")
times, vals = read_signal_tail("real_BatterieLeistung.csv", tail_bytes=3_000_000, max_rows=8000)
if times:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.5, color="#E53935")
    ax.axhline(0, color="black", lw=0.8, ls="--")
    ax.set_title("Battery Power — Recent Data (real_BatterieLeistung)\n+ve = charging, -ve = discharging")
    ax.set_ylabel("Power (kW)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    savefig("04_battery_power_recent.png")

# ─── 5. PV power — recent 2 weeks ─────────────────────────────────────────────
print("5. PV power recent")
times, vals = read_signal_tail("real_PV_Gesamt.csv", tail_bytes=3_000_000, max_rows=8000)
if times:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.fill_between(times, 0, vals, alpha=0.6, color="#FBC02D")
    ax.plot(times, vals, lw=0.5, color="#F57F17")
    ax.set_title("PV Total Power — Recent Data (real_PV_Gesamt)")
    ax.set_ylabel("Power (kW)")
    ax.set_ylim(bottom=0)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    savefig("05_pv_power_recent.png")

# ─── 6. Building power — recent 2 weeks ───────────────────────────────────────
print("6. Building power recent")
times, vals = read_signal_tail("greal_LeistungGebaeude.csv", tail_bytes=3_000_000, max_rows=8000)
if times:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.5, color="#388E3C")
    ax.set_title("Building Electrical Power Demand — Recent (greal_LeistungGebaeude)")
    ax.set_ylabel("Power (kW)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    savefig("06_building_power_recent.png")

# ─── 7. HP defrost duration — all 3 units ─────────────────────────────────────
print("7. HP defrost duration")
fig, axes = plt.subplots(3, 1, figsize=(14, 8), sharex=True)
colors = ["#1565C0", "#6A1B9A", "#B71C1C"]
for idx, (unit, ax, col) in enumerate(zip(["WP1", "WP2", "WP3"], axes, colors)):
    fname = f"greal_{unit}AbtauSek.csv"
    times, vals = read_signal(fname, max_rows=15000)
    if times:
        ax.plot(times, vals, lw=0.4, color=col, alpha=0.8)
        ax.set_ylabel(f"{unit}\n(s)", fontsize=9)
        ax.set_ylim(bottom=0)
axes[0].set_title("Heat Pump Defrost Duration — All 3 Units (greal_WP1/2/3AbtauSek)")
axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
axes[-1].xaxis.set_major_locator(mdates.MonthLocator(interval=3))
plt.xticks(rotation=30)
plt.tight_layout()
savefig("07_hp_defrost_all_units.png")

# ─── 8. Outdoor temperature full history ──────────────────────────────────────
print("8. Outdoor temp full history")
times, vals = read_signal("grealTempAussenGefiltert.csv", max_rows=20000)
if times:
    fig, ax = plt.subplots(figsize=(14, 4))
    ax.plot(times, vals, lw=0.4, color="#0288D1", alpha=0.8)
    ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.5)
    ax.set_title("Outdoor Temperature — Full History (grealTempAussenGefiltert)")
    ax.set_ylabel("Temperature (°C)")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=30)
    plt.tight_layout()
    savefig("08_outdoor_temp_full_history.png")

# ─── 9. DHW warm water temperature profile (4 sensors) ────────────────────────
print("9. DHW temperature profile")
sensors = [
    ("realIstTempWarmWasOben.csv",     "Top",         "#D32F2F"),
    ("realIstTempWarmWasObenMitte.csv","Upper-middle","#E64A19"),
    ("realIstTempWarmWasUntMitte.csv", "Lower-middle","#F57C00"),
    ("realIstTempWarmWasUnt.csv",      "Bottom",      "#FBC02D"),
]
fig, ax = plt.subplots(figsize=(14, 5))
for fname, label, col in sensors:
    times, vals = read_signal(fname, max_rows=3000)
    if times:
        ax.plot(times, vals, lw=0.8, label=label, color=col, alpha=0.85)
ax.set_title("DHW Warm Water Storage Temperature Profile — 4 Height Sensors")
ax.set_ylabel("Temperature (°C)")
ax.legend(loc="upper right", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=30)
plt.tight_layout()
savefig("09_dhw_warm_water_profile.png")

# ─── 10. Energy balance — PV vs building load (recent sample) ─────────────────
print("10. Energy balance recent")
sig_map = {
    "PV Power": ("real_PV_Gesamt.csv", "#FBC02D"),
    "Building Demand": ("greal_LeistungGebaeude.csv", "#388E3C"),
    "Battery Power": ("real_BatterieLeistung.csv", "#1976D2"),
    "BHKW Power": ("real_P_BHKW.csv", "#E53935"),
}
fig, ax = plt.subplots(figsize=(14, 5))
for label, (fname, col) in sig_map.items():
    times, vals = read_signal_tail(fname, tail_bytes=1_500_000, max_rows=3000)
    if times:
        ax.plot(times, vals, lw=0.7, label=label, color=col, alpha=0.85)
ax.axhline(0, color="black", lw=0.6, ls="--", alpha=0.4)
ax.set_title("Energy Balance — Recent Data (PV, Building Demand, Battery, BHKW)")
ax.set_ylabel("Power (kW)")
ax.legend(loc="upper right", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
plt.xticks(rotation=30)
plt.tight_layout()
savefig("10_energy_balance_recent.png")

# ─── 11. Value distribution boxplot (top signals) ─────────────────────────────
print("11. Value distributions boxplot")
box_signals = [
    ("greal_BatterieLadeZustand.csv", "Battery SOC (%)"),
    ("real_BatterieLeistung.csv",     "Battery Power (kW)"),
    ("real_PV_Gesamt.csv",            "PV Power (kW)"),
    ("greal_LeistungGebaeude.csv",    "Building Power (kW)"),
    ("real_P_BHKW.csv",               "BHKW Power (kW)"),
    ("grealTempAussenGefiltert.csv",  "Outdoor Temp (C)"),
    ("grealIstWaermepumpVorlauf.csv", "HP Supply Temp (C)"),
    ("greal_W_WMZ_P_WP.csv",          "HP Thermal Power (kW)"),
    ("realIstTempWarmWasOben.csv",     "DHW Top Temp (C)"),
]
data_boxes, labels_boxes = [], []
for fname, label in box_signals:
    _, vals = read_signal(fname, max_rows=5000)
    if vals:
        data_boxes.append(vals)
        labels_boxes.append(label)

if data_boxes:
    fig, ax = plt.subplots(figsize=(12, 6))
    bp = ax.boxplot(data_boxes, vert=True, patch_artist=True,
                    medianprops=dict(color="black", lw=2))
    colors_box = plt.cm.Set3(np.linspace(0, 1, len(data_boxes)))
    for patch, col in zip(bp["boxes"], colors_box):
        patch.set_facecolor(col)
    ax.set_xticklabels(labels_boxes, rotation=30, ha="right", fontsize=9)
    ax.set_title("Value Distributions — Key EnFa Signals (sample of first 5,000 rows)")
    ax.set_ylabel("Value")
    plt.tight_layout()
    savefig("11_value_distributions_boxplot.png")

# ─── 12. Battery cluster voltages ─────────────────────────────────────────────
print("12. Battery cluster voltages")
fig, ax = plt.subplots(figsize=(14, 5))
colors_cl = ["#1565C0", "#6A1B9A", "#2E7D32", "#BF360C"]
for i in range(1, 5):
    fname = f"grealCluster_{i}_Spannung.csv"
    times, vals = read_signal(fname, max_rows=3000)
    if times:
        ax.plot(times, vals, lw=0.5, label=f"Cluster {i}", color=colors_cl[i-1], alpha=0.8)
ax.set_title("Battery Cluster Voltage — All 4 Clusters (grealCluster_1-4_Spannung)")
ax.set_ylabel("Voltage (V)")
ax.legend(loc="upper right", fontsize=9)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
plt.xticks(rotation=30)
plt.tight_layout()
savefig("12_battery_cluster_voltages.png")

print(f"\nAll plots saved to: {PLOTS_DIR}")
print("Done.")
