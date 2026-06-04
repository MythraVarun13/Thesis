# EnFa Data Analysis — ZORO Energy

EDA of the EnFa commercial building energy dataset: signal classification,
full-data quality profiling, hourly resampling, TimescaleDB ingestion, and Grafana visualization.

**Status:** EDA complete · 215 signals profiled · Hourly Parquet ready · Grafana dashboard live

---

## Getting Started

### 1. Clone this repository

```powershell
# Windows PowerShell
git clone https://github.com/faizanoor3001/ZE.git
cd ZE
```

```bash
# Mac / Linux
git clone https://github.com/faizanoor3001/ZE.git
cd ZE
```

### 2. Install Python dependencies

```powershell
pip install -r requirements.txt
```

> `requirements-dev.txt` is optional — only needed if you want to run tests or contribute code (`pytest`, `ruff`, `black`).

### 3. Get the raw data

The 233 CSV signal files (~40.5 GB) are **not in git** — too large for version control.

Download from Google Drive:

**[EnFa Raw Data — Google Drive](https://drive.google.com/drive/folders/1eQhHjXlCtKwyOO67YyAFa9ZlAwIEV6qF)**

1. Download `data_2026_05_26.zip`
2. Extract the zip
3. Move all `.csv` files into the `data/` folder inside this repo

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

### Step 1 — EDA pipeline

Run the scripts in order from the repo root. Each script takes seconds to run.

```powershell
# Windows PowerShell
python scripts/01_scan_files.py                    # file inventory
python scripts/02_detect_schema.py                 # delimiter, encoding, column names
python scripts/03_profile_timeseries.py            # time coverage and sampling intervals
python scripts/05_classify_signals.py              # signal classification + ZORO pipeline mapping
python scripts/06_signal_profiles.py --threads 6   # full-data quality profiles (~5 min via DuckDB)
```

```bash
# Mac / Linux
python scripts/01_scan_files.py
python scripts/02_detect_schema.py
python scripts/03_profile_timeseries.py
python scripts/05_classify_signals.py
python scripts/06_signal_profiles.py --threads 6
```

> **Note:** There is no `04_` script — step 4 is covered by the interactive notebook
> `notebooks/04_signal_classification.ipynb`. Script 05 runs the same classification logic
> from the command line.

### Step 2 — Resample to hourly Parquet

Reads all 233 signals from the 40 GB raw CSVs via DuckDB and saves a single
`data/processed/hourly.parquet` (~17 MB compressed).
Run once — all further analysis reads from this file.

```powershell
# Windows PowerShell
python scripts/07_resample_hourly.py --threads 6
# Runtime: ~5 minutes
# Output:  data/processed/hourly.parquet
```

```bash
# Mac / Linux
python scripts/07_resample_hourly.py --threads 6
```

### Step 3 — Grafana visualization (optional)

> Steps 1 and 2 are completely self-contained inside this repo.
> Step 3 requires **Docker Desktop** to run TimescaleDB and Grafana locally.
> No other repository is needed — everything is bundled in `docker/`.

#### 3a. Install Docker Desktop

| Platform | Download |
|----------|---------|
| Windows | https://docs.docker.com/desktop/setup/install/windows-install/ |
| Mac | https://docs.docker.com/desktop/setup/install/mac-install/ |
| Linux (Ubuntu/Debian) | `sudo apt install docker.io docker-compose-plugin` |

After installing, start Docker Desktop and wait for the whale icon in the taskbar (Windows/Mac).

#### 3b. Start the local stack

All required config files live in `docker/` inside this repo — no other repository needed.

```powershell
# Windows PowerShell — from the repo root
docker compose -f docker/docker-compose.yml up -d

# Verify both containers are running
docker ps
# Expected:
#   enfa-timescaledb   Up (healthy)
#   enfa-grafana       Up
```

```bash
# Mac / Linux
docker compose -f docker/docker-compose.yml up -d
docker ps
```

> **First start only:** TimescaleDB automatically runs `docker/schema/init.sql`,
> which creates all required tables. Subsequent starts preserve your data.

#### 3c. Load EnFa data into TimescaleDB

Reads `data/processed/hourly.parquet` (produced in Step 2) and inserts
5.18 million hourly observations. Idempotent — safe to re-run.

```powershell
python scripts/08_load_to_timescaledb.py
# Runtime: ~5 minutes
```

#### 3d. Create the Grafana dashboard

```powershell
python scripts/09_create_grafana_dashboard.py
```

Open **http://localhost:3000** — login with **admin / zoro** → navigate to **EnFa Building Analysis**.

#### Stopping and restarting

```powershell
docker compose -f docker/docker-compose.yml down      # stop containers (data preserved)
docker compose -f docker/docker-compose.yml down -v   # stop + wipe all data
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
| `07_resample_hourly.py` | Resample 40 GB → hourly Parquet (correct aggregation per signal type) | ~5 min | `data/processed/hourly.parquet` |
| `08_load_to_timescaledb.py` | Load hourly Parquet into local TimescaleDB | ~5 min | 5.18M rows in `observations` table |
| `09_create_grafana_dashboard.py` | Build and register the Grafana dashboard via API | seconds | Dashboard at localhost:3000 |

All scripts are idempotent — safe to re-run.

> There is no `04_` script. Signal classification at the command line is handled by `05_classify_signals.py`.
> The interactive version is `notebooks/04_signal_classification.ipynb`.

---

## Notebook Reference

| Notebook | Purpose | Requires |
|----------|---------|---------|
| `01_file_inventory.ipynb` | Interactive file browser | — |
| `02_schema_detection.ipynb` | Schema explorer | — |
| `03_timeseries_profiling.ipynb` | Time coverage and sampling | — |
| `04_signal_classification.ipynb` | Signal browser and classification review | `reports/signal_classification.csv` |
| `05_signal_profiles.ipynb` | Interactive signal quality explorer — one signal or category at a time | raw CSVs |
| `06_resample_hourly.ipynb` | Self-contained resampler — same logic as `07_resample_hourly.py`, interactive | raw CSVs |
| `07_full_eda.ipynb` | Full EDA: HP COP, battery, energy balance, correlations | `data/processed/hourly.parquet` |

> `05_signal_profile_explorer.ipynb` is a legacy notebook kept for reference — use `05_signal_profiles.ipynb` instead.

---

## Key Findings

| Finding | Value |
|---------|-------|
| Dataset | 233 CSV files, 40.5 GB, Dec 2022 → May 2026 (live, still growing) |
| Format | UTF-8, semicolon-delimited, InfluxDB schema (`_time`, `_value`, `_measurement`) |
| Dominant sampling interval | ~20 seconds (169 signals) |
| Successfully profiled | 215 signals (15 commissioning snapshots skipped) |
| Pipeline-mapped signals | 223 / 233 |
| Hourly Parquet | 29,207 rows × 215 columns, 16.7 MB compressed |
| TimescaleDB | 5.18 million observations (tenant `enfa-01`) |
| Recommended first MVP | Heat Pump FDD — HP COP trend + defrost anomaly detection |

---

## Grafana Dashboard

After completing Steps 2 and 3, open **http://localhost:3000** (admin / zoro).

Dashboard: **EnFa Building Analysis** (`/d/enfa-overview`)

| Panel | What it shows |
|-------|--------------|
| HP COP daily trend | Heat output / electrical input over 3.5 years |
| WP1 / WP2 / WP3 defrost | Weekly defrost duration per heat pump unit |
| Energy balance monthly | PV + BHKW generation vs building demand |
| Battery SOC | All 4 battery clusters, hourly mean |
| Outdoor temperature | Full 3.5-year record, 6-hour mean |
| Signal browser | Dropdown to explore any of the 215 signals |

The signal browser variable is populated live from TimescaleDB — any new signals loaded via script 08 automatically appear.

---

## Data Architecture

```
EnFa raw CSVs (233 files, 40.5 GB)
    │
    ├─► scripts/06_signal_profiles.py  (DuckDB — no full load into memory)
    │       └── reports/signal_quality_profiles.csv   ← quality scorecard
    │
    └─► scripts/07_resample_hourly.py  (mean / MAX-MIN / sum / last+ffill)
            └── data/processed/hourly.parquet         ← 29K rows × 215 cols, 17 MB
                    │
                    └─► scripts/08_load_to_timescaledb.py  (direct psycopg2 insert)
                            └── TimescaleDB observations   ← 5.18M rows, tenant enfa-01
                                    │
                                    └─► scripts/09_create_grafana_dashboard.py
                                            └── Grafana dashboard ← localhost:3000
```

**Why DuckDB?** It queries CSV files directly from disk with SQL — no loading 40 GB into Python memory.
Aggregations that would take 20+ minutes with pandas take ~30 seconds with DuckDB.

**Aggregation rules for resampling:**

| Signal type | Rule | Example signals |
|-------------|------|----------------|
| Cumulative energy / gas counters | MAX − MIN per hour | `greal_E_*`, `dint*` |
| Defrost duration | SUM per hour | `greal_WP*AbtauSek` |
| Setpoints / control params | LAST per hour + forward-fill | `V_real*` |
| Everything else (temp, power, SOC) | MEAN per hour | most signals |

---

## Project Structure

```
ZE/
├── README.md
├── requirements.txt                    ← install this (everyone)
├── requirements-dev.txt                ← optional (contributors only)
├── config.yaml                         ← project paths and settings
│
├── data/                               ← raw CSVs go here (not in git — too large)
│   ├── processed/
│   │   └── hourly.parquet              ← produced by script 07 (gitignored)
│   ├── samples/
│   └── external/
│
├── docker/                             ← self-contained visualization stack
│   ├── docker-compose.yml              ← starts TimescaleDB + Grafana
│   ├── schema/
│   │   └── init.sql                    ← database schema, applied on first start
│   └── grafana/
│       └── provisioning/
│           ├── datasources/timescaledb.yml
│           └── dashboards/dashboard.yml
│
├── scripts/                            ← command-line pipeline (run in order)
│   ├── 01_scan_files.py
│   ├── 02_detect_schema.py
│   ├── 03_profile_timeseries.py
│   ├── 05_classify_signals.py          ← no 04_ script; see notebooks/04_*
│   ├── 06_signal_profiles.py
│   ├── 07_resample_hourly.py
│   ├── 08_load_to_timescaledb.py
│   └── 09_create_grafana_dashboard.py
│
├── notebooks/                          ← interactive versions of each step
│   ├── 01_file_inventory.ipynb
│   ├── 02_schema_detection.ipynb
│   ├── 03_timeseries_profiling.ipynb
│   ├── 04_signal_classification.ipynb
│   ├── 05_signal_profiles.ipynb
│   ├── 06_resample_hourly.ipynb
│   └── 07_full_eda.ipynb
│
├── src/
│   └── zoro_eda/                       ← shared Python library used by scripts and notebooks
│
├── reports/                            ← all generated outputs land here
│   ├── data_inventory.csv
│   ├── signal_classification.csv
│   ├── zoro_pipeline_mapping.csv
│   ├── signal_quality_profiles.csv
│   ├── resample_log.csv
│   ├── EDA_SUMMARY.md
│   └── plots/
│
└── context/                            ← running analysis notes and session logs
```

---

## Signal Classification

Signal names are German BMS tags. Classification uses three layers:

1. **Prefix convention** — `V_real` = setpoint, `greal` = calculated, `real` = measured, `dint` = counter
2. **German compound word decomposition** — `WP` = heat pump, `Abtau` = defrost, `Sek` = seconds
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
| 5 unidentified signals (`val1006`–`val1009`) | Excluded from modeling | Thesis appendix lookup needed |
| HP COP signal names unverified in Grafana | COP panel may show no data | Verify `greal_E__WMZ_WP` vs actual parquet column names |

---

## Data Source

**Building:** EnFa (Energiefabrik), Germany (~49°N)
**Source system:** InfluxDB BMS/SCADA export
**Format:** Semicolon-delimited CSV, UTF-8, ISO 8601 UTC timestamps
**Domain reference:** Guillet, C. (2016). *Master's Thesis — EnFa Energy System*
