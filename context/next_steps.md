# Next Steps

_Last updated: 2026-05-31_

## ~~Step 2 — COMPLETE~~

Schema detection done. All 233 files: UTF-8, semicolon-delimited, standard InfluxDB format.

## Immediate (Step 3)

1. **Run time-series profiling** — create and execute `scripts/03_profile_timeseries.py`
   - Confirm semicolon delimiter for all 233 files
   - Detect encoding (UTF-8 / Latin-1)
   - Extract column names from each file
   - Sample 20 rows per file → save to `reports/sample_rows/`
   - Detect row counts efficiently (line count, not full load)
   - Save `reports/file_format_report.csv` and `reports/schema_summary.csv`
   - Update `context/schema_context.md`

2. **Inspect ambiguous files** — peek at `A.csv`, `pilot.csv`, `_value.csv`, `val1006-1009.csv`

## ~~Step 3 — COMPLETE~~

Time-series profiling done. BMS data: Dec 2022 → May 2026 (live). Dominant interval: ~20s. 15 commissioning-snapshot files identified (exclude from modeling).

## After Time-Series Profiling (Step 4)

4. **Signal classification** — `scripts/05_classify_signals.py`
   - Map signal names to physical categories using German keyword dictionary
   - Cross-reference thesis PDF for confirmation
   - Build `context/signal_dictionary.md` and `reports/signal_classification.csv`

## After Signal Classification (Step 5)

5. **ZORO MVP use-case mapping** — evaluate readiness for each MVP path
6. **Generate final EDA summary** — `reports/EDA_SUMMARY.md`

## ~~Step 4 — COMPLETE~~

Signal classification done. 223/233 signals pipeline-mapped to JSON v1. EDA phase complete.

## EDA COMPLETE — Post-EDA Next Steps

### Immediate
1. Parse thesis PDF appendix — resolve val1006-1009, confirm irradiance signal
2. Write `scripts/06_generate_samples.py` — 30-day samples for top 20 signals into `data/samples/`
3. Build HP COP calculator (`scripts/07_hp_cop_analysis.py`)

### Pipeline work (ZoroEnergyPlatform repo)
4. Replay EnFa data through ZORO pipeline — CSV → JSON v1 → Kafka → TimescaleDB
5. Parser plugin registry refactor in `format_adapter.py`
6. Signal registry table in TimescaleDB
7. Customer container isolation (per-customer VM or GKE pods)
8. Add electricity spot price feed (Tibber API or ENTSO-E)
