# EnFa Data Analysis — ZORO Energy

EDA of the EnFa commercial building energy dataset to determine which ZORO MVP paths
are feasible and how to ingest the data into the production pipeline.

**Status:** EDA complete · 223/233 signals pipeline-ready · Recommended MVP: Heat Pump FDD

---

## Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.10 | 3.11+ also supported |
| pip | any recent | comes with Python |
| Git | any | for cloning |
| Jupyter | optional | only needed to open `.ipynb` notebooks |

No database, no Docker, no cloud account needed to run the analysis scripts.

---

## Quick Start (Mac / Linux)

```bash
# 1. Clone or navigate to the project
cd /path/to/ZE

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Edit config.yaml if your data is in a non-standard location
#    By default the scripts auto-detect the project root from their own path.
#    See "Configuration" below if you need to override.

# 5. Run the analysis pipeline in order
python scripts/01_scan_files.py
python scripts/02_detect_schema.py
python scripts/03_profile_timeseries.py
python scripts/05_classify_signals.py
python scripts/08_generate_plots.py

# 6. Run unit tests to verify everything works
python -m pytest tests/ -v
# (or without pytest: python -m unittest discover -s tests)

# 7. Open notebooks for a step-by-step explained walkthrough
pip install jupyter
jupyter notebook notebooks/
```

## Quick Start (Windows — PowerShell)

```powershell
# 1. Navigate to the project
cd "C:\path\to\ZE"

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the pipeline
python scripts/01_scan_files.py
python scripts/02_detect_schema.py
python scripts/03_profile_timeseries.py
python scripts/05_classify_signals.py
python scripts/08_generate_plots.py

# 5. Run tests
python -m pytest tests/ -v

# 6. Open notebooks
pip install jupyter
jupyter notebook notebooks/
```

> **Windows execution policy:** If PowerShell blocks `.ps1` scripts, run:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

## Configuration

All paths and settings live in `config.yaml` at the project root.
**You should not need to edit this for a standard setup** — scripts
auto-detect the project root by looking for `config.yaml` walking up from
their own directory.

If your raw data is in a non-standard location, either:

**Option A — edit `config.yaml`:**
```yaml
paths:
  project_root: "/your/path/to/ZE"   # absolute path, forward slashes work on all platforms
  raw_data: "data"                    # relative to project_root
```

**Option B — use CLI flags (any platform):**
```bash
python scripts/01_scan_files.py --raw-dir /your/path/to/ZE/data
```

**Option C — environment variable:**
```bash
export ZORO_PROJECT_ROOT=/your/path/to/ZE   # Mac/Linux
set ZORO_PROJECT_ROOT=C:\your\path\to\ZE    # Windows CMD
$env:ZORO_PROJECT_ROOT="C:\your\path\to\ZE" # Windows PowerShell
```

---

## What This Project Does

We received 233 CSV files (~40.5 GB) from an InfluxDB export of the EnFa building BMS.
The files have German signal names, no documentation, and no tag dictionary.

This project:
1. Inventories all files (sizes, formats, encodings)
2. Detects CSV schema across all 233 files (head-only, no full loads)
3. Profiles time coverage per signal (start date, end date, sampling interval)
4. Parses the German thesis PDF to interpret signal names
5. Classifies each signal (English meaning, unit, confidence, ZORO use cases)
6. Maps each signal to ZORO's JSON v1 pipeline format
7. Evaluates which ZORO MVP paths are feasible
8. Generates plots and a data catalog

**Key constraint:** The dataset is 40.5 GB. Scripts read only the first 6 KB
(head) or last 4 KB (tail) of each file — never the full content.

---

## Script → Output Map

| Script | What it does | Key outputs |
|--------|-------------|-------------|
| `01_scan_files.py` | File inventory (metadata only) | `reports/data_inventory.csv` |
| `02_detect_schema.py` | Delimiter, encoding, schema | `reports/file_format_report.csv`, `reports/sample_rows/` |
| `03_profile_timeseries.py` | Start/end dates, sampling intervals | `reports/timestamp_coverage_report.csv` |
| `05_classify_signals.py` | German→English, unit, pipeline mapping | `reports/signal_classification.csv`, `reports/zoro_pipeline_mapping.csv` |
| `08_generate_plots.py` | 12 exploratory plots | `reports/plots/01_*.png` → `12_*.png` |

All scripts are **idempotent** — re-running overwrites the same output files with fresh results.

---

## Running Tests

```bash
# With pytest (recommended — install via requirements-dev.txt)
pip install -r requirements-dev.txt
pytest tests/ -v

# Without pytest (stdlib only)
python -m unittest discover -s tests -v

# Or run a specific test file
python tests/test_parse_ts.py
```

Tests cover:
- `test_parse_ts.py` — 9 cases for timestamp parsing (Z suffix, milliseconds, bad input)
- `test_match_signal.py` — 15 cases for signal classification (direct map, patterns, unknowns)
- `test_delimiter_detection.py` — 9 cases for CSV delimiter detection (semicolon, comma, tab)

---

## Key Findings

| Finding | Value |
|---------|-------|
| Data runs to | May 2026 (live, not historical) |
| All 233 files | UTF-8, semicolon-delimited, standard InfluxDB schema |
| Dominant interval | ~20 seconds (169 signals) |
| Pipeline-ready signals | 223 / 233 |
| Recommended first MVP | Heat Pump FDD |

---

## Project Structure

```
ZE/
├── README.md                          ← you are here
├── CLAUDE.md                          ← project instructions for AI assistant
├── config.yaml                        ← all paths and settings
├── requirements.txt                   ← production dependencies
├── requirements-dev.txt               ← dev/test dependencies (pytest, ruff, black)
├── .gitignore
│
├── data/
│   ├── *.csv                          ← 233 raw signal files — READ ONLY, not in git
│   ├── processed/                     ← cleaned/resampled outputs (gitignored)
│   └── samples/                       ← 30-day samples for prototyping (gitignored)
│
├── src/
│   └── zoro_eda/                      ← shared Python library (imported by all scripts)
│       ├── __init__.py
│       ├── config.py                  ← load_config() — reads config.yaml
│       ├── paths.py                   ← ProjectPaths dataclass, resolve_paths()
│       ├── csv_io.py                  ← parse_timestamp, detect_delimiter, read_head, read_tail
│       ├── classify.py                ← classify_signal(), SignalClassification dataclass
│       └── signal_rules.py            ← DIRECT_MAP + PATTERN_RULES (classification data)
│
├── scripts/
│   ├── 01_scan_files.py               ← Step 1: file inventory
│   ├── 02_detect_schema.py            ← Step 2: schema detection
│   ├── 03_profile_timeseries.py       ← Step 3: time-series profiling
│   ├── 05_classify_signals.py         ← Step 4: signal classification
│   └── 08_generate_plots.py           ← Step 5: exploratory plots
│
├── notebooks/
│   ├── 01_file_inventory.ipynb        ← What files do we have?
│   ├── 02_schema_detection.ipynb      ← How are they formatted?
│   ├── 03_timeseries_profiling.ipynb  ← What time windows?
│   └── 04_signal_classification.ipynb ← What does each signal mean?
│
├── tests/
│   ├── conftest.py                    ← pytest path setup
│   ├── test_parse_ts.py               ← timestamp parsing tests
│   ├── test_match_signal.py           ← signal classification tests
│   └── test_delimiter_detection.py    ← CSV delimiter detection tests
│
├── reports/
│   ├── ZORO_CEO_Briefing.html         ← Open in browser — CEO summary
│   ├── EnFa_Signal_Data_Catalog.html  ← Open in browser — searchable signal reference
│   ├── EDA_SUMMARY.md                 ← Full written EDA report
│   ├── signal_classification.csv      ← Master signal table (all 233 signals)
│   ├── zoro_pipeline_mapping.csv      ← 223 signals mapped to JSON v1
│   ├── zoro_mvp_readiness_matrix.csv  ← Per-MVP-path readiness scoring
│   └── plots/
│       ├── 00_eda_pipeline_flowchart.png
│       └── 01–13_*.png
│
└── context/                           ← Running analysis notes (not for sharing)
    ├── thesis_context.md
    ├── signal_dictionary.md
    └── ...
```

---

## Signal Classification — How It Works

Signal names are German compound words from the BMS tag list.
Classification uses three layers in priority order:

**Layer 1 — Exact match** (`signal_rules.DIRECT_MAP`)
Handles edge cases: umlaut variants, underscores in unusual positions.
Example: `grealIstWaermepumpVorlauf` → heat pump supply temperature.

**Layer 2 — Pattern matching** (`signal_rules.PATTERN_RULES`)
All listed substrings must be present (case-insensitive) in the signal name.
Example: `["greal_wp", "abtau"]` matches `greal_WP1AbtauSek` → HP defrost duration.

**Layer 3 — Fallback**
`category="unknown"`, `confidence="low"`, not excluded — manual review needed.

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
| FBH / Fußbodenheizung | underfloor heating |
| Nachtabsenkung | night setback |
| Speicher | storage / tank |
| Sek / Sekunden | seconds |

---

## Dependencies

`requirements.txt` (production):
```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
charset-normalizer>=3.0
python-dateutil>=2.8
```

`requirements-dev.txt` (development):
```
pytest>=7.0
pytest-cov>=4.0
ruff>=0.4
black>=24.0
```

Optional extras:
```bash
pip install jupyter          # to run notebooks
pip install pyyaml           # to read config.yaml (scripts fall back to defaults without it)
```

**No PyYAML required** — `config.py` falls back to built-in defaults if PyYAML is not installed.
Scripts will still work; they just won't read overrides from `config.yaml`.

**pdftotext** (only needed to re-extract thesis text):
- Mac: `brew install poppler`
- Linux: `sudo apt install poppler-utils`
- Windows: download Poppler for Windows from https://github.com/oschwartz10612/poppler-windows

---

## Known Gaps

| Gap | Impact | Suggested Fix |
|-----|--------|--------------|
| No solar irradiance (W/m²) | PV model less accurate | Add Open-Meteo or Solcast API to pipeline |
| No electricity spot price | MPC limited to rule-based | Add Tibber or ENTSO-E feed |
| 15 snapshot-only files (≤8 rows) | Exclude from modeling | Already excluded in `zoro_pipeline_mapping.csv` |
| Full gap/duplicate scan not done | Unknown mid-series holes | Run on resampled subset using DuckDB |

---

## Data Source

**Building:** EnFa (Energiefabrik), Germany (~49°N)
**Source system:** InfluxDB BMS/SCADA export
**Format:** Semicolon-delimited CSV, UTF-8, ISO 8601 UTC timestamps
**Domain reference:** Guillet, C. (2016). *Master's Thesis — EnFa Energy System*
**Pipeline target:** ZORO JSON v1 → Kafka → TimescaleDB → Grafana
