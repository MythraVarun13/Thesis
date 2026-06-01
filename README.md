# EnFa Data Analysis — ZORO Energy

EDA of the EnFa commercial building energy dataset to determine which ZORO MVP paths are feasible and how to ingest the data into the production pipeline.

**Status:** EDA complete · 223/233 signals pipeline-ready · Recommended MVP: Heat Pump FDD

---

## Quick Start

```bash
# 1. Clone / open this folder
cd "C:\Users\dellg\OneDrive\Documents\ZE"

# 2. Install dependencies (system Python — no venv needed in sandbox)
pip install pandas numpy matplotlib charset-normalizer python-dateutil

# 3. Run the full analysis pipeline in order
python scripts/01_scan_files.py
python scripts/02_detect_schema.py
python scripts/03_profile_timeseries.py
python scripts/05_classify_signals.py
python scripts/08_generate_plots.py

# OR: open the Jupyter notebooks for an explained walkthrough
jupyter notebook notebooks/
```

---

## What This Project Does

We received 233 CSV files (~40.5 GB) from an InfluxDB export of the EnFa building's BMS. These files have German signal names, no documentation, and no tag dictionary. This project:

1. Inventories all files (sizes, formats, encodings)
2. Detects CSV schema across all 233 files
3. Profiles time coverage per signal (start date, end date, sampling interval)
4. Parses the German thesis PDF to interpret signal names
5. Classifies each signal (English meaning, unit, confidence)
6. Maps each signal to ZORO's JSON v1 pipeline format
7. Evaluates which ZORO MVP paths are feasible
8. Generates plots and a data catalog for the team

---

## Script → Output Map

| Script | What it does | Outputs |
|--------|-------------|---------|
| `scripts/01_scan_files.py` | Count and size all files | `reports/data_inventory.csv` |
| `scripts/02_detect_schema.py` | Detect delimiter, encoding, columns | `reports/file_format_report.csv`<br>`reports/schema_summary.csv`<br>`reports/sample_rows/*.csv` |
| `scripts/03_profile_timeseries.py` | Start/end dates, intervals, gaps | `reports/timestamp_coverage_report.csv`<br>`reports/sampling_interval_report.csv` |
| `scripts/05_classify_signals.py` | German→English, unit, use-case tagging | `reports/signal_classification.csv`<br>`reports/sensor_catalog.csv`<br>`reports/zoro_pipeline_mapping.csv`<br>`context/signal_dictionary.md` |
| `scripts/08_generate_plots.py` | 12 thematic exploratory plots | `reports/plots/01_*.png` → `12_*.png` |
| `scripts/generate_flowchart.py` | EDA pipeline diagram | `reports/plots/00_eda_pipeline_flowchart.png` |

**Manually generated outputs:**

| Output | How |
|--------|-----|
| `reports/zoro_mvp_readiness_matrix.csv` | Written from analysis findings |
| `reports/EDA_SUMMARY.md` | 16-section written report |
| `reports/EnFa_Signal_Data_Catalog.html` | Python script (inline, not saved) |
| `reports/ZORO_CEO_Briefing.html` | Python script (inline, not saved) |
| `reports/plots/13_signal_gallery_*.png` | `/tmp/gallery.py` |

---

## Key Findings

- **Data runs to May 2026** — this is live operational data, not historical
- **All 233 files**: UTF-8, semicolon-delimited, standard InfluxDB schema — 100% consistent
- **Dominant sampling interval**: ~20 seconds (169 signals)
- **223 of 233 signals** are mapped to ZORO JSON v1 format (`device_id`, `metric`, `unit`)
- **3 MVP paths are Ready**: Energy Dashboard, HVAC Advisory, Heat Pump FDD
- **Recommended first MVP**: Heat Pump FDD — 3 HP units, 3.5 years, defrost at 20s resolution

---

## Project Structure

```
ZE/
├── README.md                          ← you are here
├── CLAUDE.md                          ← project instructions for AI assistant
├── config.yaml                        ← all paths and settings (edit here, not in scripts)
├── requirements.txt                   ← Python dependencies
│
├── data/
│   ├── *.csv                          ← 233 raw signal files (READ ONLY)
│   ├── processed/                     ← cleaned/resampled outputs
│   └── samples/                       ← 30-day samples for prototyping
│
├── scripts/
│   ├── 01_scan_files.py               ← Step 1: file inventory
│   ├── 02_detect_schema.py            ← Step 2: schema detection
│   ├── 03_profile_timeseries.py       ← Step 3: time coverage profiling
│   ├── 05_classify_signals.py         ← Step 4: signal classification
│   └── 08_generate_plots.py           ← Step 5: exploratory plots
│
├── notebooks/
│   ├── 01_file_inventory.ipynb        ← Explained: what files do we have?
│   ├── 02_schema_detection.ipynb      ← Explained: how are they formatted?
│   ├── 03_timeseries_profiling.ipynb  ← Explained: what time windows?
│   └── 04_signal_classification.ipynb ← Explained: what does each signal mean?
│
├── reports/
│   ├── ZORO_CEO_Briefing.html         ← Open in browser — CEO summary
│   ├── EnFa_Signal_Data_Catalog.html  ← Open in browser — searchable signal reference
│   ├── EDA_SUMMARY.md                 ← Full written EDA report
│   ├── data_inventory.csv
│   ├── file_format_report.csv
│   ├── schema_summary.csv
│   ├── timestamp_coverage_report.csv
│   ├── sampling_interval_report.csv
│   ├── signal_classification.csv      ← Master signal table
│   ├── sensor_catalog.csv             ← Active signals only
│   ├── zoro_pipeline_mapping.csv      ← JSON v1 mapping (use this for ingestion)
│   ├── zoro_mvp_readiness_matrix.csv
│   └── plots/
│       ├── 00_eda_pipeline_flowchart.png
│       ├── 01–12_*.png                ← Thematic plots
│       └── 13_signal_gallery_*.png    ← Per-signal mini plots
│
├── context/                           ← AI assistant running notes (not for sharing)
│   ├── thesis_context.md
│   ├── signal_dictionary.md
│   ├── zoro_use_case_mapping.md
│   ├── physical_system_hypotheses.md
│   └── ...
│
└── inputs/
    └── thesis/
        └── thesis_full.txt            ← Extracted text from Guillet 2016 PDF
```

---

## Signal Classification — How It Works

Signal names are German compound words from the BMS tag list. Classification uses four layers:

**1. Prefix convention** (reliable, high confidence)
- `V_real` / `Vreal` → setpoint / configuration parameter
- `greal` → calculated / aggregated value
- `real` → raw measured value
- `grealCluster` → battery cluster data
- `green` → battery cluster raw (SMA Sunny Island)
- `dint` → counter / pulse integral

**2. German compound word decomposition**
- `Vorlauf` = supply flow temperature
- `Ruecklauf` = return flow temperature
- `WP` = Wärmepumpe (heat pump)
- `BHKW` = Blockheizkraftwerk (CHP/combined heat and power)
- `Abtau` = defrost
- `Sek` = seconds
- `Leistung` = power
- `Energie` / `E_` = energy
- `Ladung` / `Lade` = charge
- `Speicher` = storage
- `Nachtabsenkung` = night setback
- `WMZ` = Wärmemengenzähler (heat meter)
- `FBH` = Fußbodenheizung (underfloor heating)
- `BKT` = Betonkerntemperierung (concrete core activation)

**3. Value range sanity check** (resolves ambiguous names)
- 0–100 → likely SOC (%) or valve position
- 15–80 → likely temperature (°C)
- Negative possible → power signal (kW, can import/export)
- Always positive → energy counter (kWh, cumulative)

**4. Thesis confirmation** (Guillet 2016, Table 25)
- Cross-referenced key signals against documented database variables

**Use-case tags explained:**
- `use_energy` — measures energy flow: generation, consumption, storage
- `use_hvac` — temperatures, thermal power, setpoints, zone control
- `use_heatpump` — HP-specific: defrost, COP inputs, HP setpoints
- `use_pv` — PV generation and forecasting signals
- `use_battery` — battery SOC, charge/discharge power, cluster data
- `use_weather` — outdoor conditions used as model inputs
- `use_fdd` — fault detection: loss signals, defrost, phase currents, anomaly indicators
- `use_mpc` — model predictive control needs: states + control actions + disturbances

Confidence levels:
- `high` — name + prefix + value range all consistent; thesis or direct confirmation
- `medium` — name interpretation is reasonable but unit or exact meaning uncertain
- `low` — no rule matched or genuinely ambiguous; manual review needed

---

## Known Gaps

| Gap | Impact | Suggested Fix |
|-----|--------|--------------|
| No solar irradiance (W/m²) | PV model less accurate | Add Open-Meteo or Solcast API to pipeline |
| No electricity spot price | MPC limited to rule-based | Add Tibber or ENTSO-E feed |
| 15 snapshot-only files (≤8 rows) | Exclude from modeling | Already excluded in `zoro_pipeline_mapping.csv` |
| Hardcoded paths in scripts | Not portable | Use `config.yaml` — refactor in progress |
| Full gap/duplicate scan not done | Unknown mid-series holes | Run DuckDB query on resampled data |

---

## Dependencies

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
charset-normalizer>=3.0
python-dateutil>=2.8
jupyter           # for notebooks
pdftotext         # system package — sudo apt install poppler-utils
```

---

## Data Source

**Building:** EnFa (Energiefabrik), Germany (~49°N)
**Source system:** InfluxDB BMS/SCADA export
**Format:** Semicolon-delimited CSV, UTF-8, ISO 8601 UTC timestamps
**Domain reference:** Guillet, C. (2016). *Master's Thesis — EnFa Energy System*
**Pipeline target:** ZORO JSON v1 → Kafka → TimescaleDB → Grafana
