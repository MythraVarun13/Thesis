# EnFa Data Analysis — ZORO Energy

EDA of the EnFa commercial building energy dataset, including signal classification,
full-data quality profiling, hourly resampling, TimescaleDB ingestion, and Grafana visualization.

**Status:** EDA complete · 215 signals profiled · Hourly Parquet ready · Grafana dashboard live

---

## Getting the Raw Data

The 233 CSV signal files (~40.5 GB) are **not in git** — they are too large and contain operational data.

Download them from Google Drive:

**[EnFa Raw Data — Google Drive](https://drive.google.com/drive/folders/1eQhHjXlCtKwyOO67YyAFa9ZlAwIEV6qF)**

1. Download `data_2026_05_26.zip`
2. Extract the zip — it contains a `data/` folder
3. Move the contents into `<project_root>/data/`

```
ZE/
└── data/
    ├── greal_BatterieLadeZustand.csv
    ├── real_BatterieLeistung.csv
    └── ... (233 files total)
```

> **Never rename or modify raw CSV files** — they are the source of truth.

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.10+ | |
| Docker Desktop | any recent | Required only for Grafana visualization (Step 3) |
| Jupyter | optional | To open `.ipynb` notebooks |

---

## Quick Start

### Step 1 — Analysis pipeline (EDA)

```powershell
# Windows PowerShell
cd "C:\path\to\ZE"
pip install -r requirements.txt

# Run once in order
python scripts/01_scan_files.py          # file inventory
python scripts/02_detect_schema.py       # schema detection
python scripts/03_profile_timeseries.py  # time coverage and sampling intervals
python scripts/05_classify_signals.py    # signal classification + ZORO pipeline mapping
python scripts/06_signal_profiles.py --threads 6   # full-data quality profiles via DuckDB (~5 min)
```

```bash
# Mac / Linux
cd /path/to/ZE
pip install -r requirements.txt
python scripts/01_scan_files.py
python scripts/02_detect_schema.py
python scripts/03_profile_timeseries.py
python scripts/05_classify_signals.py
python scripts/06_signal_profiles.py --threads 6
```

### Step 2 — Resample to hourly Parquet

Reads all 233 signals from the 40 GB raw CSVs via DuckDB and saves a single
`data/processed/hourly.parquet` (~17 MB compressed, ~200 MB uncompressed).
Run once — all further analysis reads from this file.

```powershell
python scripts/07_resample_hourly.py --threads 6
# Runtime: ~5 minutes on a modern 6-core machine
# Output:  data/processed/hourly.parquet
```

### Step 3 — Grafana visualization (optional)

> Steps 1 and 2 are completely self-contained inside this repo.
> Step 3 requires **Docker Desktop** to run TimescaleDB and Grafana locally.
> No other repository is needed — everything is bundled in `docker/`.

#### 3a. Install Docker Desktop

| Platform | Download |
|----------|---------|
| Windows  | https://docs.docker.com/desktop/setup/install/windows-install/ |
| Mac      | https://docs.docker.com/desktop/setup/install/mac-install/ |
| Linux (Ubuntu/Debian) | `sudo apt install docker.io docker-compose-plugin` |

After installing, start Docker Desktop and wait for the whale icon to appear in the taskbar (Windows/Mac).

#### 3b. Start the local stack

All required files live in `docker/` inside this repo:

```
docker/
├── docker-compose.yml                          ← TimescaleDB + Grafana
├── schema/
│   └── init.sql                                ← applied automatically on first start
└── grafana/
    └── provisioning/
        ├── datasources/timescaledb.yml         ← auto-connects Grafana to TimescaleDB
        └── dashboards/dashboard.yml            ← auto-loads dashboard JSON files
```

```powershell
# From the ZE project root
docker compose -f docker/docker-compose.yml up -d

# Verify both containers are healthy
docker ps
# Expected output:
#   enfa-timescaledb   Up (healthy)
#   enfa-grafana       Up
```

> **First start only:** TimescaleDB runs `docker/schema/init.sql` automatically.
> This creates all required tables (`tenants`, `buildings`, `datapoints`, `observations`).
> Subsequent starts skip this step — your data is preserved in a named Docker volume.

#### 3c. Load EnFa data into TimescaleDB

Reads `data/processed/hourly.parquet` (from Step 2) and inserts 5.18 million
hourly observations. Idempotent — safe to re-run.

```powershell
python scripts/08_load_to_timescaledb.py
# Runtime: ~5 minutes
```

#### 3d. Register the Grafana dashboard

```powershell
python scripts/09_create_grafana_dashboard.py
```

Open **http://localhost:3000** (admin / zoro) → **EnFa Building Analysis**.

#### Stopping and restarting

```powershell
docker compose -f docker/docker-compose.yml down      # stop (data preserved)
docker compose -f docker/docker-compose.yml down -v   # stop + delete all data
```

---

## Script Reference

| Script | Purpose | Runtime | Key output |
|--------|---------|---------|------------|
| `01_scan_files.py` | File inventory — sizes, extensions, empty files | seconds | `reports/data_inventory.csv` |
| `02_detect_schema.py` | Delimiter, encoding, column names, 20-row samples | seconds | `reports/file_format_report.csv`, `reports/sample_rows/` |
| `03_profile_timeseries.py` | Start/end timestamps, sampling intervals, gap estimate | seconds | `reports/timestamp_coverage_report.csv`, `reports/sampling_interval_report.csv` |
| `05_classify_signals.py` | German→English signal names, units, ZORO pipeline mapping | seconds | `reports/signal_classification.csv`, `reports/zoro_pipeline_mapping.csv` |
| `06_signal_profiles.py` | Full-data statistics for every signal via DuckDB | ~5 min | `reports/signal_quality_profiles.csv` |
| `07_resample_hourly.py` | Resample 40 GB → hourly Parquet (correct agg per signal type) | ~5 min | `data/processed/hourly.parquet` |
| `08_load_to_timescaledb.py` | Load hourly Parquet into local TimescaleDB | ~5 min | 5.18M rows in `observations` table |
| `09_create_grafana_dashboard.py` | Build and register the Grafana dashboard via API | seconds | Dashboard at localhost:3000 |

All scripts are idempotent — safe to re-run.

---

## Notebook Reference

| Notebook | Purpose | Requires |
|----------|---------|---------|
| `01_file_inventory.ipynb` | Interactive file browser | — |
| `02_schema_detection.ipynb` | Schema explorer | — |
| `03_timeseries_profiling.ipynb` | Time coverage and sampling | — |
| `04_signal_classification.ipynb` | Signal browser and classification review | `reports/signal_classification.csv` |
| `05_signal_profiles.ipynb` | Interactive signal quality explorer — one signal or category at a time via DuckDB | raw CSVs |
| `05_signal_profile_explorer.ipynb` | Legacy version of 05 (kept for reference) | `reports/signal_quality_profiles.csv` |
| `06_resample_hourly.ipynb` | Self-contained resampler — same logic as script 07, interactive | raw CSVs |
| `07_full_eda.ipynb` | Full EDA: HP COP, battery, energy balance, correlations | `data/processed/hourly.parquet` |

---

## Key Findings

| Finding | Value |
|---------|-------|
| Dataset | 233 CSV files, 40.5 GB, Dec 2022 → May 2026 (live, not historical) |
| Format | UTF-8, semicolon-delimited, InfluxDB schema (`_time`, `_value`, `_measurement`) |
| Dominant sampling interval | ~20 seconds (169 signals) |
| Successfully profiled | 215 signals (15 commissioning snapshots skipped) |
| Pipeline-mapped signals | 223 / 233 |
| Hourly Parquet | 29,207 rows × 215 columns, 16.7 MB compressed |
| TimescaleDB | 5.18 million observations (tenant `enfa-01`) |
| Recommended first MVP | Heat Pump FDD → HP COP trend + defrost anomaly detection |

---

## Grafana Dashboard

After running scripts 07, 08, and 09, open **http://localhost:3000** (admin / zoro).

Dashboard: **EnFa Building Analysis** (`/d/enfa-overview`)

| Panel | What it shows |
|-------|--------------|
| HP COP daily trend | Heat output / electrical input over 3.5 years |
| WP1 / WP2 / WP3 defrost | Weekly defrost duration per heat pump unit |
| Energy balance monthly | PV + BHKW generation vs building demand |
| Battery SOC | All 4 battery clusters, hourly mean |
| Outdoor temperature | Full 3.5-year record, 6h mean |
| Signal browser | Dropdown to explore any of the 215 signals |

The signal browser variable is populated live from TimescaleDB — any new signals loaded via script 08 automatically appear.

---

## Data Architecture

```
EnFa raw CSVs (233 files, 40.5 GB)
    ↓ DuckDB (no full load into memory)
    ↓ scripts/06_signal_profiles.py
reports/signal_quality_profiles.csv    ← quality scorecard for every signal

    ↓ scripts/07_resample_hourly.py    (mean/delta/sum/last per signal type)
data/processed/hourly.parquet          ← 29K rows × 215 cols, 17 MB

    ↓ scripts/08_load_to_timescaledb.py (direct psycopg2, bypasses Kafka)
TimescaleDB observations hypertable    ← 5.18M rows, tenant='enfa-01'

    ↓ scripts/09_create_grafana_dashboard.py
Grafana dashboard                      ← localhost:3000
```

**Why DuckDB?** It queries CSV files directly from disk with SQL — no loading
40 GB into Python memory. Aggregations that would take 20+ minutes with pandas
take 30 seconds with DuckDB.

**Aggregation rules for resampling:**

| Signal type | Rule | Example signals |
|-------------|------|----------------|
| Cumulative energy/gas counters | MAX - MIN per hour | `greal_E_*`, `dint*` |
| Defrost duration | SUM per hour | `greal_WP*AbtauSek` |
| Setpoints / control params | LAST per hour + ffill | `V_real*` |
| Everything else | MEAN per hour | temperatures, SOC, power |

---

## Project Structure

```
ZE/
├── README.md
├── CLAUDE.md                           ← project instructions for AI assistant
├── config.yaml                         ← shared project settings
├── requirements.txt                    ← all dependencies (phased)
│
├── data/
│   ├── *.csv                           ← 233 raw signal files — READ ONLY, not in git
│   └── processed/
│       └── hourly.parquet              ← hourly resampled output (gitignored)
│
├── scripts/
│   ├── 01_scan_files.py                ← Step 1: file inventory
│   ├── 02_detect_schema.py             ← Step 2: schema detection
│   ├── 03_profile_timeseries.py        ← Step 3: time-series profiling
│   ├── 05_classify_signals.py          ← Step 4: signal classification
│   ├── 06_signal_profiles.py           ← Step 5: full-data quality profiles (DuckDB)
│   ├── 07_resample_hourly.py           ← Step 6: resample 40 GB → hourly Parquet
│   ├── 08_load_to_timescaledb.py       ← Step 7: load Parquet → TimescaleDB
│   └── 09_create_grafana_dashboard.py  ← Step 8: register Grafana dashboard
│
├── notebooks/
│   ├── 01_file_inventory.ipynb
│   ├── 02_schema_detection.ipynb
│   ├── 03_timeseries_profiling.ipynb
│   ├── 04_signal_classification.ipynb
│   ├── 05_signal_profiles.ipynb        ← interactive signal quality explorer
│   ├── 06_resample_hourly.ipynb        ← interactive resampler
│   └── 07_full_eda.ipynb               ← full EDA (requires hourly.parquet)
│
├── docker/                             ← self-contained visualization stack
│   ├── docker-compose.yml              ← TimescaleDB + Grafana (no external deps)
│   ├── schema/
│   │   └── init.sql                    ← applied automatically on first container start
│   └── grafana/
│       └── provisioning/
│           ├── datasources/timescaledb.yml
│           └── dashboards/dashboard.yml
│
├── src/
│   └── zoro_eda/                       ← shared Python library
│       ├── config.py                   ← load_config()
│       ├── paths.py                    ← ProjectPaths, resolve_paths()
│       └── ...
│
├── reports/
│   ├── data_inventory.csv
│   ├── signal_classification.csv       ← master signal table (223 signals)
│   ├── zoro_pipeline_mapping.csv       ← 223 signals mapped to JSON v1
│   ├── signal_quality_profiles.csv     ← DuckDB full-data quality scorecard
│   ├── resample_log.csv                ← aggregation type used per signal
│   ├── EDA_SUMMARY.md
│   └── plots/
│
└── context/                            ← running analysis notes
    ├── session_log.md
    ├── decisions_log.md
    ├── signal_dictionary.md
    └── ...
```

---

## Dependencies

`requirements.txt` covers all phases:

```
# EDA
pandas, numpy, matplotlib, charset-normalizer, python-dateutil, openpyxl

# Full-data profiling and resampling (DuckDB)
duckdb, pyarrow, seaborn, statsmodels, tqdm

# TimescaleDB + Grafana pipeline
psycopg2-binary, requests

# MPC phase (install when ready)
# cvxpy, scikit-learn

# Forecasting phase (install when ready)
# prophet, sktime, darts

# MVP demo phase (install when ready)
# streamlit, plotly
```

---

## Signal Classification

Signal names are German BMS tags. Classification uses three layers:

1. **Exact match** (`signal_rules.DIRECT_MAP`) — edge cases and umlaut variants
2. **Pattern matching** (`signal_rules.PATTERN_RULES`) — all listed substrings must be present
3. **Fallback** — `category="unknown"`, flagged for manual review

**Key German vocabulary:**

| German | English |
|--------|---------|
| WP / Wärmepumpe | heat pump |
| BHKW / Blockheizkraftwerk | CHP / combined heat and power |
| Vorlauf | supply / flow temperature |
| Ruecklauf | return temperature |
| Abtau | defrost |
| Leistung | power |
| Energie | energy |
| WMZ / Wärmemengenzähler | heat meter |
| Nachtabsenkung | night setback |
| Speicher | storage / tank |
| Sek / Sekunden | seconds |

---

## Known Gaps

| Gap | Impact | Status |
|-----|--------|--------|
| No solar irradiance (W/m²) | PV model less accurate | Open — add Open-Meteo or Solcast API |
| No electricity spot price | MPC limited to rule-based | Open — add Tibber or ENTSO-E feed |
| HP COP needs signal name verification | COP panel may show no data until confirmed | Check `greal_E__WMZ_WP` vs actual signal name in parquet |
| 5 truly unknown signals (val1006-1009) | Excluded from modeling | Thesis appendix lookup needed |
| notebook 07_full_eda not yet run | No verified EDA plots | Requires hourly.parquet ✓ (now available) |

---

## Data Source

**Building:** EnFa (Energiefabrik), Germany (~49°N)
**Source system:** InfluxDB BMS/SCADA export
**Format:** Semicolon-delimited CSV, UTF-8, ISO 8601 UTC timestamps
**Domain reference:** Guillet, C. (2016). *Master's Thesis — EnFa Energy System*
**Pipeline target:** ZORO JSON v1 → Kafka → TimescaleDB → Grafana
