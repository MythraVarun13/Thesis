"""Generate notebooks/05_signal_profile_explorer.ipynb and notebooks/06_full_eda.ipynb."""
from pathlib import Path
import nbformat
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

ROOT   = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"

md   = new_markdown_cell
code = new_code_cell


# ---------------------------------------------------------------------------
# Notebook 05 - Signal Profile Explorer
# ---------------------------------------------------------------------------

NB05_CELLS = [

    # Cell 0 - title
    ("md", """\
# 05 - Signal Profile Explorer

**Purpose:** Interactively explore signal quality profiles produced by `scripts/06_signal_profiles.py`.

Drill into one signal or one category at a time using DuckDB - no need to load 40 GB into memory.

**Requires:** `reports/signal_quality_profiles.csv`
Run first: `python scripts/06_signal_profiles.py --threads 6`  (60-120 min)

**How to use:**
- Change `CATEGORY` in Section 3 and re-run that cell to browse a signal group
- Change `SIGNAL` in Section 4 and re-run to deep-dive any individual signal
- Change `COMPARE_SIGNALS` in Section 5 to overlay multiple signals on one chart
"""),

    # Cell 1 - imports
    ("code", """\
import sys
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths

cfg   = load_config()
paths = resolve_paths(cfg=cfg)

sns.set_theme(style="whitegrid", palette="tab10")
print(f"Project root: {paths.root}")
print(f"Raw data:     {paths.raw_data}")
print(f"Reports:      {paths.reports}")
"""),

    # Cell 2 - load profiles
    ("code", """\
profiles_path = paths.reports / "signal_quality_profiles.csv"

if not profiles_path.exists():
    print("ERROR: signal_quality_profiles.csv not found.")
    print("Run:  python scripts/06_signal_profiles.py --threads 6")
    print("Expected runtime: 60-120 minutes on 40 GB.")
    raise FileNotFoundError(profiles_path)

profiles = pd.read_csv(profiles_path)
ok = profiles[profiles["notes"] == "ok"].copy()
print(f"Loaded {len(profiles)} signals  |  {len(ok)} profiled successfully")
print(f"Categories: {ok['category'].nunique()}")
print()
print(ok[["signal_name", "category", "row_count", "gap_ratio", "outlier_count"]].head(10).to_string(index=False))
"""),

    # Cell 3 - section header
    ("md", "## 1. Dataset-wide quality overview"),

    # Cell 4 - overview charts
    ("code", """\
fig, axes = plt.subplots(1, 2, figsize=(16, 5))

# Signal count by category
cat_counts = ok["category"].value_counts().head(20)
axes[0].barh(cat_counts.index[::-1], cat_counts.values[::-1])
axes[0].set_xlabel("Signal count")
axes[0].set_title("Signals per category (top 20)")

# Gap ratio distribution
axes[1].hist(ok["gap_ratio"], bins=40, edgecolor="white")
axes[1].axvline(0.10, color="red", linestyle="--", label="10% threshold")
axes[1].set_xlabel("Gap ratio  (0=complete, 1=empty)")
axes[1].set_ylabel("Number of signals")
axes[1].set_title("Data completeness distribution")
axes[1].legend()

plt.tight_layout()
plt.savefig(paths.plots / "05_quality_overview.png", dpi=150, bbox_inches="tight")
plt.show()
"""),

    # Cell 5
    ("md", "## 2. Problem signals flagged"),

    # Cell 6 - problem signals
    ("code", """\
high_gap      = ok[ok["gap_ratio"] > 0.10].sort_values("gap_ratio", ascending=False)
high_outliers = ok[ok["outlier_count"] > 5000].sort_values("outlier_count", ascending=False)
has_nulls     = ok[ok["null_count"] > 0]

print(f"=== High gap (>10%): {len(high_gap)} signals ===")
if len(high_gap):
    print(high_gap[["signal_name", "category", "gap_ratio", "row_count", "duration_days"]].to_string(index=False))

print(f"\\n=== High outlier count (>5000): {len(high_outliers)} signals ===")
if len(high_outliers):
    print(high_outliers[["signal_name", "category", "outlier_count", "val_min", "val_max"]].to_string(index=False))

print(f"\\n=== Has null values: {len(has_nulls)} signals ===")
if len(has_nulls):
    print(has_nulls[["signal_name", "null_count"]].to_string(index=False))
"""),

    # Cell 7
    ("md", """\
## 3. Browse by category

Change `CATEGORY` below and re-run this cell to explore any signal group.

Available examples: `hp_defrost`, `hp_energy`, `thermal_energy`, `battery_soc`,
`outdoor_temp`, `pv_energy`, `heating_curve`, `hp_setpoint`, `battery_voltage`
"""),

    # Cell 8 - category browser
    ("code", """\
# -- Change this to explore a different category --
CATEGORY = "hp_defrost"
# --------------------------------------------------

subset = ok[ok["category"] == CATEGORY].sort_values("signal_name")

if subset.empty:
    print(f"No signals found for category: {CATEGORY!r}")
    print(f"Available categories: {sorted(ok['category'].unique())}")
else:
    print(f"Category '{CATEGORY}' -- {len(subset)} signals\\n")
    cols = ["signal_name", "row_count", "val_min", "val_max",
            "val_mean", "val_std", "p50", "gap_ratio", "duration_days"]
    print(subset[cols].to_string(index=False))

    if len(subset) > 1:
        fig, ax = plt.subplots(figsize=(10, max(3, len(subset) * 0.4)))
        ax.boxplot(
            [ok[ok["signal_name"] == sig]["val_mean"].values for sig in subset["signal_name"]],
            labels=subset["signal_name"].tolist(),
            vert=False,
        )
        ax.set_title(f"Mean value distribution -- {CATEGORY}")
        plt.tight_layout()
        plt.show()
"""),

    # Cell 9
    ("md", """\
## 4. Deep-dive one signal

Change `SIGNAL` below and re-run. DuckDB reads the full raw CSV directly -- returns hourly means in seconds.
"""),

    # Cell 10 - deep-dive (uses f''' to avoid triple-quote collision)
    ("code", """\
# -- Change this to deep-dive any signal --
SIGNAL = "greal_WP1AbtauSek"
# ------------------------------------------

csv_path = paths.raw_data / f"{SIGNAL}.csv"

if not csv_path.exists():
    print(f"File not found: {csv_path}")
else:
    meta = ok[ok["signal_name"] == SIGNAL]
    if not meta.empty:
        m = meta.iloc[0]
        print(f"Signal:   {SIGNAL}")
        print(f"Category: {m['category']}  |  Rows: {m['row_count']:,}  |  Gap: {m['gap_ratio']:.1%}")
        print(f"Range:    {m['val_min']} to {m['val_max']}  |  Mean: {m['val_mean']:.3f}  |  Std: {m['val_std']:.3f}")
        print(f"Coverage: {m['start_time']} to {m['end_time']}  ({m['duration_days']:.0f} days)\\n")

    path_str = csv_path.as_posix()
    df = duckdb.sql(f'''
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
            AVG(TRY_CAST(_value AS DOUBLE))                     AS value
        FROM read_csv(
            '{path_str}',
            delim=';', header=true, ignore_errors=true,
            columns={{'_time': 'VARCHAR', '_value': 'VARCHAR',
                      '_field': 'VARCHAR', '_measurement': 'VARCHAR'}}
        )
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    ''').df()

    df["hour_utc"] = pd.to_datetime(df["hour_utc"], utc=True)

    fig, ax = plt.subplots(figsize=(16, 4))
    ax.plot(df["hour_utc"], df["value"], linewidth=0.6, color="steelblue")
    ax.set_title(f"{SIGNAL}  (hourly mean, full dataset)")
    ax.set_ylabel("Value")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / f"05_deep_dive_{SIGNAL}.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Cell 11
    ("md", """\
## 5. Compare signals within a category

Change `COMPARE_SIGNALS` to overlay related signals. Useful for WP1/WP2/WP3 or battery clusters 1-4.
"""),

    # Cell 12 - compare
    ("code", """\
# -- Change these to compare signals --
COMPARE_SIGNALS = [
    "greal_WP1AbtauSek",
    "greal_WP2AbtauSek",
    "greal_WP3AbtauSek",
]
RESAMPLE_FREQ = "W"   # "D"=daily, "W"=weekly, "ME"=monthly
AGG_FUNC      = "sum" # "mean" or "sum"
# --------------------------------------

COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
fig, ax = plt.subplots(figsize=(16, 5))

for i, sig in enumerate(COMPARE_SIGNALS):
    csv_path = paths.raw_data / f"{sig}.csv"
    if not csv_path.exists():
        print(f"  Missing: {csv_path.name}")
        continue

    path_str = csv_path.as_posix()
    df = duckdb.sql(f'''
        SELECT
            DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
            SUM(TRY_CAST(_value AS DOUBLE))                     AS value
        FROM read_csv(
            '{path_str}',
            delim=';', header=true, ignore_errors=true,
            columns={{'_time': 'VARCHAR', '_value': 'VARCHAR',
                      '_field': 'VARCHAR', '_measurement': 'VARCHAR'}}
        )
        WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
        GROUP BY 1 ORDER BY 1
    ''').df()

    if df.empty:
        continue

    df["hour_utc"] = pd.to_datetime(df["hour_utc"], utc=True)
    series = df.set_index("hour_utc")["value"]
    resampled = series.resample(RESAMPLE_FREQ).sum() if AGG_FUNC == "sum" else series.resample(RESAMPLE_FREQ).mean()
    ax.plot(resampled.index, resampled.values, label=sig, color=COLORS[i % len(COLORS)], linewidth=1.2)

ax.set_title(f"Signal comparison ({RESAMPLE_FREQ} {AGG_FUNC})")
ax.set_ylabel("Value")
ax.legend()
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
plt.xticks(rotation=30)
plt.tight_layout()
plt.savefig(paths.plots / "05_signal_comparison.png", dpi=150, bbox_inches="tight")
plt.show()
"""),

    # Cell 13
    ("md", "## 6. Notes and decisions"),

    # Cell 14 - notes
    ("code", """\
# Edit FINDINGS below, then run this cell to append to the data quality context file.
FINDINGS = \"\"\"
Session findings -- Signal Profile Explorer:
- (replace with your observations after exploring profiles)
- e.g. WP2 has higher gap ratio than WP1/WP3
- e.g. greal_E_WP shows expected monotone-increasing counter behaviour
\"\"\"

quality_ctx = paths.context / "data_quality_context.md"
with open(quality_ctx, "a", encoding="utf-8") as fh:
    fh.write(f"\\n{FINDINGS.strip()}\\n")
print(f"Appended to: {quality_ctx}")
"""),

]  # end NB05_CELLS


# ---------------------------------------------------------------------------
# Notebook 06 - Full EDA (all systems)
# ---------------------------------------------------------------------------

NB06_CELLS = [

    ("md", """\
# 06 - Full EDA: All Systems

**Purpose:** Deep analysis of all 11 EnFa subsystems using the hourly-resampled Parquet dataset.

**Requires:** `data/processed/hourly.parquet`
Run first: `python scripts/07_resample_hourly.py --threads 6`  (30-60 min)

**North star:** MPC. Every section characterises a component of the MPC system:
states (temperatures, SOC), controls (setpoints, dispatch), disturbances (weather, PV), constraints (limits).

**Section 2 HP COP chart is the first customer deliverable.**
"""),

    # Setup - imports
    ("code", """\
import sys
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths

cfg   = load_config()
paths = resolve_paths(cfg=cfg)

sns.set_theme(style="whitegrid", palette="tab10")
COLORS = plt.rcParams["axes.prop_cycle"].by_key()["color"]
print(f"Project root: {paths.root}")
"""),

    # Setup - load parquet
    ("code", """\
parquet_path = paths.processed / "hourly.parquet"

if not parquet_path.exists():
    print("ERROR: hourly.parquet not found.")
    print("Run:  python scripts/07_resample_hourly.py --threads 6")
    print("Expected runtime: 30-60 minutes.")
    raise FileNotFoundError(parquet_path)

df = pd.read_parquet(parquet_path)
print(f"Loaded: {df.shape[0]:,} rows x {df.shape[1]} columns")
print(f"UTC range: {df.index.min()} -> {df.index.max()}")
print(f"Memory: {df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print()
print("First 20 columns:")
for col in sorted(df.columns)[:20]:
    print(f"  {col:<50}  {df[col].notna().sum():>8,} non-null")
"""),

    # Setup - timezone
    ("code", """\
# UTC for time-series; Europe/Berlin for daily profiles and occupancy charts
df_utc   = df.copy()
df_local = df.copy()
df_local.index = df_local.index.tz_convert("Europe/Berlin")
print("df_utc   -- UTC timestamps  -- use for time-series and energy totals")
print("df_local -- Europe/Berlin   -- use for daily profiles and heatmaps")
"""),

    # Section 1 header
    ("md", "## 1. Energy Overview (whole building, 3.5 years)"),

    # 1a - 4-panel overview
    ("code", """\
fig, axes = plt.subplots(4, 1, figsize=(18, 12), sharex=True)

panels = [
    ("grealTempAussenGefiltert", "Outdoor temperature",      "C",  COLORS[0]),
    ("greal_LeistungGebaeude",   "Building demand",          "kW", COLORS[1]),
    ("real_PV_Gesamt",           "PV total power",           "kW", COLORS[3]),
    ("greal_BatterieLadeZustand","Battery SOC",               "%", COLORS[2]),
]

for ax, (col, label, unit, color) in zip(axes, panels):
    if col not in df_utc.columns:
        ax.text(0.5, 0.5, f"{col} not in dataset", ha="center", va="center",
                transform=ax.transAxes, color="grey")
        ax.set_ylabel(label)
        continue
    series = df_utc[col].resample("D").mean()
    ax.plot(series.index, series.values, linewidth=0.7, color=color)
    ax.set_ylabel(f"{label} ({unit})")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

axes[-1].tick_params(axis="x", rotation=30)
fig.suptitle("EnFa -- 3.5-year energy system overview (daily mean)", fontsize=13)
plt.tight_layout()
out = paths.plots / "06_01_energy_overview.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {out}")
"""),

    # 1b - self-sufficiency
    ("code", """\
gen_cols   = [c for c in ["real_PV_Gesamt", "real_P_BHKW"] if c in df_utc.columns]
demand_col = "greal_LeistungGebaeude"
monthly    = df_utc.resample("ME").mean()

fig, axes = plt.subplots(1, 2, figsize=(16, 5))

if gen_cols:
    monthly[gen_cols].plot(kind="bar", stacked=True, ax=axes[0], width=0.8)
    axes[0].set_title("Monthly mean generation (kW avg)")
    axes[0].tick_params(axis="x", rotation=45)
    axes[0].set_xlabel("")

if gen_cols and demand_col in df_utc.columns:
    self_suff  = (df_utc[gen_cols].sum(axis=1) / df_utc[demand_col].replace(0, np.nan)).clip(0, 1)
    monthly_ss = self_suff.resample("ME").mean() * 100
    axes[1].bar(range(len(monthly_ss)), monthly_ss.values, color=COLORS[3])
    axes[1].set_xticks(range(len(monthly_ss)))
    axes[1].set_xticklabels([str(d)[:7] for d in monthly_ss.index], rotation=45)
    axes[1].set_ylabel("Self-sufficiency (%)")
    axes[1].set_title("Monthly energy self-sufficiency (PV + BHKW / building demand)")
    axes[1].axhline(100, color="red", linestyle="--", linewidth=0.8)

plt.tight_layout()
out = paths.plots / "06_01_energy_balance.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {out}")
"""),

    # Section 2 header
    ("md", """\
## 2. Heat Pump System (WP1 / WP2 / WP3)

MPC role: states = supply/return temp; controls = HP on/off, setpoint; disturbance = outdoor temp

### HP COP -- Customer Deliverable

COP = heat energy generated / electrical energy consumed.
`script 07` applied MAX-MIN aggregation, so hourly.parquet values are kWh *in that hour* (not running totals).
"""),

    # 2a - HP COP trend
    ("code", """\
heat_col = "greal_WMZ_Hz_Erz_WP"
elec_col = "greal_E_WP"

if heat_col in df_utc.columns and elec_col in df_utc.columns:
    daily_heat = df_utc[heat_col].resample("D").sum()
    daily_elec = df_utc[elec_col].resample("D").sum()
    daily_cop  = (daily_heat / daily_elec.replace(0, np.nan)).clip(0, 8)
    cop_14d    = daily_cop.rolling(14, min_periods=7).mean()

    fig, ax = plt.subplots(figsize=(16, 5))
    ax.scatter(daily_cop.index, daily_cop.values, s=3, alpha=0.4, color=COLORS[0], label="Daily COP")
    ax.plot(cop_14d.index, cop_14d.values, linewidth=2, color=COLORS[1], label="14-day rolling mean")
    ax.axhline(3.0, color="red",    linestyle="--", linewidth=0.8, label="COP=3.0 (benchmark)")
    ax.axhline(2.0, color="orange", linestyle="--", linewidth=0.8, label="COP=2.0 (low)")
    ax.set_ylabel("COP (heat out / electricity in)")
    ax.set_title("Heat Pump COP -- 3.5-year performance trend  |  EnFa building")
    ax.legend(loc="upper right")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / "06_02_hp_cop_trend.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
    print(f"Mean COP: {daily_cop.mean():.2f}  |  Median: {daily_cop.median():.2f}")
else:
    print(f"Missing signals: {heat_col} or {elec_col}")
"""),

    # 2b - COP vs outdoor temp
    ("code", """\
at_col = "grealTempAussenGefiltert"

if heat_col in df_utc.columns and elec_col in df_utc.columns and at_col in df_utc.columns:
    daily_at  = df_utc[at_col].resample("D").mean()
    scatter   = pd.DataFrame({"cop": daily_cop, "outdoor_temp": daily_at}).dropna()
    scatter["season"] = scatter.index.month.map(
        {12:"Winter",1:"Winter",2:"Winter",3:"Spring",4:"Spring",5:"Spring",
         6:"Summer",7:"Summer",8:"Summer",9:"Autumn",10:"Autumn",11:"Autumn"}
    )
    season_colors = {"Winter": COLORS[0], "Spring": COLORS[2], "Summer": COLORS[3], "Autumn": COLORS[1]}

    fig, ax = plt.subplots(figsize=(10, 6))
    for season, grp in scatter.groupby("season"):
        ax.scatter(grp["outdoor_temp"], grp["cop"], s=8, alpha=0.5,
                   color=season_colors[season], label=season)
    ax.set_xlabel("Outdoor temperature (C)")
    ax.set_ylabel("Daily COP")
    ax.set_title("HP COP vs Outdoor Temperature  (coloured by season)")
    ax.legend()
    plt.tight_layout()
    out = paths.plots / "06_02_hp_cop_scatter.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # 2c - defrost per unit
    ("code", """\
defrost = {"WP1": "greal_WP1AbtauSek", "WP2": "greal_WP2AbtauSek", "WP3": "greal_WP3AbtauSek"}
avail   = {k: v for k, v in defrost.items() if v in df_utc.columns}

if avail:
    fig, axes = plt.subplots(len(avail), 1, figsize=(16, 3 * len(avail)), sharex=True)
    if len(avail) == 1:
        axes = [axes]

    for ax, (unit, col) in zip(axes, avail.items()):
        weekly = df_utc[col].resample("W").sum() / 3600  # seconds -> hours
        ax.bar(weekly.index, weekly.values, width=5, color=COLORS[list(avail.keys()).index(unit)])
        ax.set_ylabel("Defrost (h/week)")
        ax.set_title(f"{unit} -- weekly defrost duration")

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / "06_02_defrost_per_unit.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Section 3
    ("md", "## 3. Battery System (4 clusters)"),

    ("code", """\
soc_col = "greal_BatterieLadeZustand"
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

if soc_col in df_utc.columns:
    soc = df_utc[soc_col].dropna()
    axes[0].hist(soc.values, bins=50, edgecolor="white", color=COLORS[2])
    axes[0].set_xlabel("Battery SOC (%)")
    axes[0].set_ylabel("Hours")
    axes[0].set_title("Battery SOC histogram (3.5 years)")
    axes[0].axvline(soc.mean(), color="red", linestyle="--", label=f"Mean={soc.mean():.1f}%")
    axes[0].legend()

    daily_range  = df_utc[soc_col].resample("D").max() - df_utc[soc_col].resample("D").min()
    monthly_dep  = daily_range.resample("ME").mean()
    axes[1].bar(range(len(monthly_dep)), monthly_dep.values, color=COLORS[2])
    axes[1].set_xticks(range(len(monthly_dep)))
    axes[1].set_xticklabels([str(d)[:7] for d in monthly_dep.index], rotation=45)
    axes[1].set_ylabel("Daily SOC swing (%)")
    axes[1].set_title("Average daily battery cycling depth by month")

plt.tight_layout()
out = paths.plots / "06_03_battery_soc.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {out}")
"""),

    ("code", """\
cluster_v = {f"Cluster {i}": f"grealCluster_{i}_Spannung" for i in range(1, 5)}
avail_v   = {k: v for k, v in cluster_v.items() if v in df_utc.columns}

if avail_v:
    fig, ax = plt.subplots(figsize=(16, 5))
    for i, (label, col) in enumerate(avail_v.items()):
        monthly_v = df_utc[col].resample("ME").mean()
        ax.plot(monthly_v.index, monthly_v.values, label=label, linewidth=1.5, color=COLORS[i])
    ax.set_ylabel("Voltage (V)")
    ax.set_title("Battery cluster voltage (monthly mean) -- divergence signals cell imbalance")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / "06_03_cluster_voltage.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Section 4
    ("md", "## 4. PV System"),

    ("code", """\
pv_col = "real_PV_Gesamt"

if pv_col in df_utc.columns:
    monthly_pv = df_utc[pv_col].resample("ME").sum()
    zero_pct   = (df_utc[pv_col] == 0).resample("ME").mean() * 100

    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    axes[0].bar(range(len(monthly_pv)), monthly_pv.values, color=COLORS[3])
    axes[0].set_xticks(range(len(monthly_pv)))
    axes[0].set_xticklabels([str(d)[:7] for d in monthly_pv.index], rotation=45)
    axes[0].set_ylabel("PV generation (kWh/month)")
    axes[0].set_title("Monthly PV generation")

    axes[1].plot(zero_pct.index, zero_pct.values, color=COLORS[3], linewidth=1.5)
    axes[1].set_ylabel("Hours with zero PV (%)")
    axes[1].set_title("Zero-generation % by month (seasonal night/cloud pattern)")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)

    plt.tight_layout()
    out = paths.plots / "06_04_pv_generation.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Section 5
    ("md", "## 5. BHKW / CHP"),

    ("code", """\
bhkw_pow = "real_P_BHKW"
bhkw_gas = "greal_Gas_bhkwges"

if bhkw_pow in df_utc.columns and bhkw_gas in df_utc.columns:
    daily_elec = df_utc[bhkw_pow].resample("D").sum()
    daily_gas  = df_utc[bhkw_gas].resample("D").sum()
    efficiency = (daily_elec / daily_gas.replace(0, np.nan)).clip(0, 1)

    fig, axes = plt.subplots(2, 1, figsize=(16, 8), sharex=True)
    weekly_elec = daily_elec.resample("W").mean()
    axes[0].plot(weekly_elec.index, weekly_elec.values, color=COLORS[4], linewidth=1)
    axes[0].set_ylabel("BHKW electrical output (kWh/day)")
    axes[0].set_title("BHKW / CHP -- weekly electrical output")

    monthly_eff = efficiency.resample("ME").mean()
    axes[1].plot(monthly_eff.index, monthly_eff.values, color=COLORS[5], linewidth=1.5)
    axes[1].set_ylabel("Electrical efficiency")
    axes[1].set_title("BHKW electrical efficiency (monthly mean)")
    axes[1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)

    plt.tight_layout()
    out = paths.plots / "06_05_bhkw.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
else:
    print(f"BHKW signals not found: {bhkw_pow}, {bhkw_gas}")
"""),

    # Section 6
    ("md", "## 6. Thermal Distribution (underfloor heating zones + DHW)"),

    ("code", """\
zone_signals = {
    "FBH Nord":  ("greal_K_WMZ_TV_Nord",  "greal_K_WMZ_TR_Nord"),
    "FBH Sued":  ("greal_K_WMZ_TV_Sued",  "greal_K_WMZ_TR_Sued"),
    "FBH Halle": ("greal_K_WMZ_TV_Halle", "greal_K_WMZ_TR_Halle"),
}
avail_zones = {k: v for k, v in zone_signals.items()
               if any(s in df_utc.columns for s in v)}

if avail_zones:
    fig, axes = plt.subplots(len(avail_zones), 1,
                             figsize=(16, 4 * len(avail_zones)), sharex=True)
    if len(avail_zones) == 1:
        axes = [axes]

    for ax, (zone, (tv, tr)) in zip(axes, avail_zones.items()):
        if tv in df_utc.columns:
            ax.plot(df_utc[tv].resample("W").mean().index,
                    df_utc[tv].resample("W").mean().values, label="Supply (VL)", color=COLORS[1])
        if tr in df_utc.columns:
            ax.plot(df_utc[tr].resample("W").mean().index,
                    df_utc[tr].resample("W").mean().values, label="Return (RL)", color=COLORS[0])
        ax.set_ylabel("C")
        ax.set_title(f"{zone} -- supply and return temperature (weekly mean)")
        ax.legend()

    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / "06_06_thermal_zones.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
else:
    print("Zone temperature signals not found -- check signal names in signal_classification.csv")
"""),

    # Section 7
    ("md", "## 7. Controls and Setpoints"),

    ("code", """\
day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Night setback heatmap
setback_col = "greal_Nachtabsenkung"
if setback_col in df_local.columns:
    sb = df_local[setback_col].dropna()
    piv = pd.DataFrame({"hour": sb.index.hour, "weekday": sb.index.dayofweek,
                         "active": (sb > 0).astype(int).values})
    hm = piv.groupby(["weekday", "hour"])["active"].mean().unstack()

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(hm, cmap="YlOrRd", ax=ax, xticklabels=range(24), yticklabels=day_labels)
    ax.set_xlabel("Hour of day (Europe/Berlin)")
    ax.set_title("Night setback activation rate -- fraction of time active (3.5 years)")
    plt.tight_layout()
    out = paths.plots / "06_07_night_setback_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")

# High-tariff flag heatmap
ht_col = "greal_Administrator_HT"
if ht_col in df_local.columns:
    ht = df_local[ht_col].dropna()
    piv = pd.DataFrame({"hour": ht.index.hour, "weekday": ht.index.dayofweek,
                         "active": (ht > 0).astype(int).values})
    hm = piv.groupby(["weekday", "hour"])["active"].mean().unstack()

    fig, ax = plt.subplots(figsize=(14, 5))
    sns.heatmap(hm, cmap="Blues", ax=ax, xticklabels=range(24), yticklabels=day_labels)
    ax.set_xlabel("Hour of day (Europe/Berlin)")
    ax.set_title("High-tariff (HT) flag activation rate -- demand-shift control pattern")
    plt.tight_layout()
    out = paths.plots / "06_07_ht_flag_heatmap.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Section 8
    ("md", "## 8. EV Charging"),

    ("code", """\
ev_candidates = [c for c in df_utc.columns if any(k in c.lower() for k in ["ev", "wallbox", "ladepunkt"])]
print(f"EV-related columns: {ev_candidates if ev_candidates else 'none found'}")

if ev_candidates:
    fig, ax = plt.subplots(figsize=(14, 4))
    for i, col in enumerate(ev_candidates[:4]):
        monthly = df_utc[col].resample("ME").mean()
        ax.plot(monthly.index, monthly.values, label=col, color=COLORS[i])
    ax.set_ylabel("Value")
    ax.set_title("EV charging signals (monthly mean)")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    plt.xticks(rotation=30)
    plt.tight_layout()
    out = paths.plots / "06_08_ev_charging.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    # Section 9
    ("md", "## 9. Weather and Forecasts"),

    ("code", """\
fig, axes = plt.subplots(2, 2, figsize=(16, 8))

at_col   = "grealTempAussenGefiltert"
wind_col = "wind_now"
sun_alt  = "sun_alt"

if at_col in df_utc.columns:
    daily = df_utc[at_col].resample("D").mean()
    axes[0, 0].plot(daily.index, daily.values, linewidth=0.7, color=COLORS[0])
    axes[0, 0].set_title("Outdoor temperature -- full 3.5 years (daily mean)")
    axes[0, 0].set_ylabel("C")
    axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

if wind_col in df_utc.columns:
    weekly = df_utc[wind_col].resample("W").mean()
    axes[0, 1].plot(weekly.index, weekly.values, linewidth=0.8, color=COLORS[4])
    axes[0, 1].set_title("Wind speed (weekly mean)")
    axes[0, 1].set_ylabel("m/s")
    axes[0, 1].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

if sun_alt in df_utc.columns:
    monthly_sun = df_utc[sun_alt].resample("ME").mean()
    axes[1, 0].plot(monthly_sun.index, monthly_sun.values, color=COLORS[3])
    axes[1, 0].set_title("Solar altitude (monthly mean) -- seasonal geometry")
    axes[1, 0].set_ylabel("Degrees")
    axes[1, 0].xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))

if "wind_tomorrow" in df_utc.columns and wind_col in df_utc.columns:
    d_now  = df_utc[wind_col].resample("D").mean()
    d_fore = df_utc["wind_tomorrow"].resample("D").mean().shift(-1)
    comb   = pd.DataFrame({"actual": d_now, "forecast": d_fore}).dropna()
    axes[1, 1].scatter(comb["actual"], comb["forecast"], s=3, alpha=0.3, color=COLORS[5])
    vmax = comb.max().max()
    axes[1, 1].plot([0, vmax], [0, vmax], "r--", linewidth=0.8, label="Perfect forecast")
    axes[1, 1].set_xlabel("wind_now (actual)")
    axes[1, 1].set_ylabel("wind_tomorrow (forecast)")
    axes[1, 1].set_title("Wind forecast accuracy")
    axes[1, 1].legend()

for ax in axes.flat:
    for tick in ax.get_xticklabels():
        tick.set_rotation(30)

plt.tight_layout()
out = paths.plots / "06_09_weather.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {out}")
"""),

    # Section 10
    ("md", "## 10. Correlations"),

    ("code", """\
top_signals = [
    "grealTempAussenGefiltert", "greal_LeistungGebaeude", "real_PV_Gesamt",
    "greal_BatterieLadeZustand", "real_BatterieLeistung",
    "grealIstWaermepumpVorlauf", "greal_WP1AbtauSek", "greal_WP2AbtauSek", "greal_WP3AbtauSek",
    "greal_E_WP", "greal_WMZ_Hz_Erz_WP",
    "real_P_BHKW", "greal_Gas_bhkwges",
    "grealCluster_1_Spannung", "grealCluster_2_Spannung",
    "greal_Nachtabsenkung", "greal_Administrator_HT",
]
avail_top = [c for c in top_signals if c in df_utc.columns]
print(f"Using {len(avail_top)} signals for correlation analysis")

corr_df = df_utc[avail_top].resample("D").mean().corr()

fig, ax = plt.subplots(figsize=(14, 11))
mask = np.triu(np.ones_like(corr_df, dtype=bool))
sns.heatmap(corr_df, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
            center=0, vmin=-1, vmax=1, ax=ax, annot_kws={"size": 7})
ax.set_title("Correlation matrix -- top EnFa signals (daily mean)")
plt.tight_layout()
out = paths.plots / "06_10_correlations.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.show()
print(f"Saved: {out}")
"""),

    # Section 11
    ("md", "## 11. Seasonal Load Profiles"),

    ("code", """\
demand_col = "greal_LeistungGebaeude"

if demand_col in df_local.columns:
    local = df_local[demand_col]
    season_mask = {
        "Winter (Dec-Feb)": local.index.month.isin([12, 1, 2]),
        "Spring (Mar-May)": local.index.month.isin([3, 4, 5]),
        "Summer (Jun-Aug)": local.index.month.isin([6, 7, 8]),
        "Autumn (Sep-Nov)": local.index.month.isin([9, 10, 11]),
    }

    fig, ax = plt.subplots(figsize=(12, 5))
    for season, mask in season_mask.items():
        profile = local[mask].groupby(local[mask].index.hour).mean()
        ax.plot(profile.index, profile.values, label=season, linewidth=2)

    ax.set_xlabel("Hour of day (Europe/Berlin)")
    ax.set_ylabel("Building demand (kW)")
    ax.set_title("Average daily load profile by season")
    ax.legend()
    ax.set_xticks(range(0, 24, 2))
    plt.tight_layout()
    out = paths.plots / "06_11_seasonal_profiles.png"
    plt.savefig(out, dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Saved: {out}")
"""),

    ("code", """\
# Prophet seasonal decomposition -- install with: pip install prophet
demand_col = "greal_LeistungGebaeude"
try:
    from prophet import Prophet

    if demand_col in df_utc.columns:
        prophet_df = df_utc[demand_col].resample("D").mean().dropna().reset_index()
        prophet_df.columns = ["ds", "y"]
        prophet_df["ds"] = prophet_df["ds"].dt.tz_localize(None)

        m = Prophet(yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False)
        m.fit(prophet_df)
        future   = m.make_future_dataframe(periods=90)
        forecast = m.predict(future)
        fig = m.plot_components(forecast)
        fig.suptitle("Prophet decomposition -- building demand (trend + weekly + annual)", y=1.02)
        plt.tight_layout()
        out = paths.plots / "06_11_prophet_decomposition.png"
        plt.savefig(out, dpi=150, bbox_inches="tight")
        plt.show()
        print(f"Saved: {out}")
except ImportError:
    print("Prophet not installed. Run: pip install prophet  then re-run this cell.")
"""),

    # Section 12 - customer deliverable
    ("md", """\
## 12. HP COP -- Polished Customer Chart

First deliverable for a customer conversation. Publication-quality chart, clean labels.
"""),

    ("code", """\
heat_col = "greal_WMZ_Hz_Erz_WP"
elec_col = "greal_E_WP"

if heat_col in df_utc.columns and elec_col in df_utc.columns:
    daily_heat  = df_utc[heat_col].resample("D").sum()
    daily_elec  = df_utc[elec_col].resample("D").sum()
    daily_cop   = (daily_heat / daily_elec.replace(0, np.nan)).clip(0, 8)
    monthly_cop = daily_cop.resample("ME").mean()

    fig, ax = plt.subplots(figsize=(16, 6))

    # Seasonal shading
    for year in range(2022, 2027):
        for start, end, color, alpha in [
            (f"{year}-12-01", f"{year+1}-03-01", "steelblue", 0.07),
            (f"{year}-06-01", f"{year}-09-01",   "gold",      0.07),
        ]:
            try:
                ax.axvspan(pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC"),
                           alpha=alpha, color=color)
            except Exception:
                pass

    ax.scatter(daily_cop.index, daily_cop.values, s=4, alpha=0.3,
               color="#90CAF9", label="Daily COP", zorder=2)
    ax.plot(monthly_cop.index, monthly_cop.values, linewidth=2.5,
            color="#1565C0", label="Monthly mean COP", zorder=3)
    ax.axhline(3.0, color="#D32F2F", linestyle="--", linewidth=1.2, label="COP 3.0 (benchmark)")

    ax.set_ylabel("Heat Pump COP (heat out / electricity in)", fontsize=12)
    ax.set_title("Heat Pump Performance -- EnFa Building  (Dec 2022 to May 2026)",
                 fontsize=14, pad=12)
    ax.legend(fontsize=10, loc="upper right")
    ax.set_ylim(0, 7)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    plt.xticks(rotation=30, fontsize=10)
    plt.tight_layout()

    out = paths.plots / "06_12_hp_cop_customer.png"
    plt.savefig(out, dpi=200, bbox_inches="tight")
    plt.show()
    print(f"Customer chart saved: {out}")
    print(f"Overall mean COP:  {daily_cop.mean():.2f}")
    print(f"Best month COP:    {monthly_cop.max():.2f}  ({monthly_cop.idxmax().strftime('%b %Y')})")
    print(f"Worst month COP:   {monthly_cop.min():.2f}  ({monthly_cop.idxmin().strftime('%b %Y')})")
"""),

]  # end NB06_CELLS


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

def build_nb(cells_spec):
    nb = new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.11"},
    }
    nb.cells = [
        (md if t == "md" else code)(src) for t, src in cells_spec
    ]
    return nb


def main():
    NB_DIR.mkdir(parents=True, exist_ok=True)

    nb05 = build_nb(NB05_CELLS)
    p05  = NB_DIR / "05_signal_profile_explorer.ipynb"
    with open(p05, "w", encoding="utf-8") as f:
        nbformat.write(nb05, f)
    print(f"Written: {p05}  ({len(nb05.cells)} cells)")

    nb06 = build_nb(NB06_CELLS)
    p06  = NB_DIR / "06_full_eda.ipynb"
    with open(p06, "w", encoding="utf-8") as f:
        nbformat.write(nb06, f)
    print(f"Written: {p06}  ({len(nb06.cells)} cells)")


if __name__ == "__main__":
    main()
