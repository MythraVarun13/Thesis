# ZORO EnFa Dataset — Technical Upskilling Guide

_Last updated: 2026-05-31 | Project root: `C:\Users\dellg\OneDrive\Documents\ZE`_

This document explains the EnFa EDA project end-to-end: what was built, how the scripts work, which reports to use, and how this connects to ZORO’s production ingestion pipeline. Use it to onboard engineers, present to technical leads, or refresh your own understanding.

---

## 1. One-sentence summary

We took **~40 GB of undocumented German building telemetry** (233 CSV exports) and produced a **labeled, time-bounded, pipeline-ready catalog** that shows **what ZORO can build first** — without modifying raw data.

---

## 2. What this project is (and is not)

| **This project is** | **This project is not** |
|---------------------|-------------------------|
| Exploratory data analysis (EDA) on the **EnFa** reference building | A trained ML model or shipped product feature |
| A **decision package**: inventory, parsing rules, signal dictionary, MVP readiness | A replacement for the production repo (`ZoroEnergyPlatform`) |
| A bridge from raw BMS exports → **ZORO JSON v1** (`device_id`, `metric`, `unit`, `timestamp`, `value`) | A full row-by-row quality scan of every file at 40 GB scale (deferred) |

**Business purpose:** Use one well-instrumented German site as a **reference dataset** to validate ingestion, dashboards, heat-pump fault detection, and customer demos — in parallel with live customers (e.g. SCS).

**Domain:** Multi-source commercial building — 3 heat pumps (WP), 2 CHP units (BHKW), 7 PV strings, 4-cluster battery, DHW, heating zones, 3 EV chargers, weather. Data from **2022-12-07 → 2026-05-27** (~3.5 years BMS; weather/solar geometry from ~2024-02).

---

## 3. Project layout — who opens what

```
ZE/
├── data/                          ← RAW CSVs (~40.5 GB). READ-ONLY. Never edit.
├── scripts/                       ← Reproducible EDA pipeline (Python)
├── reports/                       ← Deliverables (share with team / CEO HTML)
│   ├── ZORO_CEO_Briefing.html     ← CEO / investors (non-technical)
│   ├── EnFa_Signal_Data_Catalog.html  ← Engineers: searchable signal catalog
│   ├── EDA_SUMMARY.md             ← Full 16-section technical report
│   ├── *.csv                      ← Machine-readable tables
│   ├── sample_rows/               ← ≤20 rows per file for quick inspection
│   └── plots/                     ← Charts (regenerate locally; see §8)
├── context/                       ← Analyst memory across sessions (internal)
├── docs/                          ← This guide and related documentation
├── inputs/thesis/                 ← Thesis text extract (secondary to PDF)
└── CLAUDE.md                      ← Master project specification
```

| Path | Audience | Purpose |
|------|----------|---------|
| `reports/ZORO_CEO_Briefing.html` | CEO, investors | One-page story: building, stats, products, recommended MVP |
| `reports/EnFa_Signal_Data_Catalog.html` | Engineers, PM | Ctrl+F any signal: time window, English name, ZORO metric |
| `reports/EDA_SUMMARY.md` | Technical lead | Full analysis (16 sections) |
| `reports/*.csv` | Data / backend | Tables behind the HTML catalogs |
| `context/` | Analysts / AI sessions | Running notes — **not** for external sharing |
| `context/zoro_pipeline_context.md` | Integration engineers | Production MQTT → Kafka → TimescaleDB |

---

## 4. End-to-end workflow (mental model)

```
data/ (233 CSV, read-only)
    │
    ▼
01_scan_files.py          → data_inventory.csv
    ▼
02_detect_schema.py       → file_format_report, schema_summary, sample_rows/
    ▼
03_profile_timeseries.py  → timestamp_coverage, sampling_interval reports
    ▼
05_classify_signals.py    → signal_classification, zoro_pipeline_mapping,
                            zoro_mvp_readiness_matrix, sensor_catalog
    ▼
reports/EDA_SUMMARY.md + HTML catalogs
    │
    └──► (separate repo) ZoroEnergyPlatform: CSV → JSON v1 → MQTT → TimescaleDB
```

**Design rule:** Never load the full ~40 GB into memory. Scripts use **head/tail sampling**, small byte windows, or (future) DuckDB SQL on files.

---

## 5. Reports reference (plain English)

| Report | What it answers |
|--------|-----------------|
| `data_inventory.csv` | What files exist and how large they are |
| `file_format_report.csv` | How to read each file: delimiter, encoding |
| `schema_summary.csv` | Column layout per file |
| `timestamp_coverage_report.csv` | Per signal: start time, end time, duration |
| `sampling_interval_report.csv` | How often each signal is recorded |
| `duplicate_timestamp_report.csv` | Duplicate timestamp hints (not exhaustive full scan) |
| `missing_values_report.csv` | Missing-value hints from samples |
| `signal_classification.csv` | German tag → category, English meaning, unit, confidence |
| `zoro_pipeline_mapping.csv` | Same signals → `zoro_device_id_suffix`, `zoro_metric`, `zoro_unit` |
| `zoro_mvp_readiness_matrix.csv` | Which ZORO product lines are Ready / Partial / etc. |
| `sensor_catalog.csv` | Consolidated sensor reference |
| `reports/sample_rows/<name>_sample.csv` | Up to 20 rows per raw file |

**Bookmark for daily work:** `reports/EnFa_Signal_Data_Catalog.html` — “Do we have signal X, for how long, and what is it called in the pipeline?”

---

## 6. Key findings (talk track)

Sourced from `reports/EDA_SUMMARY.md` and `reports/zoro_mvp_readiness_matrix.csv`.

### Data quality

- **233** valid CSV files, **one** schema, semicolon delimiter, UTF-8.
- **~40.5 GB** total (larger than initial ~2.5 GB estimate).
- BMS coverage **~3.5 years**; data **current through 2026-05-27** (operational, not a dead archive).
- Dominant sampling **~20 seconds** on core BMS signals (169 files).
- **15** commissioning snapshot files (≤8 rows) — exclude from modeling.
- **3** artifact files (`pilot.csv`, `A.csv`, `_value.csv`) — excluded.

### Building systems (customer language)

| System | What the data shows |
|--------|---------------------|
| Heat | 3 heat pumps + 2 BHKW/CHP, zones (Nord, Süd, Halle), DHW, buffer tanks |
| Electricity | 7 PV strings, battery (4 clusters), grid/building meters, 3 EV chargers |
| Controls | Heating curve, night setback, high-tariff flag (`greal_Administrator_HT`), battery–HP interlock |

### MVP readiness

| MVP path | Readiness | Notes |
|----------|-----------|-------|
| A: Energy analytics dashboard | **Ready** | PV, battery, BHKW, building load, gas, EV |
| B: HVAC optimization advisory | **Ready** | Curves, setpoints, zones, outdoor temp |
| C: Heat pump FDD | **Ready** — **recommended first** | 3 HP units, defrost at ~20 s, COP estimable |
| Battery / EV optimization | **Ready** (secondary) | No spot price for price-optimal dispatch |
| PV forecasting | Partially ready | Sun geometry yes; irradiance W/m² not confirmed |
| MPC / price-optimal | Partially ready | States/controls yes; need spot price feed |
| EnergyPlus calibration | Partially ready | Missing zone temps + building geometry in CSVs |

### Gaps (stay honest)

- No confirmed **room comfort temperatures** for all zones.
- No confirmed **solar irradiance** (W/m²); `val1008`/`val1009` may be candidates — needs thesis/BMS confirmation.
- No **electricity spot price** — only binary HT tariff flag.
- **5 unknown signals** (`val1006`–`val1009` + related).
- **Full** mid-series gap/duplicate analysis not run on entire 40 GB (planned with DuckDB).

### Recommended first product slice

**Heat pump performance & fault detection (Path C):**

- COP ≈ `greal_WMZ_Hz_Erz_WP` (heat) ÷ `greal_E_WP` (electric).
- Defrost trends: `greal_WP1AbtauSek`, `greal_WP2AbtauSek`, `greal_WP3AbtauSek`.
- Supply vs heating curve: `grealIstWaermepumpVorlauf` vs `greal_VorlaufTempKennlinie`.

Example customer narrative (replace € with modeled savings):

> “We can detect when Heat Pump 2’s defrost cycles drift from a 3-year baseline and alert before efficiency loss becomes a breakdown — using data ingestible into our pipeline today.”

---

## 7. Scripts — pipeline order and technology

### 7.1 Scripts that exist today

| Script | Input | Technique | Outputs |
|--------|-------|-----------|---------|
| `01_scan_files.py` | `data/` walk | `os.walk`, `pathlib`, `csv` | `reports/data_inventory.csv` |
| `02_detect_schema.py` | First **6 KB** per file | Delimiter voting (`;`, `,`, `\t`, `\|`); encoding UTF-8/BOM/Latin-1 | `file_format_report.csv`, `schema_summary.csv`, `sample_rows/` |
| `03_profile_timeseries.py` | Head ~30 rows + tail ~4 KB | ISO 8601 UTC parse; median interval | `timestamp_coverage_report.csv`, `sampling_interval_report.csv` |
| `05_classify_signals.py` | File stems + rules | Exact map + substring rules on German BMS names | `signal_classification.csv`, `zoro_pipeline_mapping.csv`, `zoro_mvp_readiness_matrix.csv`, context updates |
| `08_generate_plots.py` | Sampled CSV rows | `matplotlib` (Agg), capped rows | `reports/plots/*.png` |
| `generate_flowchart.py` | — | `matplotlib` patches | `reports/plots/00_eda_pipeline_flowchart.png` |

### 7.2 Scripts planned (not built yet)

Per `CLAUDE.md` and `context/next_steps.md`:

- `04_data_quality_report.py` — deeper quality (prefer DuckDB).
- `06_generate_samples.py` — 30-day extracts for top signals → `data/samples/`.
- `07_resample_timeseries.py` — uniform intervals for modeling.
- `09_generate_final_report.py` — regenerate consolidated reports.
- `src/zoro_eda/` — shared Python modules (not created yet).

### 7.3 How to run (from project root)

Activate venv if present:

```powershell
cd C:\Users\dellg\OneDrive\Documents\ZE
.\.venv\Scripts\Activate.ps1
```

Run in order:

```powershell
python scripts/01_scan_files.py --raw-dir "C:\Users\dellg\OneDrive\Documents\ZE\data"
python scripts/02_detect_schema.py --raw-dir "C:\Users\dellg\OneDrive\Documents\ZE\data"
python scripts/03_profile_timeseries.py --raw-dir "C:\Users\dellg\OneDrive\Documents\ZE\data"
python scripts/05_classify_signals.py --raw-dir "C:\Users\dellg\OneDrive\Documents\ZE\data"
```

Before running plot scripts, set `DATA_DIR` and `PLOTS_DIR` in `08_generate_plots.py` and `OUT` in `generate_flowchart.py` to your local `ZE` paths (they may still point at a cloud session path).

### 7.4 Raw CSV format (InfluxDB export)

Typical columns (semicolon-separated):

```
Unnamed: 0 ; _time ; _value ; _field ; _measurement
```

- **`_time`:** ISO 8601 UTC, e.g. `2022-12-14T14:40:41Z`
- **`_value`:** numeric measurement
- **`_field`:** usually `value`
- **`_measurement`:** signal name (often matches file stem)
- **`Unnamed: 0`:** empty export artifact — ignore

Excel will show garbage unless you import with **semicolon** delimiter.

### 7.5 Signal naming prefixes

| Prefix | Meaning | Example |
|--------|---------|---------|
| `V_real` / `Vreal` | Setpoint / configuration | `V_real_maxVorlaufTemp` |
| `greal` | Calculated / aggregated | `greal_LeistungGebaeude` |
| `real` | Measured raw | `real_BatterieLeistung` |
| `green` | Battery cluster raw | `green_bat` |
| `dint` | Counter / pulse integral | gas volume impulses |
| `grealCluster` | Battery cluster aggregated | `grealCluster_1_Spannung` |

### 7.6 German keyword cheat sheet

| German | English |
|--------|---------|
| AT | Outdoor temperature |
| Vorlauf / Rücklauf | Supply / return temperature |
| WP | Heat pump (Wärmepumpe) |
| BHKW | CHP |
| PV | Photovoltaic |
| SOC / LadeZustand | State of charge |
| Abtau | Defrost |
| WMZ | Heat meter |
| FBH | Underfloor heating |
| BKT | Concrete core activation |
| Nachtabsenkung | Night setback |
| Soll / Ist | Setpoint / actual |

Full table: `CLAUDE.md` §9 and `context/signal_dictionary.md`.

---

## 8. Python stack

From `requirements.txt`:

| Package | Role |
|---------|------|
| pandas | Tables and summaries |
| numpy | Numerics |
| matplotlib | Plots |
| charset-normalizer | Encoding detection |
| python-dateutil | Timestamps |
| openpyxl | Excel if needed |

**Planned (install when doing full-file SQL):** polars, duckdb, pyarrow, tqdm — ask before adding heavy ML stacks (scikit-learn, torch, etc.).

---

## 9. Production ZORO pipeline connection

Detailed in `context/zoro_pipeline_context.md`. Production repo: **`C:\Users\dellg\OneDrive\Documents\ZoroEnergyPlatform`** (branch `main`).

```
Customer MQTT (MQTTS)
    → zoro-mqtt-bridge
    → Kafka  zoro.prod.raw.{tenant}.v1
    → zoro-format-adapter  (JSON v1 parser)
    → Kafka  zoro.prod.obs.{tenant}.v1
    → zoro-kafka-writer
    → TimescaleDB
    → REST API + Grafana
```

**JSON v1 observation** (required fields):

- `timestamp`, `device_id`, `metric`, `value` (numeric), `unit`

**EnFa mapping:** `reports/zoro_pipeline_mapping.csv` — **223 of 233** signals mapped. Example:

| Raw signal | device suffix | metric | unit |
|------------|---------------|--------|------|
| `greal_BatterieLadeZustand` | `battery-system` | `battery_soc` | `%` |
| `greal_WP2AbtauSek` | `heat-pump` | `defrost_duration` | `s`` |

Full `device_id` in production typically follows tenant/site conventions (e.g. `de-enfa-main-01/heat-pump`).

**Next integration step:** CSV → JSON v1 replay script → dev MQTT → `sanity_test.sh` in ZoroEnergyPlatform.

---

## 10. Learning path (self-paced)

### Level 0 — Navigate (≈1 hour)

1. Read `reports/EDA_SUMMARY.md` §§1, 9, 11, 12, 15.
2. Open `reports/EnFa_Signal_Data_Catalog.html` — search `greal_WP2AbtauSek`, `greal_BatterieLadeZustand`.
3. Open one file in `reports/sample_rows/`.

### Level 1 — Trace one signal (≈half day)

For `greal_WP2AbtauSek`:

1. `reports/sample_rows/greal_WP2AbtauSek_sample.csv` — raw shape
2. `timestamp_coverage_report.csv` — start/end/duration
3. `sampling_interval_report.csv` — ~20 s?
4. `signal_classification.csv` — category, English, confidence
5. `zoro_pipeline_mapping.csv` — `device_id` / `metric` / `unit`
6. Imagine one JSON v1 MQTT payload for `format_adapter.py`

### Level 2 — Run the pipeline

1. Fix plot script paths; run `01` → `05`.
2. Read `02_detect_schema.py` — note `HEAD_BYTES = 6144` pattern.
3. Read `05_classify_signals.py` — `DM` exact map vs `RULES` patterns.

### Level 3 — Extend

1. DuckDB: `SELECT ... FROM 'data/greal_WP2AbtauSek.csv'` with semicolon options.
2. Build `06_generate_samples.py` (30-day slices).
3. HP COP batch job on TimescaleDB after replay.

---

## 11. Trace exercise: `greal_WP2AbtauSek`

**Physical meaning:** Heat pump unit 2 defrost duration (seconds).

| Step | File / field |
|------|----------------|
| Raw file | `data/greal_WP2AbtauSek.csv` |
| Category | `hp_defrost` |
| English | Heat pump defrost duration |
| Unit | `s` |
| ZORO metric | `defrost_duration` on device suffix `heat-pump` |
| Use cases | `use_heatpump`, `use_fdd` flags in mapping CSV |
| MVP | Heat Pump FDD (Ready) |

**Why it matters:** ~20 s resolution over 3.5 years enables baseline + anomaly detection on defrost behavior — rare in typical 15-minute utility data.

---

## 12. ZE folder vs ZoroEnergyPlatform

| **ZE (this repo)** | **ZoroEnergyPlatform** |
|--------------------|-------------------------|
| Offline CSV EDA | Live MQTT/Kafka ingestion |
| Historical exports | GCP, Confluent, TimescaleDB |
| “What data exists?” | “How we run production” |
| CSV/HTML reports | Bridges, adapters, API, Grafana |

EnFa EDA **de-risks** production; it does not replace it.

---

## 13. Quick lookup

| Question | Where |
|----------|-------|
| Do we have signal X? | `reports/EnFa_Signal_Data_Catalog.html` |
| What can we build? | `reports/zoro_mvp_readiness_matrix.csv` |
| How do we ingest it? | `reports/zoro_pipeline_mapping.csv` |
| Full technical story? | `reports/EDA_SUMMARY.md` |
| Production ingest? | `context/zoro_pipeline_context.md` |
| What was done when? | `context/session_log.md` |
| Project rules? | `CLAUDE.md` |

---

## 14. EDA completion status

Per `context/session_log.md` — **EDA phase marked complete** for CLAUDE.md deliverables.

**Still open:**

- Thesis appendix → resolve `val1006`–`val1009`, irradiance
- Full 40 GB gap/duplicate scan (DuckDB)
- Plot regeneration with local paths
- `06_generate_samples.py`, HP COP script, CSV→JSON v1 replay
- Modular `src/zoro_eda/` package

---

## 15. Related documents

| Document | Path |
|----------|------|
| Code review (readability & maintainability) | `docs/CODE_REVIEW.md` |
| CEO briefing (HTML) | `reports/ZORO_CEO_Briefing.html` |
| CEO upskilling (markdown) | `docs/ZORO_CEO_Upskilling.md` (if created) |
| Master spec | `CLAUDE.md` |
| Session history | `context/session_log.md` |

---

*Maintained as part of the ZORO EnFa EDA project. Update this file when scripts, reports, or pipeline contracts change.*
