"""
_create_notebooks_05_06_07.py
Generate notebooks 05, 06, 07 following the 01-04 pattern.
Each notebook contains the logic inline — no scripts need to run first.
"""
import sys
from pathlib import Path

try:
    import nbformat as nbf
except ImportError:
    print("pip install nbformat")
    sys.exit(1)

ROOT   = Path(__file__).resolve().parent.parent
NB_DIR = ROOT / "notebooks"

def md(text):   return nbf.v4.new_markdown_cell(text)
def code(text): return nbf.v4.new_code_cell(text)

def save(nb, name):
    path = NB_DIR / name
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    nbf.validate(nb)
    print(f"  OK: {path}")

# ============================================================
# Notebook 05 — Signal Quality Profiling
# ============================================================

def make_nb05():
    nb = nbf.v4.new_notebook()
    nb.cells = [

md("""# 05 — Signal Quality Profiling

**Purpose:** Profile every EnFa signal across its full time range using DuckDB.

Corresponds to `scripts/06_signal_profiles.py` — same logic, step by step.

**What this does:**
- Row count, null count, min/max/mean/std, percentiles for every signal
- Gap ratio — fraction of expected 20-second readings that are missing
- Outlier count — values beyond mean ± 3σ
- Saves `reports/signal_quality_profiles.csv` (used by notebook 07)

**Interactive cells:**
- **Step 2** — change `SIGNAL` and re-run → instant stats for one signal
- **Step 3** — change `CATEGORY` and re-run → all signals in that group
- **Step 4** — batch run all signals (~60-120 min), saves the CSV"""),

code("""import sys
import csv
import time
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path
from collections import Counter

import duckdb
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths

cfg   = load_config()
paths = resolve_paths(cfg=cfg)

sns.set_theme(style="whitegrid", palette="tab10")
print(f"Project root : {paths.root}")
print(f"Raw data     : {paths.raw_data}")
print(f"Reports      : {paths.reports}")"""),

md("""## Step 1: Load signal classification

Notebook 04 already classified all 233 signals into physical categories.
We load that here so every profile row is labelled with its category."""),

code("""EXCLUDE_STEMS         = frozenset({"A", "_value", "pilot"})
SNAPSHOT_ROW_THRESHOLD = 20
DEFAULT_INTERVAL_S     = 20   # dominant BMS polling rate

def load_category_map(reports_dir: Path) -> dict:
    path = reports_dir / "signal_classification.csv"
    if not path.exists():
        print("WARNING: signal_classification.csv not found")
        return {}
    mapping = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            stem = row.get("signal_name", "").strip()
            cat  = row.get("category",    "").strip()
            excl = row.get("exclude",     "").strip().lower()
            if stem:
                mapping[stem] = "EXCLUDE" if excl == "true" else cat
    return mapping

category_map = load_category_map(paths.reports)

counts = Counter(v for v in category_map.values() if v != "EXCLUDE")
print(f"Signals mapped : {len(category_map)}")
print(f"Categories     : {len(counts)}")
print()
for cat, n in sorted(counts.items(), key=lambda x: -x[1])[:15]:
    print(f"  {cat:<35}  {n:>3}")"""),

md("""## Step 2: Profile one signal

**Change `SIGNAL` and re-run this cell.**

DuckDB reads the full CSV in a few seconds and returns complete statistics.

Gap ratio:
- `0.00` = all readings present
- `0.10` = 10 % of expected 20-second readings missing
- `> 0.50` = more than half the data is gone"""),

code("""# ---- change this ----
SIGNAL = "greal_WP1AbtauSek"
# ----------------------

csv_path = paths.raw_data / f"{SIGNAL}.csv"
if not csv_path.exists():
    raise FileNotFoundError(csv_path)

STATS = '''
SELECT
    COUNT(*)                                                       AS row_count,
    COUNT(*) - COUNT(TRY_CAST(_value AS DOUBLE))                   AS null_count,
    ROUND(MIN(TRY_CAST(_value AS DOUBLE)), 4)                      AS val_min,
    ROUND(MAX(TRY_CAST(_value AS DOUBLE)), 4)                      AS val_max,
    ROUND(AVG(TRY_CAST(_value AS DOUBLE)), 4)                      AS val_mean,
    ROUND(STDDEV_SAMP(TRY_CAST(_value AS DOUBLE)), 4)              AS val_std,
    ROUND(APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.50), 4)    AS p50,
    ROUND(APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.95), 4)    AS p95,
    MIN(TRY_CAST(_time AS TIMESTAMPTZ))                            AS t_start,
    MAX(TRY_CAST(_time AS TIMESTAMPTZ))                            AS t_end
FROM read_csv(
    '{path}',
    delim=';', header=true, ignore_errors=true
)
WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
'''

row = duckdb.sql(STATS.format(path=csv_path.as_posix())).fetchone()
rc, nc, vmin, vmax, vmean, vstd, p50, p95, t_s, t_e = row

dur_s    = (t_e - t_s).total_seconds() if t_s and t_e else 0
expected = int(dur_s / DEFAULT_INTERVAL_S) if dur_s > 0 else 0
gap      = round(max(0.0, 1 - rc / expected), 3) if expected > 0 else 0.0

print(f"Signal   : {SIGNAL}  [{category_map.get(SIGNAL, 'unknown')}]")
print(f"Rows     : {rc:,}   Nulls: {nc:,}")
print(f"Range    : {vmin} → {vmax}")
print(f"Mean/Std : {vmean} / {vstd}")
print(f"Median   : {p50}   P95: {p95}")
print(f"Coverage : {t_s}  →  {t_e}")
print(f"Gap ratio: {gap:.1%}  (expected {expected:,} readings @ {DEFAULT_INTERVAL_S}s)")"""),

md("""## Step 3: Browse by category

**Change `CATEGORY` and re-run.** Profiles every signal in that group.

Categories to try: `hp_defrost` · `hp_temperature` · `battery_soc` ·
`energy_meter` · `outdoor_weather` · `heating_supply` · `pv_generation`"""),

code("""# ---- change this ----
CATEGORY = "hp_defrost"
# ----------------------

in_cat  = [s for s, c in category_map.items() if c == CATEGORY]
files_c = [paths.raw_data / f"{s}.csv" for s in in_cat
           if (paths.raw_data / f"{s}.csv").exists()]
print(f"Category '{CATEGORY}' → {len(files_c)} signals\\n")

QUICK = '''
SELECT
    COUNT(*) AS rows,
    ROUND(MIN(TRY_CAST(_value AS DOUBLE)), 3)  AS val_min,
    ROUND(MAX(TRY_CAST(_value AS DOUBLE)), 3)  AS val_max,
    ROUND(AVG(TRY_CAST(_value AS DOUBLE)), 3)  AS val_mean
FROM read_csv(
    '{path}', delim=';', header=true, ignore_errors=true
)
WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
'''

rows = []
for fpath in files_c:
    try:
        r = duckdb.sql(QUICK.format(path=fpath.as_posix())).fetchone()
        rows.append({"signal": fpath.stem, "rows": r[0],
                     "min": r[1], "max": r[2], "mean": r[3]})
    except Exception as e:
        rows.append({"signal": fpath.stem, "rows": 0,
                     "min": None, "max": None, "mean": str(e)[:40]})

print(pd.DataFrame(rows).to_string(index=False))"""),

md("""## Step 4: Batch profile all signals

Runs DuckDB over all ~230 signals across 40 GB. **Expected: 60-120 min.**

Run once. If the output CSV already exists, this cell is a no-op.
The script version (`scripts/06_signal_profiles.py`) does the same thing
from the command line."""),

code("""out_path = paths.reports / "signal_quality_profiles.csv"

if out_path.exists():
    print(f"Already exists: {out_path}")
    print("Delete it and re-run to regenerate.")
else:
    csv_files_all = sorted(
        f for f in paths.raw_data.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
        and f.stem not in EXCLUDE_STEMS
        and category_map.get(f.stem, "") != "EXCLUDE"
    )
    print(f"Profiling {len(csv_files_all)} signals  (this will take 60-120 min)...")

    FULL_STATS = '''
    SELECT
        COUNT(*) AS row_count,
        COUNT(*) - COUNT(TRY_CAST(_value AS DOUBLE)) AS null_count,
        MIN(TRY_CAST(_value AS DOUBLE))  AS val_min,
        MAX(TRY_CAST(_value AS DOUBLE))  AS val_max,
        AVG(TRY_CAST(_value AS DOUBLE))  AS val_mean,
        STDDEV_SAMP(TRY_CAST(_value AS DOUBLE)) AS val_std,
        APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.05) AS p05,
        APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.50) AS p50,
        APPROX_QUANTILE(TRY_CAST(_value AS DOUBLE), 0.95) AS p95,
        MIN(TRY_CAST(_time AS TIMESTAMPTZ)) AS t_start,
        MAX(TRY_CAST(_time AS TIMESTAMPTZ)) AS t_end
    FROM read_csv(
        '{path}', delim=';', header=true, ignore_errors=true
    )
    WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
    '''

    con = duckdb.connect()
    con.execute("PRAGMA threads=4")

    profile_rows = []
    t0 = time.time()

    for i, fpath in enumerate(csv_files_all):
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(csv_files_all)}  elapsed={time.time()-t0:.0f}s")
        cat = category_map.get(fpath.stem, "unknown")
        try:
            r  = con.execute(FULL_STATS.format(path=fpath.as_posix())).fetchone()
            rc = int(r[0] or 0)
            if rc < SNAPSHOT_ROW_THRESHOLD:
                profile_rows.append({"signal_name": fpath.stem, "category": cat,
                                     "row_count": rc, "notes": f"snapshot ({rc} rows)"})
                continue
            t_s, t_e = r[9], r[10]
            dur_s = (t_e - t_s).total_seconds() if t_s and t_e else 0
            exp   = int(dur_s / DEFAULT_INTERVAL_S) if dur_s > 0 else 0
            gap   = round(max(0.0, 1 - rc / exp), 4) if exp > 0 else 0.0
            profile_rows.append({
                "signal_name": fpath.stem, "category": cat,
                "row_count": rc, "null_count": int(r[1] or 0),
                "val_min": r[2],  "val_max": r[3],
                "val_mean": r[4], "val_std": r[5],
                "p05": r[6], "p50": r[7], "p95": r[8],
                "start_time": str(t_s), "end_time": str(t_e),
                "gap_ratio": gap, "notes": "ok",
            })
        except Exception as exc:
            profile_rows.append({"signal_name": fpath.stem, "category": cat,
                                  "row_count": 0, "notes": str(exc)[:80]})

    con.close()
    df_all = pd.DataFrame(profile_rows)
    df_all.to_csv(out_path, index=False)
    ok_n = (df_all["notes"] == "ok").sum()
    print(f"\\nDone. {ok_n} signals profiled. Saved: {out_path}")"""),

md("## Step 5: Quality overview plots"),

code("""profiles_path = paths.reports / "signal_quality_profiles.csv"
if not profiles_path.exists():
    print("Run Step 4 first.")
else:
    pf  = pd.read_csv(profiles_path)
    ok  = pf[pf["notes"] == "ok"].copy()
    ok["gap_ratio"] = pd.to_numeric(ok.get("gap_ratio", 0), errors="coerce").fillna(0)

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    cat_counts = ok["category"].value_counts().head(15)
    axes[0].barh(cat_counts.index, cat_counts.values, color="steelblue")
    axes[0].set_title("Signal count by category")
    axes[0].set_xlabel("Signals")

    axes[1].hist(ok["gap_ratio"], bins=30, color="coral", edgecolor="white")
    axes[1].set_title("Gap ratio distribution")
    axes[1].set_xlabel("Gap ratio  (0 = complete, 1 = all missing)")
    axes[1].set_ylabel("Signals")

    plt.tight_layout()
    plots_dir = paths.reports / "plots"
    plots_dir.mkdir(exist_ok=True)
    plt.savefig(plots_dir / "05_signal_quality_overview.png", dpi=150, bbox_inches="tight")
    plt.show()

    problem = ok[ok["gap_ratio"] > 0.10].sort_values("gap_ratio", ascending=False)
    print(f"Signals with >10% gap ratio: {len(problem)}")
    if len(problem):
        cols = [c for c in ["signal_name","category","row_count","gap_ratio"] if c in problem]
        print(problem[cols].head(20).to_string(index=False))"""),

md("""## Key findings

After running Step 4:
- Signals with gap_ratio > 0.10 need investigation before modeling
- Signals with val_min == val_max are stuck / always-on → exclude from forecasting
- Categories with many signals are the richest subsystems for MPC

These profiles feed directly into notebook 06 (resampling) and notebook 07 (full EDA)."""),

    ]
    return nb


# ============================================================
# Notebook 06 — Hourly Resampling
# ============================================================

def make_nb06():
    nb = nbf.v4.new_notebook()
    nb.cells = [

md("""# 06 — Hourly Resampling

**Purpose:** Resample all EnFa signals from ~20-second raw resolution to hourly Parquet.

Corresponds to `scripts/07_resample_hourly.py` — same logic, step by step.

**Aggregation rules (critical — do not change without reason):**

| Signal type | Rule | Why |
|---|---|---|
| Power (kW), temperature, SOC, voltage | `MEAN` | Average over the hour |
| Cumulative energy/gas counters (`greal_E_*`) | `MAX − MIN` (delta) | Ever-increasing totals — delta gives energy that hour |
| Defrost duration (`*AbtauSek`) | `SUM` | Total seconds of defrost in that hour |
| Setpoints (`V_real*`, event-driven) | `LAST` + forward-fill | Only written on change; ffill propagates last known value |

Output: `data/processed/hourly.parquet` (~200 MB) — one UTC hour per row, one column per signal.
All notebooks 07+ load this Parquet instead of the raw 40 GB."""),

code("""import sys
import csv
import time
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths

cfg   = load_config()
paths = resolve_paths(cfg=cfg)

print(f"Project root : {paths.root}")
print(f"Raw data     : {paths.raw_data}")
print(f"Processed    : {paths.processed}")"""),

md("""## Step 1: Aggregation rule logic

`resolve_aggregation()` maps each signal's category to its correct aggregation type.

Test it on a few signals to confirm it assigns the right rules."""),

code("""EXCLUDE_STEMS = frozenset({"A", "_value", "pilot"})

_SETPOINT_CATS = frozenset({
    "hp_setpoint", "hvac_setpoint", "night_setback", "dhw_setpoint",
    "battery_setpoint", "storage_setpoint", "heating_curve",
    "control_param", "timer_schedule",
})

def resolve_aggregation(category: str, signal_name: str) -> str:
    cat  = category.lower().strip()
    name = signal_name.lower()
    if cat in ("exclude",) or signal_name in EXCLUDE_STEMS:
        return "skip"
    if any(k in cat  for k in ("energy","gas","volume","counter","pulse","dint")): return "delta"
    if signal_name.startswith("dint"):                                              return "delta"
    if "defrost" in cat or "abtau" in cat or "abtau" in name:                      return "sum"
    if cat in _SETPOINT_CATS:                                                       return "last"
    if any(k in cat  for k in ("setpoint","setback","curve","schedule","timer","param")): return "last"
    return "mean"

# Quick self-test
tests = [
    ("greal_E_WP",          "energy_meter"),
    ("greal_WP1AbtauSek",   "hp_defrost"),
    ("V_real_maxVorlaufTemp","hp_setpoint"),
    ("real_BatterieLeistung","battery_power"),
    ("greal_BatterieLadeZustand", "battery_soc"),
]
print(f"{'Signal':<35} {'Category':<20} {'Agg'}")
print("-" * 62)
for sig, cat in tests:
    print(f"{sig:<35} {cat:<20} {resolve_aggregation(cat, sig)}")"""),

md("""## Step 2: Check aggregation assignments for all signals

Load the classification from notebook 04 and show which aggregation type
each signal will receive. This is a good sanity check before running the full resample."""),

code("""def load_category_map(reports_dir: Path) -> dict:
    path = reports_dir / "signal_classification.csv"
    if not path.exists():
        print("WARNING: signal_classification.csv not found — all signals will use 'mean'")
        return {}
    mapping = {}
    with open(path, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            stem = row.get("signal_name", "").strip()
            cat  = row.get("category",    "").strip()
            excl = row.get("exclude",     "").strip().lower()
            if stem:
                mapping[stem] = "EXCLUDE" if excl == "true" else cat
    return mapping

category_map = load_category_map(paths.reports)

# Show aggregation assignment breakdown
from collections import Counter
assignments = {s: resolve_aggregation(c, s) for s, c in category_map.items()}
agg_counts  = Counter(assignments.values())
print("Aggregation type breakdown:")
for agg, n in sorted(agg_counts.items()):
    print(f"  {agg:<8}  {n} signals")

print()
print("Sample — delta signals (cumulative energy counters):")
delta_sigs = [s for s, a in assignments.items() if a == "delta"][:8]
for s in delta_sigs:
    print(f"  {s}")"""),

md("""## Step 3: Demonstrate aggregation on one signal

**Change `SIGNAL` and re-run** to see raw rows vs hourly-aggregated result side by side.

Try `greal_E_WP` (cumulative energy counter → delta) or
`V_real_maxVorlaufTemp` (setpoint → last)."""),

code("""# ---- change this ----
SIGNAL = "greal_E_WP"
# ----------------------

csv_path = paths.raw_data / f"{SIGNAL}.csv"
cat      = category_map.get(SIGNAL, "unknown")
agg      = resolve_aggregation(cat, SIGNAL)

print(f"Signal: {SIGNAL}  Category: {cat}  →  Aggregation: {agg}\\n")

# Show first 6 raw rows
RAW = '''
SELECT TRY_CAST(_time AS TIMESTAMPTZ) AS ts, TRY_CAST(_value AS DOUBLE) AS raw_value
FROM read_csv('{path}', delim=';', header=true, ignore_errors=true)
ORDER BY ts LIMIT 6
'''
print("Raw rows (20-second resolution):")
print(duckdb.sql(RAW.format(path=csv_path.as_posix())).df().to_string(index=False))

# Show first 6 hourly-aggregated rows
AGG_SQL = {
    "mean":  "AVG(TRY_CAST(_value AS DOUBLE))",
    "delta": "GREATEST(MAX(TRY_CAST(_value AS DOUBLE)) - MIN(TRY_CAST(_value AS DOUBLE)), 0.0)",
    "sum":   "SUM(TRY_CAST(_value AS DOUBLE))",
    "last":  "ARG_MAX(TRY_CAST(_value AS DOUBLE), TRY_CAST(_time AS TIMESTAMPTZ))",
}
expr = AGG_SQL.get(agg, AGG_SQL["mean"])
HOURLY = f'''
SELECT DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
       ROUND({expr}, 4) AS value
FROM read_csv('{{path}}', delim=';', header=true, ignore_errors=true)
WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
GROUP BY 1 ORDER BY 1 LIMIT 6
'''
print(f"\\nHourly ({agg}):")
print(duckdb.sql(HOURLY.format(path=csv_path.as_posix())).df().to_string(index=False))"""),

md("""## Step 4: Resample all signals to hourly

**This takes 30-60 minutes.** Run once. If `hourly.parquet` already exists, skip.

Each signal is read by DuckDB and reduced to one value per UTC hour.
The results are collected as pandas Series and joined into a wide DataFrame."""),

code("""out_parquet = paths.processed / "hourly.parquet"
paths.processed.mkdir(parents=True, exist_ok=True)

if out_parquet.exists():
    print(f"Already exists: {out_parquet}")
    print("Delete it and re-run to regenerate.")
else:
    EXCLUDE_STEMS_RUN     = frozenset({"A", "_value", "pilot"})
    SNAPSHOT_THRESHOLD    = 20

    csv_files_all = sorted(
        f for f in paths.raw_data.iterdir()
        if f.is_file() and f.suffix.lower() == ".csv"
        and f.stem not in EXCLUDE_STEMS_RUN
        and category_map.get(f.stem, "") != "EXCLUDE"
    )
    print(f"Resampling {len(csv_files_all)} signals → {out_parquet}")

    # DuckDB SQL templates — one per aggregation type
    AGG_TEMPLATES = {
        "mean": '''
            SELECT DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
                   AVG(TRY_CAST(_value AS DOUBLE)) AS value
            FROM read_csv('{path}', delim=';', header=true, ignore_errors=true)
            WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
            GROUP BY 1 ORDER BY 1''',
        "delta": '''
            SELECT DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
                   GREATEST(MAX(TRY_CAST(_value AS DOUBLE))
                            - MIN(TRY_CAST(_value AS DOUBLE)), 0.0) AS value
            FROM read_csv('{path}', delim=';', header=true, ignore_errors=true)
            WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
            GROUP BY 1 ORDER BY 1''',
        "sum": '''
            SELECT DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
                   SUM(TRY_CAST(_value AS DOUBLE)) AS value
            FROM read_csv('{path}', delim=';', header=true, ignore_errors=true)
            WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
            GROUP BY 1 ORDER BY 1''',
        "last": '''
            SELECT DATE_TRUNC('hour', TRY_CAST(_time AS TIMESTAMPTZ)) AS hour_utc,
                   ARG_MAX(TRY_CAST(_value AS DOUBLE),
                           TRY_CAST(_time AS TIMESTAMPTZ)) AS value
            FROM read_csv('{path}', delim=';', header=true, ignore_errors=true)
            WHERE TRY_CAST(_value AS DOUBLE) IS NOT NULL
            GROUP BY 1 ORDER BY 1''',
    }

    con = duckdb.connect()
    con.execute("PRAGMA threads=4")

    series_list    = []
    setpoint_cols  = []
    skipped, t0    = 0, time.time()

    for i, fpath in enumerate(csv_files_all):
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{len(csv_files_all)}  elapsed={time.time()-t0:.0f}s")
        stem = fpath.stem
        cat  = category_map.get(stem, "unknown")
        agg  = resolve_aggregation(cat, stem)
        if agg == "skip":
            skipped += 1
            continue
        try:
            # Skip commissioning snapshots
            count_sql = f"SELECT COUNT(*) FROM read_csv('{fpath.as_posix()}', delim=';', header=true, ignore_errors=true)"
            rc = con.execute(count_sql).fetchone()[0]
            if rc < SNAPSHOT_THRESHOLD:
                skipped += 1
                continue
            sql = AGG_TEMPLATES[agg].format(path=fpath.as_posix())
            df  = con.execute(sql).df()
            if df.empty:
                skipped += 1
                continue
            df["hour_utc"] = pd.to_datetime(df["hour_utc"], utc=True)
            s = df.set_index("hour_utc")["value"].rename(stem)
            series_list.append(s)
            if agg == "last":
                setpoint_cols.append(stem)
        except Exception as exc:
            print(f"  WARN {stem}: {exc}")
            skipped += 1

    con.close()
    print(f"\\nCollected {len(series_list)} signals  |  Skipped {skipped}")
    print("Assembling wide DataFrame...")"""),

md("""## Step 5: Assemble wide DataFrame and forward-fill setpoints

`pd.concat` joins all hourly Series on the shared UTC time index.

Setpoint columns get forward-filled because they are event-driven —
only written when the value changes. Without ffill, most hours are NaN."""),

code("""# This cell runs immediately after Step 4 (series_list must exist in memory)
wide = pd.concat(series_list, axis=1)
wide.index = pd.DatetimeIndex(wide.index, name="hour_utc")
wide.sort_index(inplace=True)

# Forward-fill setpoint columns
cols_present = [c for c in setpoint_cols if c in wide.columns]
if cols_present:
    wide[cols_present] = wide[cols_present].ffill()
    print(f"Forward-filled {len(cols_present)} setpoint columns")

print(f"Wide DataFrame : {wide.shape[0]:,} rows × {wide.shape[1]} columns")
print(f"Time range     : {wide.index.min()}  →  {wide.index.max()}")
print(f"Memory         : {wide.memory_usage(deep=True).sum() / 1e6:.1f} MB")
print()
print(wide.iloc[:3, :6])"""),

md("## Step 6: Save to Parquet and verify"),

code("""table = pa.Table.from_pandas(wide, preserve_index=True)
pq.write_table(table, out_parquet, compression="snappy")

size_mb = out_parquet.stat().st_size / 1e6
print(f"Saved: {out_parquet}")
print(f"Size : {size_mb:.1f} MB")

# Reload to verify round-trip
df_check = pd.read_parquet(out_parquet)
print(f"Reload check : {df_check.shape[0]:,} rows × {df_check.shape[1]} columns  ✓")
print(f"Time range   : {df_check.index.min()}  →  {df_check.index.max()}")
print(f"\\nColumns (first 10):")
for col in df_check.columns[:10]:
    print(f"  {col}")"""),

md("""## Key findings

After running Steps 4-6:
- `hourly.parquet` is the single source of truth for all EDA and modeling notebooks
- Delta signals (`greal_E_*`) now represent actual energy consumed per hour (not running totals)
- Setpoint columns are fully populated via ffill — no NaN gaps
- Notebook 07 (full EDA) loads this Parquet instantly

Check the Parquet shape — expect roughly 30,000 rows (3.5 years × 8,760 hours/year ≈ 30,660)
and ~200 columns."""),

    ]
    return nb


# ============================================================
# Notebook 07 — Full EDA
# ============================================================

def make_nb07():
    nb = nbf.v4.new_notebook()
    nb.cells = [

md("""# 07 — Full EDA

**Purpose:** Analyse all EnFa subsystems using the hourly Parquet from notebook 06.

**Requires:** `data/processed/hourly.parquet`
Run notebook 06 first if it does not exist.

**Sections:**
1. Energy overview — grid, PV, HP monthly balance
2. Heat pump COP — first customer deliverable
3. Battery — SOC and cycling
4. Controls — night setback patterns
5. Correlations — cross-system heatmap"""),

code("""import sys
import warnings
warnings.filterwarnings("ignore")
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns

PROJECT_ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from zoro_eda.config import load_config
from zoro_eda.paths import resolve_paths

cfg   = load_config()
paths = resolve_paths(cfg=cfg)

pq_path = paths.processed / "hourly.parquet"
if not pq_path.exists():
    raise FileNotFoundError(f"Run notebook 06 first: {pq_path}")

df = pd.read_parquet(pq_path)
print(f"Loaded : {df.shape[0]:,} rows × {df.shape[1]} columns")
print(f"Range  : {df.index.min()}  →  {df.index.max()}")

# Localise to Europe/Berlin for daily/seasonal plots
df_local = df.copy()
df_local.index = df_local.index.tz_convert("Europe/Berlin")

sns.set_theme(style="whitegrid", palette="tab10")
plots_dir = paths.reports / "plots"
plots_dir.mkdir(exist_ok=True)
print("Ready.")"""),

md("""## Section 1: Energy overview

Monthly energy balance across the main meters.
Signals used (all delta-aggregated → kWh per hour, summed to monthly):
- `greal_E_WP` — heat pump electricity consumption
- `greal_E_PV` — PV generation (if present)
- `greal_E_Netz` or similar — grid import/export"""),

code("""# Identify available energy signals
energy_cols = [c for c in df.columns if c.startswith("greal_E_") or
               any(k in c.lower() for k in ("netz","pv","bhkw","wp")) and "greal_E" in c]
print("Energy-related columns found:")
for c in energy_cols[:20]:
    print(f"  {c}  min={df[c].min():.1f}  max={df[c].max():.1f}")"""),

code("""# Build monthly sums for whichever energy columns exist
monthly = df.resample("ME").sum()

# Plot top energy signals monthly
plot_cols = [c for c in energy_cols if c in monthly.columns][:6]
if not plot_cols:
    print("No energy columns found — check column names above")
else:
    fig, ax = plt.subplots(figsize=(14, 5))
    for col in plot_cols:
        ax.plot(monthly.index, monthly[col], marker="o", label=col, linewidth=1.5)
    ax.set_title("Monthly energy totals (kWh)", fontsize=13)
    ax.set_ylabel("kWh / month")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    ax.legend(fontsize=8, ncol=2)
    plt.xticks(rotation=30)
    plt.tight_layout()
    plt.savefig(plots_dir / "07_energy_overview.png", dpi=150, bbox_inches="tight")
    plt.show()"""),

md("""## Section 2: Heat pump COP — customer deliverable

COP (Coefficient of Performance) = thermal energy out / electrical energy in.

We use delta-aggregated hourly signals:
- Thermal output: `greal_WMZ_Hz_Erz_WP` (heat meter, kWh)
- Electrical input: `greal_E_WP` (energy meter, kWh)

Daily COP is more stable than hourly (avoids division noise during short cycles)."""),

code("""# Identify HP thermal and electrical signals
thermal_candidates = [c for c in df.columns if "WMZ" in c and "WP" in c]
elec_candidates    = [c for c in df.columns if c in ("greal_E_WP",) or
                      ("E_WP" in c and "greal" in c)]
print("Thermal candidates:", thermal_candidates)
print("Electrical candidates:", elec_candidates)"""),

code("""# COP calculation — adjust column names if the auto-detection above shows different names
THERMAL_COL = thermal_candidates[0] if thermal_candidates else None
ELEC_COL    = elec_candidates[0]    if elec_candidates    else None

if not THERMAL_COL or not ELEC_COL:
    print("Could not find HP thermal or electrical columns — check candidates above")
else:
    daily  = df[[THERMAL_COL, ELEC_COL]].resample("D").sum()
    daily  = daily[(daily[ELEC_COL] > 0.1) & (daily[THERMAL_COL] > 0.1)]
    daily["cop"] = (daily[THERMAL_COL] / daily[ELEC_COL]).clip(0.5, 8)

    fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=False)

    # COP time series (7-day rolling)
    roll = daily["cop"].rolling(7, min_periods=3).mean()
    axes[0].plot(daily.index, daily["cop"], alpha=0.3, color="steelblue", linewidth=0.8)
    axes[0].plot(roll.index,  roll,         color="steelblue", linewidth=2, label="7-day rolling")
    axes[0].axhline(daily["cop"].median(), color="red", linestyle="--",
                    linewidth=1, label=f"Median COP = {daily['cop'].median():.2f}")
    axes[0].set_title("Heat Pump COP — daily (7-day rolling average)", fontsize=13)
    axes[0].set_ylabel("COP")
    axes[0].legend()
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(axes[0].get_xticklabels(), rotation=30)

    # COP histogram
    axes[1].hist(daily["cop"].dropna(), bins=40, color="steelblue", edgecolor="white")
    axes[1].axvline(daily["cop"].median(), color="red", linestyle="--",
                    label=f"Median = {daily['cop'].median():.2f}")
    axes[1].set_title("COP distribution", fontsize=12)
    axes[1].set_xlabel("COP")
    axes[1].set_ylabel("Days")
    axes[1].legend()

    plt.tight_layout()
    plt.savefig(plots_dir / "07_hp_cop.png", dpi=150, bbox_inches="tight")
    plt.show()

    print(f"Median COP  : {daily['cop'].median():.2f}")
    print(f"Mean COP    : {daily['cop'].mean():.2f}")
    print(f"Days with data: {len(daily)}")"""),

md("""## Section 3: Battery SOC and cycling

Battery state of charge over the full period.
Cycling depth = how much the SOC swings each day (max - min).
Deep daily cycling shortens battery life."""),

code("""soc_cols = [c for c in df.columns if "ladezustand" in c.lower() or "soc" in c.lower()
            or ("ladezu" in c.lower())]
print("SOC columns found:", soc_cols)

if soc_cols:
    soc_col = soc_cols[0]
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))

    axes[0].plot(df.index, df[soc_col], linewidth=0.5, color="green", alpha=0.7)
    axes[0].set_title(f"Battery SOC over time — {soc_col}", fontsize=11)
    axes[0].set_ylabel("SOC (%)")
    axes[0].xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    plt.setp(axes[0].get_xticklabels(), rotation=30)

    daily_soc = df[soc_col].resample("D").agg(["min","max"])
    daily_soc["swing"] = daily_soc["max"] - daily_soc["min"]
    axes[1].hist(daily_soc["swing"].dropna(), bins=30, color="green", edgecolor="white")
    axes[1].set_title("Daily SOC swing (cycling depth)", fontsize=11)
    axes[1].set_xlabel("SOC swing per day (%)")
    axes[1].set_ylabel("Days")

    plt.tight_layout()
    plt.savefig(plots_dir / "07_battery_soc.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"Median daily swing: {daily_soc['swing'].median():.1f}%")"""),

md("""## Section 4: Controls — night setback patterns

Night setback = heating setpoints are lowered during unoccupied hours.
This heatmap shows the average setpoint value by hour-of-day and month,
revealing occupancy patterns and seasonal control schedules."""),

code("""setback_cols = [c for c in df.columns if "nacht" in c.lower() or
                "setback" in c.lower() or "absenkung" in c.lower()]
setpoint_cols_all = [c for c in df.columns if c.startswith("V_real")]

print("Night setback columns:", setback_cols)
print(f"V_real setpoint columns: {len(setpoint_cols_all)}")

if setback_cols:
    sb_col = setback_cols[0]
    pivot  = df_local.groupby([df_local.index.hour, df_local.index.month])[sb_col].mean().unstack()
    fig, ax = plt.subplots(figsize=(12, 5))
    sns.heatmap(pivot, ax=ax, cmap="RdYlGn_r", cbar_kws={"label": "Setpoint value"})
    ax.set_title(f"Night setback by hour × month — {sb_col}", fontsize=12)
    ax.set_xlabel("Month")
    ax.set_ylabel("Hour of day (local)")
    plt.tight_layout()
    plt.savefig(plots_dir / "07_night_setback_heatmap.png", dpi=150, bbox_inches="tight")
    plt.show()
else:
    print("No night setback columns found — check V_real signals above")"""),

md("## Section 5: Cross-system correlation heatmap"),

code("""# Select a representative set of signals for correlation
candidate_prefixes = ("greal_E_", "greal_WMZ_", "greal_Batterie", "real_Batterie",
                      "real_AT", "greal_WP")
rep_cols = [c for c in df.columns
            if any(c.startswith(p) for p in candidate_prefixes)][:25]

if len(rep_cols) < 3:
    print("Too few candidate columns — listing all columns for manual selection:")
    print(df.columns.tolist()[:30])
else:
    daily_df = df[rep_cols].resample("D").mean().dropna(thresh=len(rep_cols)//2)
    corr = daily_df.corr()

    mask = np.triu(np.ones_like(corr, dtype=bool))
    fig, ax = plt.subplots(figsize=(14, 11))
    sns.heatmap(corr, mask=mask, ax=ax, cmap="coolwarm", center=0,
                vmin=-1, vmax=1, annot=len(rep_cols) <= 15,
                fmt=".2f", linewidths=0.3, cbar_kws={"shrink": 0.7})
    ax.set_title("Daily signal correlation (sample of key signals)", fontsize=13)
    plt.tight_layout()
    plt.savefig(plots_dir / "07_correlation_heatmap.png", dpi=150, bbox_inches="tight")
    plt.show()"""),

md("""## Key findings

After running this notebook:
- HP COP chart (`reports/plots/07_hp_cop.png`) is the first customer deliverable
- Battery cycling depth indicates whether the current control strategy is aggressive
- Night setback heatmap reveals actual occupancy schedule vs design intent
- Correlation heatmap shows which signals move together — useful for MPC feature selection

**Next notebooks:**
- `08_hp_model.ipynb` — physics-based HP COP model (COP vs outdoor temp)
- `09_battery_model.ipynb` — round-trip efficiency, degradation
- `10_mpc_prototype.ipynb` — MPC state-space formulation"""),

    ]
    return nb


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("Creating notebooks 05, 06, 07...\n")

    save(make_nb05(), "05_signal_profiles.ipynb")
    save(make_nb06(), "06_resample_hourly.ipynb")
    save(make_nb07(), "07_full_eda.ipynb")

    print("\nDone.")
    print("  05_signal_profiles.ipynb  — profile signals (corresponds to scripts/06)")
    print("  06_resample_hourly.ipynb  — resample to Parquet (corresponds to scripts/07)")
    print("  07_full_eda.ipynb         — full EDA using the Parquet")
